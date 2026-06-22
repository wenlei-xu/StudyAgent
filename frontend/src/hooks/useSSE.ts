import { useEffect, useRef, useCallback } from 'react'
import { connectSSE } from '../api/client'
import type { SSEEvent } from '../api/types'

interface UseSSEOptions {
  sessionId: string
  message: string
  model: string | null
  onEvent: (event: SSEEvent) => void
  onDone: () => void
  onError: (err: Error) => void
  enabled: boolean
}

export function useSSE({
  sessionId,
  message,
  model,
  onEvent,
  onDone,
  onError,
  enabled,
}: UseSSEOptions) {
  const ctrlRef = useRef<AbortController | null>(null)

  const abort = useCallback(() => {
    ctrlRef.current?.abort()
    ctrlRef.current = null
  }, [])

  useEffect(() => {
    if (!enabled || !sessionId || !message) return

    abort()

    ctrlRef.current = connectSSE(sessionId, message, model, onEvent, onDone, onError)

    return () => {
      abort()
    }
  }, [sessionId, message, model, enabled])

  return { abort }
}
