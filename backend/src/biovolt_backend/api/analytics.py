from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/experiments")


@router.get("/{experiment_id}/analytics/summary")
async def analytics_summary(request: Request, experiment_id: str):
    return await request.app.state.analytics_service.summary(experiment_id)
