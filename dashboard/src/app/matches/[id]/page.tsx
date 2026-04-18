import { api } from '@/lib/api'
import MatchScoreboard from '@/components/MatchScoreboard'
import RoundTimeline from '@/components/RoundTimeline'

export default async function MatchDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const match = await api.getMatch(params.id)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-mono">{match.map_name}</h1>
          <p className="text-gray-400 text-sm">
            {new Date(match.started_at).toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-mono font-bold">
            <span className="text-yellow-400">{match.t_score}</span>
            <span className="text-gray-500 mx-2">–</span>
            <span className="text-blue-400">{match.ct_score}</span>
          </p>
          <p className="text-gray-400 text-xs uppercase">{match.status}</p>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Scoreboard</h3>
        <MatchScoreboard scoreboard={match.scoreboard} />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-3">Round Timeline</h3>
        <RoundTimeline rounds={match.rounds} />
      </div>
    </div>
  )
}
