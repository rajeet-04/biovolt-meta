"""Operator PIN login/logout and session introspection endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from biovolt_backend.security.dependencies import COOKIE_NAME

router = APIRouter(prefix="/api/operator")


class OperatorLogin(BaseModel):
    pin: str = Field(min_length=1, max_length=128)


@router.post("/login")
async def login(request: Request, response: Response, body: OperatorLogin):
    if not request.app.state.operator_authenticator.verify_pin(body.pin):
        raise HTTPException(status_code=401, detail="invalid operator credentials")
    token, expires_at = request.app.state.operator_sessions.create(datetime.now(UTC))
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=1800,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
    )
    return {"authenticated": True, "expires_at": expires_at.isoformat()}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        request.app.state.operator_sessions.revoke(token)
    response.delete_cookie(COOKIE_NAME, samesite="strict", secure=request.url.scheme == "https")
    return {"authenticated": False, "expires_at": None}


@router.get("/session")
async def session(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    store = request.app.state.operator_sessions
    if token and store.valid(token, datetime.now(UTC)):
        # The store intentionally exposes validity only; token material never
        # enters the response or frontend state.
        expires_at = store.expires_at(token)
        return {"authenticated": True, "expires_at": expires_at.isoformat() if expires_at else None}
    return {"authenticated": False, "expires_at": None}
