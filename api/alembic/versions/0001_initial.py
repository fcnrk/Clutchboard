"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tables ---
    op.create_table(
        "players",
        sa.Column("steam_id", sa.BigInteger(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("real_name", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("steam_id"),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("map_name", sa.Text(), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("t_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ct_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="live"),
        sa.Column("demo_path", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "match_players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("steam_id", sa.BigInteger(), nullable=False),
        sa.Column("team", sa.Text(), nullable=False),
        sa.Column("kills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deaths", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("assists", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("damage_dealt", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("headshot_kills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rounds_played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_kills", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_deaths", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("utility_damage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enemies_flashed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("team_flashes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clutch_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clutch_wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mvp_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["steam_id"], ["players.steam_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "steam_id"),
    )
    op.create_table(
        "rounds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("winner", sa.Text(), nullable=False),
        sa.Column("win_reason", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "round_number"),
    )
    op.create_table(
        "kills",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("killer_steam_id", sa.BigInteger(), nullable=True),
        sa.Column("victim_steam_id", sa.BigInteger(), nullable=False),
        sa.Column("assister_steam_id", sa.BigInteger(), nullable=True),
        sa.Column("weapon", sa.Text(), nullable=False),
        sa.Column("headshot", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("penetrated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("noscope", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("thrusmoke", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("attacker_blind", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assister_steam_id"], ["players.steam_id"]),
        sa.ForeignKeyConstraint(["killer_steam_id"], ["players.steam_id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["victim_steam_id"], ["players.steam_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "damage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("attacker_steam_id", sa.BigInteger(), nullable=True),
        sa.Column("victim_steam_id", sa.BigInteger(), nullable=False),
        sa.Column("weapon", sa.Text(), nullable=False),
        sa.Column("damage", sa.Integer(), nullable=False),
        sa.Column("damage_armor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hitgroup", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["attacker_steam_id"], ["players.steam_id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["victim_steam_id"], ["players.steam_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "utility_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("steam_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("damage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["steam_id"], ["players.steam_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "flash_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("thrower_steam_id", sa.BigInteger(), nullable=True),
        sa.Column("blinded_steam_id", sa.BigInteger(), nullable=True),
        sa.Column("blind_duration", sa.Float(), nullable=False),
        sa.Column("is_teammate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["blinded_steam_id"], ["players.steam_id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thrower_steam_id"], ["players.steam_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "weapon_fires",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.UUID(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("steam_id", sa.BigInteger(), nullable=True),
        sa.Column("weapon", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["steam_id"], ["players.steam_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- indexes ---
    op.execute("CREATE INDEX ix_kills_match_id ON kills (match_id)")
    op.execute("CREATE INDEX ix_kills_match_round ON kills (match_id, round_id)")
    op.execute("CREATE INDEX ix_kills_killer ON kills (killer_steam_id)")
    op.execute("CREATE INDEX ix_kills_victim ON kills (victim_steam_id)")
    op.execute("CREATE INDEX ix_damage_match_id ON damage (match_id)")
    op.execute("CREATE INDEX ix_damage_match_round ON damage (match_id, round_id)")
    op.execute("CREATE INDEX ix_weapon_fires_match_id ON weapon_fires (match_id)")
    op.execute("CREATE INDEX ix_weapon_fires_match_steam_weapon ON weapon_fires (match_id, steam_id, weapon)")
    op.execute("CREATE INDEX ix_flash_events_match_id ON flash_events (match_id)")
    op.execute("CREATE INDEX ix_flash_events_match_steam ON flash_events (match_id, thrower_steam_id)")
    op.execute("CREATE INDEX ix_utility_events_match_id ON utility_events (match_id)")
    op.execute("CREATE INDEX ix_utility_events_match_steam ON utility_events (match_id, steam_id)")
    op.execute("CREATE INDEX ix_rounds_match_id ON rounds (match_id)")

    # --- materialized view ---
    op.execute("""
        CREATE MATERIALIZED VIEW player_stats AS
        SELECT
            p.steam_id,
            p.display_name,
            p.real_name,
            p.avatar_url,
            COUNT(DISTINCT mp.match_id)                                                    AS total_matches,
            COALESCE(SUM(mp.kills), 0)                                                     AS total_kills,
            COALESCE(SUM(mp.deaths), 0)                                                    AS total_deaths,
            COALESCE(SUM(mp.assists), 0)                                                   AS total_assists,
            COALESCE(SUM(mp.damage_dealt), 0)                                              AS total_damage,
            COALESCE(SUM(mp.rounds_played), 0)                                             AS total_rounds,
            COALESCE(SUM(CASE
                WHEN m.status = 'completed'
                 AND ((mp.team = 'T' AND m.t_score > m.ct_score)
                  OR  (mp.team = 'CT' AND m.ct_score > m.t_score))
                THEN 1 ELSE 0 END), 0)                                                     AS total_wins,
            CASE WHEN COALESCE(SUM(mp.deaths), 0) = 0
                 THEN COALESCE(SUM(mp.kills), 0)::float
                 ELSE ROUND(COALESCE(SUM(mp.kills), 0)::numeric / NULLIF(SUM(mp.deaths), 0), 2)::float
            END                                                                            AS kd_ratio,
            CASE WHEN COALESCE(SUM(mp.rounds_played), 0) = 0 THEN 0.0
                 ELSE ROUND(COALESCE(SUM(mp.damage_dealt), 0)::numeric / NULLIF(SUM(mp.rounds_played), 0), 1)::float
            END                                                                            AS adr,
            CASE WHEN COALESCE(SUM(mp.kills), 0) = 0 THEN 0.0
                 ELSE ROUND(COALESCE(SUM(mp.headshot_kills), 0)::numeric / NULLIF(SUM(mp.kills), 0) * 100, 1)::float
            END                                                                            AS hs_pct,
            CASE WHEN COUNT(DISTINCT mp.match_id) = 0 THEN 0.0
                 ELSE ROUND(
                     COALESCE(SUM(CASE
                         WHEN m.status = 'completed'
                          AND ((mp.team = 'T' AND m.t_score > m.ct_score)
                           OR  (mp.team = 'CT' AND m.ct_score > m.t_score))
                         THEN 1 ELSE 0 END), 0)::numeric
                     / NULLIF(COUNT(DISTINCT mp.match_id), 0) * 100, 1
                 )::float
            END                                                                            AS win_rate,
            COALESCE(SUM(mp.first_kills), 0)                                               AS first_kills_total,
            COALESCE(SUM(mp.utility_damage), 0)                                            AS utility_damage_total
        FROM players p
        LEFT JOIN match_players mp ON mp.steam_id = p.steam_id
        LEFT JOIN matches m ON m.id = mp.match_id
        GROUP BY p.steam_id, p.display_name, p.real_name, p.avatar_url
        WITH DATA
    """)

    # Required for REFRESH MATERIALIZED VIEW CONCURRENTLY
    op.execute("CREATE UNIQUE INDEX ix_player_stats_steam_id ON player_stats (steam_id)")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS player_stats")
    op.drop_table("weapon_fires")
    op.drop_table("flash_events")
    op.drop_table("utility_events")
    op.drop_table("damage")
    op.drop_table("kills")
    op.drop_table("rounds")
    op.drop_table("match_players")
    op.drop_table("matches")
    op.drop_table("players")
