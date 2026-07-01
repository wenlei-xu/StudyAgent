import { create } from 'zustand'
import type { Message, QuizCard, CheckResult, ResourceCard } from '../api/types'
import { connectSSE } from '../api/client'

let msgCounter = 0

interface ChatStore {
  streaming: boolean
  currentPhase: 'idle' | 'explaining' | 'quiz' | 'checking' | 'recommending'

  messages: Message[]
  quizCard: QuizCard | null
  checkResult: CheckResult | null
  resourceCards: ResourceCard[]
  errorMessage: string | null

  knowledgeMap: Record<string, 'mastered' | 'learning' | 'unfamiliar'>
  progress: number

  selectedModel: string | null
  activeRequest: AbortController | null

  sendMessage: (sessionId: string, text: string) => void
  submitAnswer: (sessionId: string, option: string) => void
  loadHistory: (sessionId: string) => Promise<void>
  resetSession: () => void
  appendToken: (token: string) => void
  setQuizCard: (card: QuizCard) => void
  setCheckResult: (result: CheckResult) => void
  setSelectedModel: (model: string | null) => void
  clearError: () => void
  abort: () => void
}

export const useChatStore = create<ChatStore>((set, get) => ({
  streaming: false,
  currentPhase: 'idle',

  messages: [],
  quizCard: null,
  checkResult: null,
  resourceCards: [],
  errorMessage: null,

  knowledgeMap: {},
  progress: 0,

  activeRequest: null,
  selectedModel: 'deepseek-v4-flash',

  sendMessage: (sessionId: string, text: string) => {
    const state = get()
    if (state.streaming) return
    state.abort()

    const userMsg: Message = {
      id: `msg-${++msgCounter}`,
      role: 'user',
      content: text,
    }
    const aiMsg: Message = {
      id: `msg-${++msgCounter}`,
      role: 'ai',
      content: '',
      streaming: true,
    }

    set({
      messages: [...state.messages, userMsg, aiMsg],
      streaming: true,
      errorMessage: null,
      quizCard: null,
      checkResult: null,
      resourceCards: [],
    })

    const ctrl = connectSSE(
      sessionId,
      text,
      state.selectedModel,
      (event) => {
        const s = get()
        switch (event.type) {
          case 'token':
            if (event.content) s.appendToken(event.content)
            break
          case 'phase_change':
            set({ currentPhase: (event.phase as ChatStore['currentPhase']) ?? 'idle' })
            break
          case 'quiz_card':
            set({ quizCard: event.data as QuizCard, currentPhase: 'quiz' })
            break
          case 'check_result':
            set({
              checkResult: {
                correct: event.correct!,
                explanation: event.explanation!,
                correct_answer: event.correct_answer!,
              },
              currentPhase: 'checking',
            })
            break
          case 'resource_cards':
            set({ resourceCards: event.cards ?? [], currentPhase: 'recommending' })
            break
          case 'progress_update':
            set({
              progress: event.progress ?? s.progress,
              knowledgeMap: event.knowledge_map ?? s.knowledgeMap,
            })
            break
          case 'done':
            set({ streaming: false, currentPhase: 'idle' })
            break
          case 'error':
            set({
              errorMessage: event.detail ?? '未知错误',
              streaming: false,
            })
            break
        }
      },
      () => {
        set({ streaming: false })
      },
      (_err) => {
        set({ streaming: false })
      },
    )

    set({ activeRequest: ctrl })
  },

  submitAnswer: (sessionId: string, option: string) => {
    get().sendMessage(sessionId, option)
  },

  loadHistory: async (sessionId: string) => {
    const state = get()
    // Already loaded for this session → skip
    if (!state.streaming && state.messages.length > 0 && state.messages[0]?.id?.startsWith(`hist-${sessionId.slice(0, 8)}`)) {
      return
    }
    get().resetSession()
    try {
      const res = await fetch(`/chat/${sessionId}/history`)
      if (!res.ok) return
      const data = await res.json()
      const msgs: Message[] = (data.messages ?? []).map((m: { id?: string; role: string; content: string }, i: number) => ({
        id: m.id ?? `hist-${sessionId.slice(0, 8)}-${i}`,
        role: m.role as 'user' | 'ai',
        content: m.content,
      }))
      set({
        messages: msgs,
        knowledgeMap: data.knowledge_map ?? {},
        progress: data.progress ?? 0,
      })
    } catch {
      // ignore — no history is fine, start fresh
    }
  },

  resetSession: () => set({
    messages: [],
    streaming: false,
    currentPhase: 'idle',
    quizCard: null,
    checkResult: null,
    resourceCards: [],
    errorMessage: null,
    knowledgeMap: {},
    progress: 0,
  }),

  appendToken: (token: string) => {
    set((s) => {
      const msgs = [...s.messages]
      const last = msgs[msgs.length - 1]
      if (last && last.role === 'ai') {
        msgs[msgs.length - 1] = {
          ...last,
          content: last.content + token,
        }
      }
      return { messages: msgs }
    })
  },

  setQuizCard: (card: QuizCard) => set({ quizCard: card, currentPhase: 'quiz' }),

  setCheckResult: (result: CheckResult) =>
    set({ checkResult: result, currentPhase: 'checking' }),

  setSelectedModel: (model: string | null) => set({ selectedModel: model }),

  clearError: () => set({ errorMessage: null }),

  abort: () => {
    const { activeRequest } = get()
    if (activeRequest) {
      activeRequest.abort()
      set((s) => {
        const msgs = [...s.messages]
        const last = msgs[msgs.length - 1]
        if (last && last.role === 'ai' && last.streaming) {
          msgs[msgs.length - 1] = { ...last, streaming: false }
        }
        return { messages: msgs, activeRequest: null, streaming: false, currentPhase: 'idle' as const }
      })
    }
  },
}))
