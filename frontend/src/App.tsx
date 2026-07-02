import { useSessionStore } from './store/sessionStore'
import SessionList from './components/session/SessionList'
import SessionCreate from './components/session/SessionCreate'
import ChatPanel from './components/chat/ChatPanel'
import KnowledgePanel from './components/knowledge/KnowledgePanel'
import ModelSelector from './components/common/ModelSelector'
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

export default function App() {
  const {
    sessions,
    currentSessionId,
    fetchSessions,
    createSession,
    removeSession,
    setCurrentSession,
  } = useSessionStore()

  const [showCreate, setShowCreate] = useState(false)
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  useEffect(() => {
    fetchSessions()
  }, [])

  // Sync URL param → store
  useEffect(() => {
    if (sessionId && sessionId !== currentSessionId) {
      setCurrentSession(sessionId)
    }
  }, [sessionId])

  const handleSelect = (id: string) => {
    setCurrentSession(id)
    navigate(`/chat/${id}`)
  }

  const handleCreate = async (goal: string) => {
    const id = await createSession(goal)
    if (id) navigate(`/chat/${id}`)
  }

  return (
    <div className="flex h-screen bg-white">
      <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200">
          <ModelSelector />
        </div>
        <SessionList
          sessions={sessions}
          currentId={currentSessionId}
          onSelect={handleSelect}
          onDelete={removeSession}
          onCreate={() => setShowCreate(true)}
        />
      </div>

      <div className="flex-1 flex flex-col">
        {currentSessionId ? (
          <ChatPanel sessionId={currentSessionId} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-lg mb-2">选择一个学习会话开始</p>
              <p className="text-sm">或点击左侧"新建学习会话"创建</p>
            </div>
          </div>
        )}
      </div>

      {currentSessionId && <KnowledgePanel sessionId={currentSessionId} />}

      <SessionCreate
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}
