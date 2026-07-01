import { useState } from 'react'

interface Props {
  open: boolean
  onClose: () => void
  onCreate: (goal: string) => void
}

export default function SessionCreate({ open, onClose, onCreate }: Props) {
  const [goal, setGoal] = useState('')

  if (!open) return null

  const handleSubmit = () => {
    const trimmed = goal.trim()
    // Auto-generate title if user doesn't input one
    const title = trimmed || `学习会话 ${new Date().toLocaleDateString('zh-CN')}`
    onCreate(title)
    setGoal('')
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-[400px] max-w-[90vw] shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">新建学习会话</h3>
        <label className="text-sm text-gray-600 mb-2 block">
          会话标题（留空则自动生成）
        </label>
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="例如：Python 异步编程学习"
          className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
          autoFocus
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSubmit()
          }}
        />
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  )
}
