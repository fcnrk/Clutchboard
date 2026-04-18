export const dynamic = 'force-dynamic'

import { api } from '@/lib/api'
import WeaponBreakdown from '@/components/WeaponBreakdown'

export default async function WeaponsPage() {
  const weapons = await api.getWeaponMeta()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Server Weapon Meta</h1>

      <WeaponBreakdown weapons={weapons} />

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-800 text-xs uppercase">
            <th className="py-2 pr-4">Weapon</th>
            <th className="py-2 pr-4 text-right">Kills</th>
            <th className="py-2 pr-4 text-right">HS Kills</th>
            <th className="py-2 pr-4 text-right">HS%</th>
            <th className="py-2 text-right">Accuracy</th>
          </tr>
        </thead>
        <tbody>
          {weapons.map((w) => (
            <tr key={w.weapon} className="border-b border-gray-800/50">
              <td className="py-2 pr-4 font-mono">{w.weapon}</td>
              <td className="py-2 pr-4 text-right">{w.kills}</td>
              <td className="py-2 pr-4 text-right">{w.headshot_kills}</td>
              <td className="py-2 pr-4 text-right">{w.hs_pct.toFixed(1)}%</td>
              <td className="py-2 text-right">{w.accuracy.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
