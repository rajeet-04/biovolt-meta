from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


def test_login_sets_strict_httponly_cookie_and_session_endpoint(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'operator.db'}",
            operator_pin_hash=PasswordHasher().hash("2468"),
        )
    )
    with TestClient(app) as client:
        response = client.post("/api/operator/login", json={"pin": "2468"})
        assert response.status_code == 200
        cookie = response.cookies.get("biovolt_operator_session")
        assert cookie
        assert "HttpOnly" in response.headers.get("set-cookie", "")
        assert "SameSite=strict" in response.headers.get("set-cookie", "")
        assert "2468" not in response.text
        session = client.get("/api/operator/session").json()
        assert session["authenticated"] is True
        assert session["expires_at"]


def test_wrong_pin_is_generic_unauthorized_and_write_requires_session(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'operator.db'}",
            operator_pin_hash=PasswordHasher().hash("2468"),
        )
    )
    with TestClient(app) as client:
        wrong = client.post("/api/operator/login", json={"pin": "0000"})
        assert wrong.status_code == 401
        assert "2468" not in wrong.text
        assert client.post("/api/experiments", json={"name": "blocked"}).status_code == 401


def test_logout_revokes_session(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'operator.db'}",
            operator_pin_hash=PasswordHasher().hash("2468"),
        )
    )
    with TestClient(app) as client:
        client.post("/api/operator/login", json={"pin": "2468"})
        assert client.get("/api/operator/session").json()["authenticated"] is True
        assert client.post("/api/operator/logout").status_code == 200
        assert client.get("/api/operator/session").json()["authenticated"] is False
