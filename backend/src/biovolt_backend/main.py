from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from biovolt_backend.api.health import router as health_router
from biovolt_backend.config import Settings
from biovolt_backend.domain.energy import EnergyAccumulator
from biovolt_backend.domain.processing import ProcessingConfig
from biovolt_backend.persistence.database import create_engine_and_session, init_database
from biovolt_backend.persistence.telemetry_repository import TelemetryRepository
from biovolt_backend.persistence.throttle import PersistenceThrottle
from biovolt_backend.services.telemetry_service import TelemetryService
from biovolt_backend.websocket.dashboard_hub import DashboardHub
from biovolt_backend.websocket.device_registry import DeviceRegistry
from biovolt_backend.websocket.routes import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize runtime dependencies for the application lifetime."""

    settings: Settings = app.state.settings
    engine, session_factory = create_engine_and_session(settings.database_url)
    try:
        await init_database(engine)

        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.telemetry_repository = TelemetryRepository(session_factory)
        app.state.device_registry = DeviceRegistry()
        app.state.dashboard_hub = DashboardHub()
        app.state.telemetry_service = TelemetryService(
            config=ProcessingConfig(
                load_resistance_ohm=settings.load_resistance_ohm,
                bpw34_dark_raw=settings.bpw34_dark_raw,
                bpw34_blank_raw=settings.bpw34_blank_raw,
            ),
            energy=EnergyAccumulator(),
            throttle=PersistenceThrottle(),
            repository=app.state.telemetry_repository,
            dashboard_hub=app.state.dashboard_hub,
            device_registry=app.state.device_registry,
        )
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    app = FastAPI(title=resolved.app_name, lifespan=lifespan)
    app.state.settings = resolved
    app.include_router(health_router)
    app.include_router(websocket_router)
    return app


app = create_app()
