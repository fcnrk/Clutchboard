import type { PlayerStats } from '@/lib/api'

interface Props {
  player: PlayerStats
}

export default function PlayerCard({ player }: Props) {
  const name = player.real_name ?? player.display_name

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <div className="mb-4">
        <h2 className="text-xl font-bold">{name}</h2>
        {player.real_name && (
          <p className="text-gray-400 text-sm">{player.display_name}</p>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Stat label="K/D" value={player.kd_ratio.toFixed(2)} />
        <Stat label="ADR" value={player.adr.toFixed(1)} />
        <Stat label="HS%" value={`${player.hs_pct.toFixed(1)}%`} />
        <Stat label="Win%" value={`${player.win_rate.toFixed(1)}%`} />
        <Stat label="Kills" value={player.total_kills.toString()} />
        <Stat label="Deaths" value={player.total_deaths.toString()} />
        <Stat label="Assists" value={player.total_assists.toString()} />
        <Stat label="Matches" value={player.total_matches.toString()} />
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-800 rounded p-3">
      <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-lg font-mono font-semibold">{value}</p>
    </div>
  )
}
