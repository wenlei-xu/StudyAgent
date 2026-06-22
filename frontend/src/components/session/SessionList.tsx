import type { SessionResponse } from '../../api/types'

interface Props {
  sessions: SessionResponse[]
  currentId: string | null
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onCreate: () => void
}

export default function SessionList({
  sessions,
  currentId,
  onSelect,
  onDelete,
  onCreate,
}: Props) {
  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={onCreate}
          className="w-full py-1.5 px-3 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 新建学习会话
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-8">暂无会话</p>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={`px-4 py-3 cursor-pointer border-b border-gray-100 hover:bg-gray-100 transition-colors ${
                s.id === currentId ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
              }`}
            >
              <p className="text-sm font-medium text-gray-800 truncate">
                {s.learning_goal}
              </p>
              <div className="flex items-center justify-between mt-1">
                <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden mr-2">
                  <div
                    className="h-full bg-green-500 rounded-full"
                    style={{ width: `${Math.round(s.progress * 100)}%` }}
                  />
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(s.id)
                  }}
                  className="text-xs text-gray-400 hover:text-red-500"
                >
                  删除
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
