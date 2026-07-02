import type { KnowledgeNote, GraphData } from './types'

export async function fetchAllNotes(
  tag?: string,
  limit = 200,
  offset = 0,
): Promise<KnowledgeNote[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (tag) params.set('tag', tag)
  const res = await fetch(`/notes?${params}`)
  if (!res.ok) return []
  const data = await res.json()
  return data.notes ?? []
}

export async function fetchNotes(
  sessionId: string,
  tag?: string,
  limit = 50,
  offset = 0,
): Promise<KnowledgeNote[]> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (tag) params.set('tag', tag)
  const res = await fetch(`/sessions/${sessionId}/notes?${params}`)
  if (!res.ok) return []
  const data = await res.json()
  return data.notes ?? []
}

export async function searchNotes(sessionId: string, query: string): Promise<KnowledgeNote[]> {
  if (!query.trim()) return []
  const res = await fetch(`/sessions/${sessionId}/notes/search?q=${encodeURIComponent(query)}`)
  if (!res.ok) return []
  const data = await res.json()
  return data.notes ?? []
}

export async function createNote(
  sessionId: string,
  topic: string,
  content: string,
  tags: string[] = [],
): Promise<KnowledgeNote | null> {
  const res = await fetch(`/sessions/${sessionId}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, content, tags }),
  })
  if (!res.ok) return null
  return res.json()
}

export async function updateNote(
  sessionId: string,
  noteId: string,
  data: { topic?: string; content?: string; tags?: string[] },
): Promise<KnowledgeNote | null> {
  const res = await fetch(`/sessions/${sessionId}/notes/${noteId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) return null
  return res.json()
}

export async function deleteNote(sessionId: string, noteId: string): Promise<boolean> {
  const res = await fetch(`/sessions/${sessionId}/notes/${noteId}`, { method: 'DELETE' })
  return res.ok
}

export async function fetchTags(sessionId: string): Promise<string[]> {
  const res = await fetch(`/sessions/${sessionId}/notes/tags`)
  if (!res.ok) return []
  const data = await res.json()
  return data.tags ?? []
}

export async function fetchGraphData(sessionId: string): Promise<GraphData> {
  const res = await fetch(`/sessions/${sessionId}/notes/graph`)
  if (!res.ok) return { nodes: [], edges: [] }
  return res.json()
}

export async function fetchAllGraphData(): Promise<GraphData> {
  const res = await fetch('/notes/graph')
  if (!res.ok) return { nodes: [], edges: [] }
  return res.json()
}

export async function autoSummarizeNotes(sessionId: string, aiMessage?: string): Promise<KnowledgeNote[]> {
  const res = await fetch(`/sessions/${sessionId}/notes/auto-summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ai_message: aiMessage ?? '' }),
  })
  if (!res.ok) return []
  const data = await res.json()
  return data.notes ?? []
}
