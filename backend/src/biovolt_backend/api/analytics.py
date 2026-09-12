import csv
import io

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/experiments")


@router.get("/{experiment_id}/analytics/summary")
async def analytics_summary(request: Request, experiment_id: str):
    return await request.app.state.analytics_service.summary(experiment_id)


@router.get("/{experiment_id}/analytics/comparison")
async def analytics_comparison(
    request: Request, experiment_id: str, passive_arm_id: str, adaptive_arm_id: str
):
    return await request.app.state.analytics_service.comparison(
        experiment_id, passive_arm_id, adaptive_arm_id
    )


@router.get("/{experiment_id}/analytics/series")
async def analytics_series(request: Request, experiment_id: str, bucket_seconds: int = 10):
    return await request.app.state.analytics_service.series(experiment_id, bucket_seconds)


@router.get("/{experiment_id}/analytics/export.csv")
async def analytics_export(request: Request, experiment_id: str):
    rows = await request.app.state.analytics_service.export_rows(experiment_id)
    output = io.StringIO()
    fields = (
        list(rows[0])
        if rows
        else [
            "experiment_id",
            "arm_id",
            "arm_mode",
            "device_id",
            "cell_id",
            "received_at",
            "elapsed_s",
            "sequence",
            "uptime_ms",
            "power_uw",
            "cumulative_energy_mj",
            "od680",
            "grow_led_pwm",
            "mixer_on",
        ]
    )
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="biovolt-{experiment_id}-analytics.csv"'
        },
    )
