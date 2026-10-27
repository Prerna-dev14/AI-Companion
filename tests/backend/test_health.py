import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint_contract(async_client: AsyncClient):
    """Verify GET /api/health fulfills the master specification API contract."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["database"]["connected"] is True
    assert "services" in data
    assert data["services"]["conversation"] == "ready"
    assert data["services"]["emotion_engine"] == "ready"

@pytest.mark.asyncio
async def test_api_v1_health_endpoint(async_client: AsyncClient):
    """Verify GET /api/v1/health is also reachable via API v1 router."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
