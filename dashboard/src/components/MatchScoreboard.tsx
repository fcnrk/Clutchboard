import type { MatchScoreboardEntry } from '@/lib/api'

interface Props {
  scoreboard: MatchScoreboardEntry[]
}

export default function MatchScoreboard({ scoreboard }: Props) {
  const tSide = scoreboard.filter((p) => p.team === 'T')
  const ctSide = scoreboard.filter((p) => p.team === 'CT')

  return (
    <div className="space-y-4">
      {[
        { label: 'Terrorist', players: tSide, color: 'text-yellow-400' },
        { label: 'Counter-Terrorist', players: ctSide, color: 'text-blue-400' },
      ].map(({ label, players, color }) => (
        <div key={label}>
          <h4 className={`text-sm font-semibold mb-2 ${color}`}>{label}</h4>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800 text-xs uppercase">
                <th className="py-1.5 pr-4">Player</th>
                <th className="py-1.5 pr-4 text-right">K</th>
                <th className="py-1.5 pr-4 text-right">D</th>
                <th className="py-1.5 pr-4 text-right">A</th>
                <th className="py-1.5 pr-4 text-right">ADR</th>
                <th className="py-1.5 pr-4 text-right">HS</th>
                <th className="py-1.5 text-right">MVP</th>
              </tr>
            </thead>
            <tbody>
              {players.map((p) => (
                <tr key={p.steam_id} className="border-b border-gray-800/30">
                  <td className="py-2 pr-4">
                    {p.real_name ?? p.display_name}
                    {p.real_name && (
                      <span className="text-gray-500 text-xs ml-1">({p.display_name})</span>
                    )}
                  </td>
                  <td className="py-2 pr-4 text-right font-mono">{p.kills}</td>
                  <td className="py-2 pr-4 text-right font-mono">{p.deaths}</td>
                  <td className="py-2 pr-4 text-right font-mono">{p.assists}</td>
                  <td className="py-2 pr-4 text-right font-mono">{p.adr.toFixed(1)}</td>
                  <td className="py-2 pr-4 text-right font-mono">{p.headshot_kills}</td>
                  <td className="py-2 text-right font-mono">{p.mvp_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
