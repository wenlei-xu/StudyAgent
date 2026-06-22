import ProgressBar from '../knowledge/ProgressBar'

const PHASE_LABELS: Record<string, string> = {
  idle: '就绪',
  explaining: '正在讲解…',
  quiz: '答题中',
  checking: '批改中',
  recommending: '正在推荐…',
}

interface Props {
  phase: string
  progress: number
}

export default function PhaseIndicator({ phase, progress }: Props) {
  if (phase === 'idle' && progress === 0) return null

  return (
    <div className="border-b border-gray-100 bg-white px-4 py-2">
      <div className="max-w-3xl mx-auto flex items-center gap-3">
        <span className="text-xs font-medium text-gray-500">
          {PHASE_LABELS[phase] ?? phase}
        </span>
        {progress > 0 && (
          <div className="max-w-[160px] flex-1">
            <ProgressBar progress={progress} size="sm" showLabel />
          </div>
        )}
      </div>
    </div>
  )
}
