import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_player_connect(client: AsyncClient):
    response = await client.post("/events", json=[{
        "type": "player_connect",
        "steam_id": 76561198999999001,
        "display_name": "TestUser",
    }])
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_match_start(client: AsyncClient):
    response = await client.post("/events", json=[{
        "type": "match_start",
        "match_id": "20000000-0000-0000-0000-000000000001",
        "map_name": "de_dust2",
        "started_at": "2026-04-16T14:00:00Z",
    }])
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_kill_event_inserts(client: AsyncClient, seeded_match):
    response = await client.post("/events", json=[{
        "type": "kill",
        "match_id": seeded_match["match_id"],
        "round_number": 1,
        "killer_steam_id": seeded_match["p1"],
        "victim_steam_id": seeded_match["p2"],
        "weapon": "ak47",
        "headshot": True,
    }])
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_invalid_event_type_returns_422(client: AsyncClient):
    response = await client.post("/events", json=[{"type": "not_a_real_event"}])
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_match_end_triggers_refresh(client: AsyncClient, seeded_match):
    response = await client.post("/events", json=[{
        "type": "match_end",
        "match_id": seeded_match["match_id"],
        "t_score": 13,
        "ct_score": 7,
    }])
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_match_end_populates_match_players(client: AsyncClient, seeded_match):
    # Seed a kill so there is data to aggregate
    await client.post("/events", json=[{
        "type": "kill",
        "match_id": seeded_match["match_id"],
        "round_number": 1,
        "killer_steam_id": seeded_match["p1"],
        "victim_steam_id": seeded_match["p2"],
        "weapon": "ak47",
        "headshot": True,
    }])
    # End the match with team assignments
    response = await client.post("/events", json=[{
        "type": "match_end",
        "match_id": seeded_match["match_id"],
        "t_score": 1,
        "ct_score": 0,
        "player_teams": {
            str(seeded_match["p1"]): "T",
            str(seeded_match["p2"]): "CT",
        },
    }])
    assert response.status_code == 204
    # After end_match runs, player_stats materialized view should be refreshed
    # and the killer should now show kills > 0
    resp = await client.get(f"/api/players/{seeded_match['p1']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_kills"] == 1
    assert data["total_deaths"] == 0


@pytest.mark.asyncio
async def test_events_rejects_bad_secret(client: AsyncClient, monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "api_secret", "correct-secret")
    response = await client.post(
        "/events",
        json=[{"type": "player_connect", "steam_id": 76561198000000099, "display_name": "X"}],
        headers={"X-Api-Secret": "wrong-secret"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_events_accepts_correct_secret(client: AsyncClient, monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "api_secret", "correct-secret")
    response = await client.post(
        "/events",
        json=[{"type": "player_connect", "steam_id": 76561198000000099, "display_name": "X"}],
        headers={"X-Api-Secret": "correct-secret"},
    )
    assert response.status_code == 204
