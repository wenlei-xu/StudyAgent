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
    if (!trimmed) return
    onCreate(trimmed)
    setGoal('')
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-[400px] max-w-[90vw] shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">新建学习会话</h3>
        <label className="text-sm text-gray-600 mb-2 block">学习目标</label>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="例如：熟练掌握 Python 异步编程"
          rows={3}
          className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
          autoFocus
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
            disabled={!goal.trim()}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  )
}
