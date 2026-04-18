'use client'

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import type { WeaponStats } from '@/lib/api'

interface Props {
  weapons: WeaponStats[]
}

export default function WeaponBreakdown({ weapons }: Props) {
  if (weapons.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg p-6 border border-gray-800 flex items-center justify-center h-48">
        <p className="text-gray-500 text-sm">No weapon data yet</p>
      </div>
    )
  }

  const data = [...weapons]
    .sort((a, b) => b.kills - a.kills)
    .slice(0, 10)
    .map((w) => ({ weapon: w.weapon, kills: w.kills }))

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <ResponsiveContainer width="100%" height={Math.max(160, data.length * 32)}>
        <BarChart data={data} layout="vertical">
          <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <YAxis
            type="category"
            dataKey="weapon"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            width={90}
          />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151' }}
            formatter={(v: number) => [v, 'Kills']}
          />
          <Bar dataKey="kills" fill="#f97316" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
