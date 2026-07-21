from fastapi.testclient import TestClient

from app.access_gate import ACCESS_COOKIE_NAME
from app.main import app


def test_access_gate_protects_api_and_accepts_configured_password():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/access/status").json() == {"authenticated": False}
        assert (
            client.post(
                "/api/auth/login", data={"username": "pm", "password": "pm123"}
            ).status_code
            == 401
        )

        wrong = client.post("/api/access/verify", json={"password": "wrong"})
        assert wrong.status_code == 401

        verified = client.post(
            "/api/access/verify", json={"password": "local666"}
        )
        assert verified.status_code == 200
        assert ACCESS_COOKIE_NAME in client.cookies
        assert client.get("/api/access/status").json() == {"authenticated": True}
        assert (
            client.post(
                "/api/auth/login", data={"username": "pm", "password": "pm123"}
            ).status_code
            == 200
        )
