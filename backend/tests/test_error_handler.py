import pytest

from app.shared.exceptions import AppException


@pytest.mark.asyncio
async def test_app_exception_returns_json(client):
    from app.main import app

    @app.get("/api/v1/test-error")
    async def trigger_error():
        raise AppException(message="Test error", status_code=422, field="name")

    response = await client.get("/api/v1/test-error")
    assert response.status_code == 422
    data = response.json()
    assert data["error"] is True
    assert data["message"] == "Test error"
    assert data["field"] == "name"
