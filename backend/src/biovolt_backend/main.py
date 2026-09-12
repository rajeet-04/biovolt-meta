from fastapi import FastAPI

from biovolt_backend.api.health import router as health_router
from biovolt_backend.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    app = FastAPI(title=resolved.app_name)
    app.state.settings = resolved
    app.include_router(health_router)
    return app


app = create_app()
