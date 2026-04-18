import asyncio
import os
import uuid
import pytest
import asyncpg
from httpx import AsyncClient, ASGITransport

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clutchboard_test",
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def apply_migrations():
    """Run Alembic migrations against the test DB before the session."""
    import subprocess
    env = {**os.environ, "DATABASE_URL": TEST_DATABASE_URL}
    subprocess.run(
        ["alembic", "upgrade", "head"],
        env=env,
        check=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    yield
    # Teardown: wipe schema so next run starts clean
    dsn = TEST_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(dsn)
    await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    await conn.close()


@pytest.fixture
async def client():
    from app.config import settings
    import app.database as database
    settings.database_url = TEST_DATABASE_URL
    await database.create_pool()
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    await database.close_pool()


@pytest.fixture
async def seeded_match(client: AsyncClient):
    """Insert two players, a match, and one round into the test DB."""
    match_id = str(uuid.uuid4())
    await client.post("/events", json=[
        {"type": "player_connect", "steam_id": 76561198000000001, "display_name": "Alice"},
        {"type": "player_connect", "steam_id": 76561198000000002, "display_name": "Bob"},
        {
            "type": "match_start",
            "match_id": match_id,
            "map_name": "de_inferno",
            "started_at": "2026-04-16T13:00:00Z",
        },
        {
            "type": "round_end",
            "match_id": match_id,
            "round_number": 1,
            "winner": "T",
            "win_reason": "elimination",
        },
    ])
    return {"match_id": match_id, "p1": 76561198000000001, "p2": 76561198000000002}
