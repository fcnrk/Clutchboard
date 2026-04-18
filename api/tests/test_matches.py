import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_matches_returns_list(client: AsyncClient):
    response = await client.get("/api/matches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_match_detail(client: AsyncClient, seeded_match):
    match_id = seeded_match["match_id"]
    response = await client.get(f"/api/matches/{match_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["map_name"] == "de_inferno"
    assert "scoreboard" in data
    assert "rounds" in data
    assert len(data["rounds"]) >= 1


@pytest.mark.asyncio
async def test_get_match_not_found(client: AsyncClient):
    response = await client.get("/api/matches/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 404
