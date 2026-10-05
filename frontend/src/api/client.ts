import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}

export async function getKnowledgeGraph(params: Record<string, unknown>) {
  const { data } = await api.get('/kg/visualization', { params })
  return data
}

export async function getKnowledgeGraphStatus() {
  const { data } = await api.get('/kg/status')
  return data
}

export async function getEntityGraph(focusId: string) {
  const { data } = await api.get('/kg/visualization', { params: { focus_id: focusId, max_nodes: 60 } })
  return data
}

export async function searchEntities(query: string) {
  const { data } = await api.get('/kg/search', { params: { query, limit: 8 } })
  return data
}

export async function createStageSession() {
  const { data } = await api.post('/topic/stage/create')
  return data
}

export async function submitStage(sessionId: string, stage: number, payload: Record<string, unknown>) {
  const { data } = await api.post(`/topic/stage/submit/${sessionId}/${stage}`, payload)
  return data
}

export async function getStageData(sessionId: string, stage: number) {
  const { data } = await api.get(`/topic/stage/data/${sessionId}/${stage}`)
  return data
}

export async function sendChat(message: string, sessionId: string) {
  const { data } = await api.post('/chat', { message, user_id: sessionId, session_id: sessionId })
  return data
}

export async function submitFeedback(payload: Record<string, unknown>) {
  const { data } = await api.post('/topic/feedback', payload)
  return data
}
