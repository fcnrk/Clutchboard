'use client'

import { useState } from 'react'
import type { HeadToHeadResponse } from '@/lib/api'

export default function HeadToHeadPage() {
  const [p1, setP1] = useState('')
  const [p2, setP2] = useState('')
  const [data, setData] = useState<HeadToHeadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function compare() {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/head-to-head?p1=${p1}&p2=${p2}`
      )
      if (!res.ok) throw new Error(`${res.status}`)
      setData(await res.json())
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Head to Head</h1>

      <div className="flex gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Player 1 Steam ID</label>
          <input
            value={p1}
            onChange={(e) => setP1(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm font-mono w-52"
            placeholder="76561198..."
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Player 2 Steam ID</label>
          <input
            value={p2}
            onChange={(e) => setP2(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm font-mono w-52"
            placeholder="76561198..."
          />
        </div>
        <button
          onClick={compare}
          disabled={!p1 || !p2 || loading}
          className="px-4 py-2 bg-orange-500 hover:bg-orange-400 disabled:opacity-50 rounded text-sm font-medium transition-colors"
        >
          {loading ? 'Loading…' : 'Compare'}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {data && (
        <div className="grid grid-cols-2 gap-6">
          {[
            { stats: data.player1_stats, kills: data.player1_kills_on_player2 },
            { stats: data.player2_stats, kills: data.player2_kills_on_player1 },
          ].map(({ stats, kills }, i) => (
            <div key={i} className="bg-gray-900 rounded-lg p-5 border border-gray-800 space-y-4">
              <div>
                <h3 className="font-bold text-lg">{stats.real_name ?? stats.display_name}</h3>
                {stats.real_name && (
                  <p className="text-gray-400 text-sm">{stats.display_name}</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <Stat label="K/D" value={stats.kd_ratio.toFixed(2)} />
                <Stat label="ADR" value={stats.adr.toFixed(1)} />
                <Stat label="HS%" value={`${stats.hs_pct.toFixed(1)}%`} />
                <Stat label="Win%" value={`${stats.win_rate.toFixed(1)}%`} />
              </div>
              <p className="text-sm text-gray-300">
                Kills on opponent: <span className="font-mono font-bold text-orange-400">{kills}</span>
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-800 rounded p-2">
      <p className="text-xs text-gray-400">{label}</p>
      <p className="font-mono font-semibold">{value}</p>
    </div>
  )
}
