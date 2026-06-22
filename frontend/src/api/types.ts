// ── Mirrored from backend app/models/ ──

export interface ChatRequest {
  message: string
  model?: string
}

export interface QuizOption {
  key: string
  text: string
}

export interface QuizCard {
  id: string
  question: string
  options: QuizOption[]
  correct_answer: string
  explanation: string
  knowledge_point: string
}

export interface CheckResult {
  correct: boolean
  explanation: string
  correct_answer: string
}

export interface ResourceCard {
  title: string
  url: string
  summary: string
  relevance: string
}

export interface SessionCreate {
  learning_goal: string
}

export interface SessionResponse {
  id: string
  thread_id: string
  learning_goal: string
  progress: number
  status: string
  created_at: string
}

// ── SSE Events ──

export type SSEEventType =
  | 'token'
  | 'done'
  | 'phase_change'
  | 'quiz_card'
  | 'check_result'
  | 'resource_cards'
  | 'progress_update'
  | 'error'

export interface SSEEvent {
  type: SSEEventType
  content?: string
  data?: unknown
  node?: string
  phase?: string
  from?: string
  progress?: number
  knowledge_map?: Record<string, 'mastered' | 'learning' | 'unfamiliar'>
  code?: string
  detail?: string
  cards?: ResourceCard[]
  correct?: boolean
  explanation?: string
  correct_answer?: string
}

// ── Messages ──

export interface Message {
  id: string
  role: 'user' | 'ai' | 'system'
  content: string
  streaming?: boolean
}
