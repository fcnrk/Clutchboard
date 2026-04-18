'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import type { PlayerStats } from '@/lib/api'

const SORT_OPTIONS = [
  { value: 'kd_ratio', label: 'K/D' },
  { value: 'adr', label: 'ADR' },
  { value: 'hs_pct', label: 'HS%' },
  { value: 'total_wins', label: 'Wins' },
  { value: 'total_kills', label: 'Kills' },
]

interface Props {
  players: PlayerStats[]
  currentSort: string
}

export default function Leaderboard({ players, currentSort }: Props) {
  const router = useRouter()

  return (
    <div>
      <div className="flex gap-2 mb-6">
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => router.push(`/?sort_by=${opt.value}`)}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              currentSort === opt.value
                ? 'bg-orange-500 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-800 text-xs uppercase tracking-wider">
            <th className="py-2 pr-4 w-8">#</th>
            <th className="py-2 pr-4">Player</th>
            <th className="py-2 pr-4 text-right">Matches</th>
            <th className="py-2 pr-4 text-right">K/D</th>
            <th className="py-2 pr-4 text-right">ADR</th>
            <th className="py-2 pr-4 text-right">HS%</th>
            <th className="py-2 pr-4 text-right">Wins</th>
            <th className="py-2 text-right">Win%</th>
          </tr>
        </thead>
        <tbody>
          {players.map((p, i) => (
            <tr
              key={p.steam_id}
              className="border-b border-gray-800/50 hover:bg-gray-900/40 transition-colors"
            >
              <td className="py-3 pr-4 text-gray-500 text-xs">{i + 1}</td>
              <td className="py-3 pr-4">
                <Link
                  href={`/players/${p.steam_id}`}
                  className="hover:text-orange-400 transition-colors"
                >
                  <span className="font-medium">{p.real_name ?? p.display_name}</span>
                  {p.real_name && (
                    <span className="text-gray-500 text-xs ml-2">({p.display_name})</span>
                  )}
                </Link>
              </td>
              <td className="py-3 pr-4 text-right text-gray-300">{p.total_matches}</td>
              <td className="py-3 pr-4 text-right font-mono">{p.kd_ratio.toFixed(2)}</td>
              <td className="py-3 pr-4 text-right font-mono">{p.adr.toFixed(1)}</td>
              <td className="py-3 pr-4 text-right font-mono">{p.hs_pct.toFixed(1)}%</td>
              <td className="py-3 pr-4 text-right font-mono">{p.total_wins}</td>
              <td className="py-3 text-right font-mono">{p.win_rate.toFixed(1)}%</td>
            </tr>
          ))}
          {players.length === 0 && (
            <tr>
              <td colSpan={8} className="py-8 text-center text-gray-500">
                No players yet. Start a match to see stats here.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
