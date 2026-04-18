def test_base_importable():
    from app.models.base import Base
    assert Base.metadata is not None


def test_player_columns():
    from app.models.player import Player
    cols = {c.key for c in Player.__table__.columns}
    assert cols == {"steam_id", "display_name", "real_name", "avatar_url", "created_at", "updated_at"}


def test_match_columns():
    from app.models.match import Match
    cols = {c.key for c in Match.__table__.columns}
    assert "id" in cols
    assert "map_name" in cols
    assert "demo_path" in cols
    assert "status" in cols


def test_match_player_unique_constraint():
    from app.models.match_player import MatchPlayer
    from sqlalchemy import UniqueConstraint
    uc_cols = []
    for c in MatchPlayer.__table__.constraints:
        if isinstance(c, UniqueConstraint):
            uc_cols.append(sorted(col.key for col in c.columns))
    assert ["match_id", "steam_id"] in uc_cols


def test_round_unique_constraint():
    from app.models.round import Round
    from sqlalchemy import UniqueConstraint
    uc_cols = []
    for c in Round.__table__.constraints:
        if isinstance(c, UniqueConstraint):
            uc_cols.append(sorted(col.key for col in c.columns))
    assert ["match_id", "round_number"] in uc_cols


def test_kill_nullable_killer():
    from app.models.kill import Kill
    col = Kill.__table__.columns["killer_steam_id"]
    assert col.nullable is True


def test_damage_columns():
    from app.models.damage import Damage
    cols = {c.key for c in Damage.__table__.columns}
    assert "hitgroup" in cols
    assert "damage_armor" in cols


def test_all_models_registered_in_metadata():
    import app.models  # noqa: F401 — triggers __init__.py imports
    from app.models.base import Base
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "players", "matches", "match_players", "rounds",
        "kills", "damage", "utility_events", "flash_events", "weapon_fires",
    }
    assert expected == table_names
