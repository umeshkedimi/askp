from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_is_ready_with_no_registered_checks(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {}}


def test_ready_fails_closed_when_a_check_raises(app: FastAPI, client: TestClient) -> None:
    async def failing_check() -> None:
        raise RuntimeError("dependency unavailable")

    app.state.readiness_checks["dependency"] = failing_check

    response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert "error" in body["checks"]["dependency"]
