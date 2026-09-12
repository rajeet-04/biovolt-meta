from fastapi import APIRouter, Request

from biovolt_backend.services.access_mode import capabilities

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/capabilities")
async def get_capabilities(request: Request):
    return capabilities(request)
