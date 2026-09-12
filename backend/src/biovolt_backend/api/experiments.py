# ruff: noqa: E501
from fastapi import APIRouter, Depends, Request

from biovolt_backend.experiments.schemas import ExperimentCreate, ExperimentDraftUpdate
from biovolt_backend.experiments.service import ExperimentService
from biovolt_backend.security.dependencies import require_operator_session

router = APIRouter(prefix="/api/experiments")


def service(request: Request) -> ExperimentService:
    return request.app.state.experiment_service


def orchestrator(request: Request):
    return request.app.state.experiment_orchestrator


@router.post("", dependencies=[Depends(require_operator_session)])
async def create(request: Request, body: ExperimentCreate):
    return await service(request).create(body)


@router.get("")
async def list_all(request: Request):
    return await service(request).list()


@router.get("/{experiment_id}")
async def get(request: Request, experiment_id: str):
    return await service(request).get(experiment_id)


@router.patch("/{experiment_id}", dependencies=[Depends(require_operator_session)])
async def update(request: Request, experiment_id: str, body: ExperimentDraftUpdate):
    return await service(request).update_draft(experiment_id, body)


@router.post("/{experiment_id}/ready", dependencies=[Depends(require_operator_session)])
async def ready(request: Request, experiment_id: str):
    return await service(request).mark_ready(experiment_id)


@router.post("/{experiment_id}/start", dependencies=[Depends(require_operator_session)])
async def start(request: Request, experiment_id: str):
    return await orchestrator(request).start(experiment_id)


@router.post("/{experiment_id}/stop", dependencies=[Depends(require_operator_session)])
async def stop(request: Request, experiment_id: str):
    return await orchestrator(request).stop(experiment_id)


@router.post("/{experiment_id}/abort", dependencies=[Depends(require_operator_session)])
async def abort(request: Request, experiment_id: str):
    return await service(request).abort(experiment_id)


@router.post(
    "/{experiment_id}/arms/{arm_id}/baseline/capture",
    dependencies=[Depends(require_operator_session)],
)
async def capture_baseline(request: Request, experiment_id: str, arm_id: str):
    return await request.app.state.baseline_service.capture(experiment_id, arm_id)
