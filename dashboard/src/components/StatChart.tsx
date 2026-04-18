'use client'

import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import type { TrendPoint } from '@/lib/api'

interface Props {
  data: TrendPoint[]
}

const STATS = ['kd_ratio', 'adr', 'hs_pct'] as const
type Stat = typeof STATS[number]

const LABELS: Record<Stat, string> = { kd_ratio: 'K/D', adr: 'ADR', hs_pct: 'HS%' }

export default function StatChart({ data }: Props) {
  const [stat, setStat] = useState<Stat>('kd_ratio')

  if (data.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 flex items-center justify-center h-48">
        <p className="text-gray-500 text-sm">No match data yet</p>
      </div>
    )
  }

  // API returns newest-first; chart shows oldest→newest
  const chartData = [...data].reverse().map((p, i) => ({
    match: i + 1,
    value: p[stat],
  }))

  const mean = chartData.reduce((sum, p) => sum + p.value, 0) / chartData.length

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <div className="flex gap-2 mb-4">
        {STATS.map((s) => (
          <button
            key={s}
            onClick={() => setStat(s)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              stat === s
                ? 'bg-orange-500 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {LABELS[s]}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={chartData}>
          <XAxis dataKey="match" tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} width={40} />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151' }}
            labelFormatter={(v) => `Match ${v}`}
            formatter={(v: number) => [v.toFixed(2), LABELS[stat]]}
          />
          <ReferenceLine y={mean} stroke="#6b7280" strokeDasharray="3 3" />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#f97316"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
