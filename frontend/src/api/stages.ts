import type { LearningStage, HomeworkResult } from './types'

const BASE = '/sessions/'

export async function fetchStages(sessionId: string): Promise<LearningStage[]> {
  const res = await fetch(`${BASE}${sessionId}/stages`)
  if (!res.ok) throw new Error(`获取学习阶段失败: ${res.status}`)
  const data = await res.json()
  return data.stages ?? []
}

export async function generateStages(sessionId: string): Promise<LearningStage[]> {
  const res = await fetch(`${BASE}${sessionId}/stages/generate`, { method: 'POST' })
  if (!res.ok) throw new Error(`生成学习阶段失败: ${res.status}`)
  const data = await res.json()
  return data.stages ?? []
}

export async function submitHomework(
  sessionId: string,
  stageId: number,
  answer: string,
): Promise<HomeworkResult> {
  const res = await fetch(`${BASE}${sessionId}/stages/${stageId}/submit-homework`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answer }),
  })
  if (!res.ok) throw new Error(`提交作业失败: ${res.status}`)
  return res.json()
}
