"""FastAPI dependencies for authenticated operator mutations."""

from datetime import UTC, datetime

from fastapi import HTTPException, Request

from .sessions import OperatorSessionStore

COOKIE_NAME = "biovolt_operator_session"


def require_operator_session(request: Request) -> str:
    """Return the session token or reject an unauthenticated write request."""

    token = request.cookies.get(COOKIE_NAME)
    store: OperatorSessionStore = request.app.state.operator_sessions
    if token is None or not store.valid(token, datetime.now(UTC)):
        raise HTTPException(status_code=401, detail="operator authentication required")
    return token
