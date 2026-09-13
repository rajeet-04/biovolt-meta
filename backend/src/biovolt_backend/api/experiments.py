from fastapi import APIRouter, Request

from biovolt_backend.experiments.schemas import ExperimentCreate, ExperimentDraftUpdate
from biovolt_backend.experiments.service import ExperimentService

router = APIRouter(prefix="/api/experiments")


def service(request: Request) -> ExperimentService:
    return request.app.state.experiment_service


@router.post("")
async def create(request: Request, body: ExperimentCreate):
    return await service(request).create(body)


@router.get("")
async def list_all(request: Request):
    return await service(request).list()


@router.get("/{experiment_id}")
async def get(request: Request, experiment_id: str):
    return await service(request).get(experiment_id)


@router.patch("/{experiment_id}")
async def update(request: Request, experiment_id: str, body: ExperimentDraftUpdate):
    return await service(request).update_draft(experiment_id, body)


@router.post("/{experiment_id}/ready")
async def ready(request: Request, experiment_id: str):
    return await service(request).mark_ready(experiment_id)


@router.post("/{experiment_id}/start")
async def start(request: Request, experiment_id: str):
    return await service(request).begin_start(experiment_id)


@router.post("/{experiment_id}/stop")
async def stop(request: Request, experiment_id: str):
    return await service(request).begin_stop(experiment_id)


@router.post("/{experiment_id}/abort")
async def abort(request: Request, experiment_id: str):
    return await service(request).abort(experiment_id)
