"""Read-only command status API."""

from fastapi import APIRouter, Request

from biovolt_backend.commands.service import CommandService

router = APIRouter(prefix="/api/commands")


def service(request: Request) -> CommandService:
    return request.app.state.command_service


@router.get("/{command_id}")
async def get(request: Request, command_id: str):
    return await service(request).get(command_id)
