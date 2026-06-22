import { useSessionStore } from './store/sessionStore'
import SessionList from './components/session/SessionList'
import SessionCreate from './components/session/SessionCreate'
import ChatPanel from './components/chat/ChatPanel'
import { useState, useEffect } from 'react'

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

  useEffect(() => {
    fetchSessions()
  }, [])

  return (
    <div className="flex h-screen bg-white">
      <SessionList
        sessions={sessions}
        currentId={currentSessionId}
        onSelect={setCurrentSession}
        onDelete={removeSession}
        onCreate={() => setShowCreate(true)}
      />

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

      <SessionCreate
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreate={async (goal) => {
          await createSession(goal)
        }}
      />
    </div>
  )
}
