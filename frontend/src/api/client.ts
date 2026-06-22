import {
  fetchEventSource,
  EventStreamContentType,
} from '@microsoft/fetch-event-source'
import type { SSEEvent } from './types'

class RetriableError extends Error {}
class FatalError extends Error {}

export function connectSSE(
  sessionId: string,
  message: string,
  onEvent: (event: SSEEvent) => void,
  onClose: () => void,
  onError: (err: Error) => void,
): AbortController {
  const controller = new AbortController()

  fetchEventSource(`/chat/${sessionId}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
    signal: controller.signal,
    openWhenHidden: true,

    async onopen(response) {
      if (
        response.ok &&
        response.headers.get('content-type')?.includes(EventStreamContentType)
      ) {
        return
      }
      if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        throw new FatalError(`请求失败: ${response.status}`)
      }
      throw new RetriableError(`连接失败: ${response.status}`)
    },

    onmessage(msg) {
      if (msg.data === '[DONE]') {
        onEvent({ type: 'done' })
        return
      }
      try {
        const event: SSEEvent = JSON.parse(msg.data)
        onEvent(event)
      } catch {
        console.warn('SSE parse error:', msg.data)
      }
    },

    onclose() {
      onClose()
    },

    onerror(err) {
      if (err instanceof FatalError) {
        onError(err)
        throw err
      }
      onError(err)
    },
  })

  return controller
}
