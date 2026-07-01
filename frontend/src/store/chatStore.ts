import { create } from 'zustand'
import type { Message, QuizCard, CheckResult, ResourceCard, LearningStage, HomeworkResult } from '../api/types'
import { connectSSE } from '../api/client'
import { fetchStages, generateStages, submitHomework } from '../api/stages'

let msgCounter = 0

interface ChatStore {
  streaming: boolean
  currentPhase: 'idle' | 'planning' | 'explaining' | 'quiz' | 'checking' | 'recommending'

  messages: Message[]
  quizCard: QuizCard | null
  checkResult: CheckResult | null
  resourceCards: ResourceCard[]
  errorMessage: string | null

  knowledgeMap: Record<string, 'mastered' | 'learning' | 'unfamiliar'>
  progress: number

  selectedModel: string | null
  activeRequest: AbortController | null

  // Stage-related state
  stages: LearningStage[]
  homeworkResult: HomeworkResult | null
  stagesLoading: boolean

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

  // Stage-related actions
  fetchStagesAction: (sessionId: string) => Promise<void>
  generateStagesAction: (sessionId: string) => Promise<void>
  submitHomeworkAction: (sessionId: string, stageId: number, answer: string) => Promise<void>
  clearHomeworkResult: () => void
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

  // Stage state
  stages: [],
  homeworkResult: null,
  stagesLoading: false,

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
          case 'stages_generated':
            if (event.stages) {
              set({ stages: event.stages })
            }
            break
          case 'stage_change':
            if (event.current_stage) {
              // Update the active stage in our stages list
              const updatedStages = get().stages.map((s: LearningStage) => ({
                ...s,
                status: s.stage_number === event.current_stage!.stage_number ? 'active' as const : s.status,
              }))
              set({ stages: updatedStages })
            }
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

  // ── Stage actions ──

  fetchStagesAction: async (sessionId: string) => {
    set({ stagesLoading: true })
    try {
      const stages = await fetchStages(sessionId)
      set({ stages, stagesLoading: false })
    } catch {
      set({ stagesLoading: false })
    }
  },

  generateStagesAction: async (sessionId: string) => {
    set({ stagesLoading: true })
    try {
      const stages = await generateStages(sessionId)
      set({ stages, stagesLoading: false })
    } catch {
      set({ stagesLoading: false })
    }
  },

  submitHomeworkAction: async (sessionId: string, stageId: number, answer: string) => {
    set({ streaming: true })
    try {
      const result = await submitHomework(sessionId, stageId, answer)
      set({ homeworkResult: result, streaming: false })
      // Refresh stages after submission
      const stages = await fetchStages(sessionId)
      set({ stages, progress: result.next_stage_unlocked ? get().progress + (1 / stages.length) : get().progress })
    } catch {
      set({ streaming: false, errorMessage: '作业提交失败，请重试' })
    }
  },

  clearHomeworkResult: () => set({ homeworkResult: null }),
}))
