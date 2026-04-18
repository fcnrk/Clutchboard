const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Types (mirror FastAPI Pydantic schemas exactly) ──────────────────────────

export interface PlayerStats {
  steam_id: number
  display_name: string
  real_name: string | null
  avatar_url: string | null
  total_matches: number
  total_kills: number
  total_deaths: number
  total_assists: number
  total_damage: number
  total_rounds: number
  total_wins: number
  kd_ratio: number
  adr: number
  hs_pct: number
  win_rate: number
  first_kills_total: number
  utility_damage_total: number
}

export interface MatchListItem {
  id: string
  map_name: string
  started_at: string
  ended_at: string | null
  t_score: number
  ct_score: number
  status: string
}

export interface MatchScoreboardEntry {
  steam_id: number
  display_name: string
  real_name: string | null
  team: string
  kills: number
  deaths: number
  assists: number
  damage_dealt: number
  headshot_kills: number
  adr: number
  mvp_count: number
}

export interface RoundSummary {
  round_number: number
  winner: string
  win_reason: string
  duration_seconds: number | null
}

export interface MatchDetail extends MatchListItem {
  duration_seconds: number | null
  scoreboard: MatchScoreboardEntry[]
  rounds: RoundSummary[]
}

export interface WeaponStats {
  weapon: string
  kills: number
  headshot_kills: number
  shots_fired: number
  hs_pct: number
  accuracy: number
}

export interface UtilityStats {
  smokes_thrown: number
  molotovs_thrown: number
  he_grenades_thrown: number
  utility_damage: number
  enemies_flashed: number
  team_flashes: number
  avg_flash_duration: number
}

export interface TrendPoint {
  match_id: string
  map_name: string
  started_at: string
  kills: number
  deaths: number
  kd_ratio: number
  adr: number
  hs_pct: number
}

export interface HeadToHeadResponse {
  player1_steam_id: number
  player2_steam_id: number
  player1_kills_on_player2: number
  player2_kills_on_player1: number
  player1_stats: PlayerStats
  player2_stats: PlayerStats
}

// ── Fetch helper ─────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, revalidate = 60): Promise<T> {
  const options: RequestInit & { next?: { revalidate: number } } = {
    next: { revalidate },
  }
  const res = await fetch(`${API_BASE}${path}`, options)
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

// ── API surface ───────────────────────────────────────────────────────────────

export const api = {
  getLeaderboard: (sortBy?: string) =>
    apiFetch<PlayerStats[]>(`/api/players${sortBy ? `?sort_by=${sortBy}` : ''}`),

  getPlayer: (steamId: number | string) =>
    apiFetch<PlayerStats>(`/api/players/${steamId}`),

  getPlayerMatches: (steamId: number | string) =>
    apiFetch<MatchListItem[]>(`/api/players/${steamId}/matches`),

  getPlayerWeapons: (steamId: number | string) =>
    apiFetch<WeaponStats[]>(`/api/players/${steamId}/weapons`),

  getPlayerUtility: (steamId: number | string) =>
    apiFetch<UtilityStats>(`/api/players/${steamId}/utility`),

  getMatches: (page = 0) =>
    apiFetch<MatchListItem[]>(`/api/matches?limit=20&offset=${page * 20}`),

  getMatch: (matchId: string) =>
    apiFetch<MatchDetail>(`/api/matches/${matchId}`),

  getWeaponMeta: () =>
    apiFetch<WeaponStats[]>('/api/weapons'),

  getHeadToHead: (p1: number | string, p2: number | string) =>
    apiFetch<HeadToHeadResponse>(`/api/head-to-head?p1=${p1}&p2=${p2}`),

  getTrends: (steamId: number | string, n = 10) =>
    apiFetch<TrendPoint[]>(`/api/players/${steamId}/trends?n=${n}`),
}
