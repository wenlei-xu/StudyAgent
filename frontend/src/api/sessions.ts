import type { SessionResponse, SessionCreate } from './types'

const BASE = '/sessions/'

export async function listSessions(): Promise<SessionResponse[]> {
  const res = await fetch(BASE)
  if (!res.ok) throw new Error(`获取会话列表失败: ${res.status}`)
  const data = await res.json()
  return data.sessions ?? []
}

export async function createSession(
  input: SessionCreate,
): Promise<SessionResponse> {
  const res = await fetch(BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!res.ok) throw new Error(`创建会话失败: ${res.status}`)
  return res.json()
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${BASE}/${sessionId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`删除会话失败: ${res.status}`)
}
