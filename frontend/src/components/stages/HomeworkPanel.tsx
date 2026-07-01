import { useState } from 'react'
import type { LearningStage, HomeworkResult } from '../../api/types'

interface Props {
  stage: LearningStage
  result: HomeworkResult | null
  loading: boolean
  onSubmit: (answer: string) => void
  onClearResult: () => void
}

export default function HomeworkPanel({
  stage,
  result,
  loading,
  onSubmit,
  onClearResult,
}: Props) {
  const [answer, setAnswer] = useState('')
  const [expanded, setExpanded] = useState(false)

  const handleSubmit = () => {
    const trimmed = answer.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  return (
    <div className="border border-blue-200 rounded-xl bg-blue-50/50 mx-4 mt-4">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-blue-50 rounded-xl transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm">📝</span>
          <span className="text-sm font-semibold text-blue-800">
            阶段作业：{stage.title}
          </span>
        </div>
        <span className="text-xs text-blue-500">{expanded ? '收起 ▲' : '展开 ▼'}</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Stage description */}
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">阶段内容</p>
            <p className="text-sm text-gray-700">{stage.description}</p>
          </div>

          {/* Homework */}
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">作业要求</p>
            <div className="text-sm text-gray-800 bg-white rounded-lg p-3 border border-blue-100">
              {stage.homework}
            </div>
          </div>

          {/* Result */}
          {result && (
            <div
              className={`rounded-lg p-3 ${
                result.passed
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-red-50 border border-red-200'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span
                  className={`text-sm font-semibold ${
                    result.passed ? 'text-green-700' : 'text-red-700'
                  }`}
                >
                  {result.passed ? '✅ 作业通过！' : '❌ 作业未通过'}
                </span>
                <button
                  onClick={onClearResult}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  关闭
                </button>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.feedback}</p>
              {result.next_stage_unlocked && (
                <p className="text-sm text-green-600 font-medium mt-1">
                  🎉 下一阶段已解锁！
                </p>
              )}
            </div>
          )}

          {/* Answer input (only show if no result or failed) */}
          {(!result || !result.passed) && (
            <div>
              <p className="text-xs font-medium text-gray-500 mb-1">
                {result && !result.passed ? '根据反馈修改后重新提交' : '提交你的作业'}
              </p>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="在这里输入你的作业答案…"
                rows={6}
                className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
              <button
                onClick={handleSubmit}
                disabled={!answer.trim() || loading}
                className="mt-2 px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? '提交中…' : '提交作业'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
