"""Read-only command status API."""

from fastapi import APIRouter, Depends, Request

from biovolt_backend.commands.schemas import CommandCreate
from biovolt_backend.commands.service import CommandService
from biovolt_backend.security.dependencies import require_operator_session

router = APIRouter(prefix="/api/commands")


def service(request: Request) -> CommandService:
    return request.app.state.command_service


@router.get("/{command_id}")
async def get(request: Request, command_id: str):
    return await service(request).get(command_id)


@router.post("", dependencies=[Depends(require_operator_session)])
async def create(request: Request, body: CommandCreate):
    command = await service(request).create(body)
    await request.app.state.command_dispatcher.dispatch(str(command.command_id))
    return command
