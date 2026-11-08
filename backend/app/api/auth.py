from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
import httpx
import secrets
import hashlib
import base64
import time
from typing import Optional
from urllib.parse import urlencode

from app.core.config import settings

router = APIRouter(tags=["auth"])


class LoginResponse(BaseModel):
    auth_url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    sub: str
    email: str
    name: str
    roles: list[str] = []


class OIDCConfig(BaseModel):
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    userinfo_endpoint: str
    end_session_endpoint: str


# In-memory storage for PKCE and state (use Redis in production)
_pkce_store: dict[str, dict] = {}
_session_store: dict[str, dict] = {}

# Cache for OIDC config and JWKS
_oidc_config: Optional[OIDCConfig] = None
_jwks_cache: Optional[dict] = None
_jwks_cache_time: float = 0


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_verifier, code_challenge


def generate_state() -> str:
    """Generate cryptographically secure state parameter."""
    return secrets.token_urlsafe(32)


async def get_oidc_config() -> OIDCConfig:
    """Fetch OIDC configuration from Keycloak."""
    global _oidc_config
    if _oidc_config is not None:
        return _oidc_config
    
    issuer = settings.oidc_issuer or f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
    config_url = f"{issuer}/.well-known/openid-configuration"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(config_url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    
    _oidc_config = OIDCConfig(
        issuer=data["issuer"],
        authorization_endpoint=data["authorization_endpoint"],
        token_endpoint=data["token_endpoint"],
        jwks_uri=data["jwks_uri"],
        userinfo_endpoint=data["userinfo_endpoint"],
        end_session_endpoint=data.get("end_session_endpoint", ""),
    )
    return _oidc_config


async def get_jwks() -> dict:
    """Fetch and cache JWKS from Keycloak."""
    global _jwks_cache, _jwks_cache_time
    
    # Cache for 1 hour
    if _jwks_cache is not None and time.time() - _jwks_cache_time < 3600:
        return _jwks_cache
    
    oidc_config = await get_oidc_config()
    async with httpx.AsyncClient() as client:
        resp = await client.get(oidc_config.jwks_uri, timeout=10.0)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = time.time()
    
    return _jwks_cache


async def validate_token(token: str) -> dict:
    """Validate JWT access token using Keycloak JWKS."""
    jwks = await get_jwks()
    
    # Get the key ID from token header
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Token missing key ID")
    
    # Find matching key
    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key = k
            break
    
    if not key:
        raise HTTPException(status_code=401, detail="Unable to find matching key")
    
    # Validate token
    issuer = settings.oidc_issuer or f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
    audience = settings.oidc_audience or settings.keycloak_client_id
    
    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def get_current_user(request: Request) -> UserInfo:
    """Dependency to get current authenticated user from session cookie."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = _session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    
    # Check if access token is expired, try to refresh
    if time.time() >= session.get("expires_at", 0):
        # Try refresh token
        if session.get("refresh_token"):
            try:
                new_tokens = await refresh_access_token(session["refresh_token"])
                session.update(new_tokens)
                session["expires_at"] = time.time() + new_tokens["expires_in"]
            except Exception:
                # Refresh failed, clear session
                _session_store.pop(session_id, None)
                raise HTTPException(status_code=401, detail="Session expired")
        else:
            _session_store.pop(session_id, None)
            raise HTTPException(status_code=401, detail="Session expired")
    
    # Validate access token and get user info
    payload = await validate_token(session["access_token"])
    
    return UserInfo(
        sub=payload.get("sub", ""),
        email=payload.get("email", ""),
        name=payload.get("name", payload.get("preferred_username", "")),
        roles=payload.get("realm_access", {}).get("roles", []),
    )


async def refresh_access_token(refresh_token: str) -> dict:
    """Refresh access token using refresh token."""
    oidc_config = await get_oidc_config()
    
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
        "refresh_token": refresh_token,
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            oidc_config.token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


def create_session(response: Response, tokens: dict) -> str:
    """Create session and set secure cookie."""
    session_id = secrets.token_urlsafe(32)
    expires_in = tokens.get("expires_in", 300)
    
    _session_store[session_id] = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "expires_at": time.time() + expires_in,
        "created_at": time.time(),
    }
    
    # Set secure HTTP-only cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=expires_in * 2,  # Cookie lives longer than token for refresh
        path="/",
    )
    
    return session_id


def clear_session(response: Response, request: Request) -> None:
    """Clear session and cookie."""
    session_id = request.cookies.get("session_id")
    if session_id:
        _session_store.pop(session_id, None)
    response.delete_cookie(key="session_id", path="/", httponly=True, secure=False, samesite="lax")


@router.get("/login", response_model=LoginResponse)
async def login(response: Response):
    """Initiate OIDC login flow with PKCE."""
    oidc_config = await get_oidc_config()
    
    # Generate PKCE and state
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()
    
    # Store PKCE data with state
    _pkce_store[state] = {
        "code_verifier": code_verifier,
        "created_at": time.time(),
    }
    
    # Clean old PKCE entries (older than 10 minutes)
    current_time = time.time()
    for k, v in list(_pkce_store.items()):
        if current_time - v["created_at"] > 600:
            _pkce_store.pop(k, None)
    
    # Build authorization URL
    params = {
        "client_id": settings.keycloak_client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": f"{settings.cors_origins[0]}/callback",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    
    auth_url = f"{oidc_config.authorization_endpoint}?{urlencode(params)}"
    
    return LoginResponse(auth_url=auth_url, state=state)


@router.post("/callback", response_model=TokenResponse)
async def callback(code: str, state: str, response: Response):
    """Handle OIDC callback and exchange code for tokens."""
    # Verify state and get PKCE
    pkce_data = _pkce_store.pop(state, None)
    if not pkce_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    code_verifier = pkce_data["code_verifier"]
    
    oidc_config = await get_oidc_config()
    
    # Exchange code for tokens
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.keycloak_client_id,
        "client_secret": settings.keycloak_client_secret,
        "code": code,
        "redirect_uri": f"{settings.cors_origins[0]}/callback",
        "code_verifier": code_verifier,
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            oidc_config.token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")
        
        tokens = resp.json()
    
    # Create session
    create_session(response, tokens)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens.get("token_type", "bearer"),
        expires_in=tokens.get("expires_in", 300),
    )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session."""
    session_id = request.cookies.get("session_id")
    session = _session_store.get(session_id) if session_id else None
    
    # Clear local session
    clear_session(response, request)
    
    # Optionally redirect to Keycloak logout
    if session:
        oidc_config = await get_oidc_config()
        if oidc_config.end_session_endpoint:
            # In a real app, you might redirect here
            pass
    
    return {"message": "Logged out"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_endpoint(user: UserInfo = Depends(get_current_user)):
    """Get current user info (requires authentication)."""
    return user


# Dependency for role-based access control
def require_roles(*required_roles: str):
    """Dependency factory for role-based access control."""
    async def role_checker(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        user_roles = set(user.roles)
        if not user_roles.intersection(required_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker


# Export for use in other routers
__all__ = ["router", "get_current_user", "require_roles", "validate_token"]
