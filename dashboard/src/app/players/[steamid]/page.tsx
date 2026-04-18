import Link from 'next/link'
import { api } from '@/lib/api'
import PlayerCard from '@/components/PlayerCard'
import StatChart from '@/components/StatChart'
import WeaponBreakdown from '@/components/WeaponBreakdown'

export default async function PlayerPage({
  params,
}: {
  params: { steamid: string }
}) {
  const [player, matches, weapons, trends] = await Promise.all([
    api.getPlayer(params.steamid),
    api.getPlayerMatches(params.steamid),
    api.getPlayerWeapons(params.steamid),
    api.getTrends(params.steamid),
  ])

  return (
    <div className="space-y-6">
      <PlayerCard player={player} />

      <div>
        <h3 className="text-lg font-semibold mb-3">Performance Trend</h3>
        <StatChart data={trends} />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Weapon Stats</h3>
        <WeaponBreakdown weapons={weapons} />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Recent Matches</h3>
        <div className="space-y-2">
          {matches.map((m) => (
            <Link
              key={m.id}
              href={`/matches/${m.id}`}
              className="flex items-center justify-between bg-gray-900 rounded p-3 border border-gray-800 hover:border-gray-600 transition-colors"
            >
              <span className="font-mono text-sm">{m.map_name}</span>
              <span className="text-gray-400 text-sm">
                {m.t_score} – {m.ct_score}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
