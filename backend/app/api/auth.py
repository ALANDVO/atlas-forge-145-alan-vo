from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

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


@router.get("/login", response_model=LoginResponse)
async def login():
    """Initiate OIDC login flow (placeholder - full implementation in oidc-auth feature)."""
    # TODO: Implement full OIDC authorization code flow with PKCE
    # This is a placeholder for the skeleton
    return LoginResponse(
        auth_url="http://localhost:8080/realms/atlas-forge/protocol/openid-connect/auth",
        state="placeholder-state"
    )


@router.post("/callback", response_model=TokenResponse)
async def callback(code: str, state: str):
    """Handle OIDC callback (placeholder)."""
    raise HTTPException(status_code=501, detail="Not implemented - requires oidc-auth feature")


@router.post("/logout")
async def logout():
    """Logout (placeholder)."""
    return {"message": "Logged out"}


@router.get("/me", response_model=UserInfo)
async def get_current_user():
    """Get current user info (placeholder - requires auth dependency)."""
    raise HTTPException(status_code=501, detail="Not implemented - requires oidc-auth feature")
