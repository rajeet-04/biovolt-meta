from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from biovolt_backend.analytics.repository import AnalyticsRepository
from biovolt_backend.analytics.service import AnalyticsService
from biovolt_backend.api.analytics import router as analytics_router
from biovolt_backend.api.calibration import router as calibration_router
from biovolt_backend.api.commands import router as commands_router
from biovolt_backend.api.experiments import router as experiments_router
from biovolt_backend.api.health import router as health_router
from biovolt_backend.api.operator import router as operator_router
from biovolt_backend.api.status import router as status_router
from biovolt_backend.api.telemetry import router as telemetry_router
from biovolt_backend.calibration.service import CalibrationService
from biovolt_backend.commands.dispatcher import CommandDispatcher
from biovolt_backend.commands.repository import CommandRepository
from biovolt_backend.commands.service import CommandService
from biovolt_backend.config import Settings
from biovolt_backend.domain.continuity import TelemetryContinuityTracker
from biovolt_backend.domain.energy import EnergyAccumulator
from biovolt_backend.domain.processing import ProcessingConfig
from biovolt_backend.experiments.baseline import BaselineService
from biovolt_backend.experiments.orchestrator import ExperimentOrchestrator
from biovolt_backend.experiments.repository import ExperimentRepository
from biovolt_backend.experiments.service import ExperimentService
from biovolt_backend.persistence.database import create_engine_and_session, init_database
from biovolt_backend.persistence.telemetry_repository import TelemetryRepository
from biovolt_backend.persistence.throttle import PersistenceThrottle
from biovolt_backend.security.operator import OperatorAuthenticator
from biovolt_backend.security.sessions import OperatorSessionStore
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
        app.state.calibration_service = CalibrationService(session_factory)
        app.state.baseline_service = BaselineService(session_factory)
        experiment_repository = ExperimentRepository(session_factory)
        app.state.experiment_service = ExperimentService(
            experiment_repository, settings.evidence_class
        )
        app.state.analytics_service = AnalyticsService(
            experiment_repository,
            AnalyticsRepository(session_factory),
        )
        app.state.device_registry = DeviceRegistry()
        app.state.command_service = CommandService(CommandRepository(session_factory))
        app.state.command_dispatcher = CommandDispatcher(
            CommandRepository(session_factory),
            app.state.command_service,
            app.state.device_registry,
        )
        app.state.experiment_orchestrator = ExperimentOrchestrator(
            app.state.experiment_service,
            app.state.command_service,
            app.state.command_dispatcher,
        )
        app.state.command_service.set_ack_handler(app.state.experiment_orchestrator.on_ack)
        app.state.dashboard_hub = DashboardHub()
        app.state.telemetry_service = TelemetryService(
            config=ProcessingConfig(
                load_resistance_ohm=settings.load_resistance_ohm,
                bpw34_dark_raw=settings.bpw34_dark_raw,
                bpw34_blank_raw=settings.bpw34_blank_raw,
            ),
            energy=EnergyAccumulator(),
            continuity=TelemetryContinuityTracker(),
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
    app.state.operator_authenticator = OperatorAuthenticator(resolved.operator_pin_hash)
    app.state.operator_sessions = OperatorSessionStore()
    app.include_router(health_router)
    app.include_router(operator_router)
    app.include_router(calibration_router)
    app.include_router(analytics_router)
    app.include_router(experiments_router)
    app.include_router(commands_router)
    app.include_router(status_router)
    app.include_router(telemetry_router)
    app.include_router(websocket_router)
    return app


app = create_app()
