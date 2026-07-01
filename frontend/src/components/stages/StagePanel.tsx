import type { LearningStage } from '../../api/types'

interface Props {
  stages: LearningStage[]
  loading: boolean
}

const STATUS_ICON: Record<string, string> = {
  completed: '✅',
  active: '📖',
  locked: '🔒',
}

const STATUS_LABEL: Record<string, string> = {
  completed: '已完成',
  active: '学习中',
  locked: '未解锁',
}

export default function StagePanel({ stages, loading }: Props) {
  if (loading) {
    return (
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
        <p className="text-xs text-gray-400 text-center">正在生成学习阶段…</p>
      </div>
    )
  }

  if (stages.length === 0) {
    return (
      <div className="border-b border-gray-200 bg-amber-50 px-4 py-3">
        <p className="text-xs text-amber-700 text-center">
          💡 在聊天框输入你想学习的目标，AI 将为你自动生成学习计划
        </p>
      </div>
    )
  }

  return (
    <div className="border-b border-gray-200 bg-gray-50 px-4 py-3">
      <div className="flex items-center gap-2 overflow-x-auto">
        {stages.map((stage, i) => (
          <div key={stage.id} className="flex items-center gap-1 shrink-0">
            {i > 0 && (
              <div
                className={`w-6 h-0.5 ${
                  stage.status === 'locked' ? 'bg-gray-300' : 'bg-green-400'
                }`}
              />
            )}
            <div
              className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs whitespace-nowrap ${
                stage.status === 'active'
                  ? 'bg-blue-100 text-blue-800 ring-1 ring-blue-300'
                  : stage.status === 'completed'
                    ? 'bg-green-50 text-green-700'
                    : 'bg-gray-100 text-gray-400'
              }`}
              title={`${stage.title}\n${stage.description}`}
            >
              <span>{STATUS_ICON[stage.status]}</span>
              <span className="font-medium">{stage.title}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
