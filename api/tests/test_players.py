import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_leaderboard_returns_list(client: AsyncClient):
    response = await client.get("/api/players")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_player_not_found(client: AsyncClient):
    response = await client.get("/api/players/9999999999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_player_matches_returns_list(client: AsyncClient, seeded_match):
    steam_id = seeded_match["p1"]
    response = await client.get(f"/api/players/{steam_id}/matches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_player_weapons_returns_list(client: AsyncClient, seeded_match):
    steam_id = seeded_match["p1"]
    response = await client.get(f"/api/players/{steam_id}/weapons")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_player_trends(client: AsyncClient, seeded_match):
    # Insert a kill then end the match so match_players is populated
    await client.post("/events", json=[{
        "type": "kill",
        "match_id": seeded_match["match_id"],
        "round_number": 1,
        "killer_steam_id": seeded_match["p1"],
        "victim_steam_id": seeded_match["p2"],
        "weapon": "ak47",
        "headshot": True,
    }])
    await client.post("/events", json=[{
        "type": "match_end",
        "match_id": seeded_match["match_id"],
        "t_score": 1,
        "ct_score": 0,
        "player_teams": {
            str(seeded_match["p1"]): "T",
            str(seeded_match["p2"]): "CT",
        },
    }])

    response = await client.get(f"/api/players/{seeded_match['p1']}/trends")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    point = data[0]
    assert point["kills"] == 1
    assert point["deaths"] == 0
    assert point["kd_ratio"] == 1.0
    assert "match_id" in point
    assert "map_name" in point
    assert "started_at" in point
