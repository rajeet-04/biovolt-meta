from fastapi import APIRouter, Depends, HTTPException, Request

from biovolt_backend.calibration.schemas import CalibrationRevisionCreate
from biovolt_backend.calibration.service import CalibrationService
from biovolt_backend.security.dependencies import require_operator_session

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


def service(request: Request) -> CalibrationService:
    return request.app.state.calibration_service


@router.get("/profiles")
async def profiles(request: Request):
    return await service(request).list_profiles()


@router.post("/profiles", dependencies=[Depends(require_operator_session)])
async def create_profile(request: Request, body: CalibrationRevisionCreate):
    return await service(request).create_profile(body)


@router.post("/profiles/{profile_id}/revisions", dependencies=[Depends(require_operator_session)])
async def revise(profile_id: str, request: Request, body: CalibrationRevisionCreate):
    try:
        return await service(request).revise(profile_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="profile not found") from exc


@router.post("/revisions/{revision_id}/activate", dependencies=[Depends(require_operator_session)])
async def activate(revision_id: str, request: Request):
    try:
        return await service(request).activate(revision_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="revision not found") from exc
