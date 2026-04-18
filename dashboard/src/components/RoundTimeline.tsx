import type { RoundSummary } from '@/lib/api'

interface Props {
  rounds: RoundSummary[]
}

function RoundBlock({ round }: { round: RoundSummary }) {
  return (
    <div
      title={`R${round.round_number}: ${round.winner} — ${round.win_reason}`}
      className={`w-7 h-7 rounded text-xs flex items-center justify-center font-mono select-none ${
        round.winner === 'T'
          ? 'bg-yellow-400 text-yellow-900'
          : 'bg-blue-500 text-blue-100'
      }`}
    >
      {round.round_number}
    </div>
  )
}

export default function RoundTimeline({ rounds }: Props) {
  const firstHalf = rounds.filter((r) => r.round_number <= 12)
  const secondHalf = rounds.filter((r) => r.round_number > 12)

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-2">
      <div className="flex flex-wrap gap-1">
        {firstHalf.map((r) => <RoundBlock key={r.round_number} round={r} />)}
      </div>
      <div className="flex flex-wrap gap-1">
        {secondHalf.map((r) => <RoundBlock key={r.round_number} round={r} />)}
      </div>
    </div>
  )
}
