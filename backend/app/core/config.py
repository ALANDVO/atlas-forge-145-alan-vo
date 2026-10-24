from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "atlas-forge-145-alan-vo"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    
    # Keycloak / OIDC
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "atlas-forge"
    keycloak_client_id: str = "atlas-forge-client"
    keycloak_client_secret: str = ""
    oidc_issuer: Optional[str] = None
    oidc_audience: Optional[str] = None
    
    # LLM
    llm_provider: str = "openai-compatible"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]
    
    # Media server
    media_range_piece_bytes: int = 4 * 1024 * 1024  # 4 MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
