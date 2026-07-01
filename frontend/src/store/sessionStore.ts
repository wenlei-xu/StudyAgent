import { create } from 'zustand'
import type { SessionResponse } from '../api/types'
import { listSessions, createSession, deleteSession } from '../api/sessions'

interface SessionStore {
  sessions: SessionResponse[]
  loading: boolean
  currentSessionId: string | null

  fetchSessions: () => Promise<void>
  createSession: (learningGoal: string) => Promise<SessionResponse>
  removeSession: (id: string) => Promise<void>
  setCurrentSession: (id: string | null) => void
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessions: [],
  loading: false,
  currentSessionId: null,

  fetchSessions: async () => {
    set({ loading: true })
    try {
      const sessions = await listSessions()
      set({ sessions })
    } finally {
      set({ loading: false })
    }
  },

  createSession: async (learningGoal: string) => {
    const session = await createSession({ learning_goal: learningGoal })
    set((s) => ({ sessions: [...s.sessions, session], currentSessionId: session.id }))
    return session.id
  },

  removeSession: async (id: string) => {
    await deleteSession(id)
    set((s) => ({
      sessions: s.sessions.filter((sess) => sess.id !== id),
      currentSessionId: s.currentSessionId === id ? null : s.currentSessionId,
    }))
  },

  setCurrentSession: (id: string | null) => set({ currentSessionId: id }),
}))
