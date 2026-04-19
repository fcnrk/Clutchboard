export const dynamic = 'force-dynamic'

import Link from 'next/link'
import { api } from '@/lib/api'

export default async function MatchesPage() {
  const matches = await api.getMatches()

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Match History</h1>
      <div className="space-y-2">
        {matches.map((m) => (
          <Link
            key={m.id}
            href={`/matches/${m.id}`}
            className="flex items-center justify-between bg-gray-900 rounded-lg p-4 border border-gray-800 hover:border-gray-600 transition-colors"
          >
            <div>
              <span className="font-mono font-semibold">{m.map_name}</span>
              <span
                className={`ml-3 text-xs px-2 py-0.5 rounded ${
                  m.status === 'completed'
                    ? 'bg-green-900 text-green-300'
                    : 'bg-yellow-900 text-yellow-300'
                }`}
              >
                {m.status}
              </span>
            </div>
            <div className="text-right">
              <span className="font-mono text-lg">
                {m.t_score} – {m.ct_score}
              </span>
              <p className="text-gray-400 text-xs">
                {new Date(m.started_at).toLocaleDateString(undefined, {
                  year: 'numeric', month: 'short', day: 'numeric',
                  hour: '2-digit', minute: '2-digit',
                })}
              </p>
            </div>
          </Link>
        ))}
        {matches.length === 0 && (
          <p className="text-gray-500 text-center py-12">No matches recorded yet.</p>
        )}
      </div>
    </div>
  )
}
