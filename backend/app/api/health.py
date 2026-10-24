from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        service="atlas-forge-145-alan-vo",
        version="1.0.0"
    )
