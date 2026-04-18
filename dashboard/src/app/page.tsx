export const dynamic = 'force-dynamic'

import { api } from '@/lib/api'
import Leaderboard from '@/components/Leaderboard'

export default async function LeaderboardPage({
  searchParams,
}: {
  searchParams: { sort_by?: string }
}) {
  const sortBy = searchParams.sort_by ?? 'kd_ratio'
  const players = await api.getLeaderboard(sortBy)

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Leaderboard</h1>
      <Leaderboard players={players} currentSort={sortBy} />
    </div>
  )
}
