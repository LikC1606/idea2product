/**
 * Projects API - fetch wrapper for Idea2Product backend
 */

const API_BASE = '/api/projects'

export async function createProject(startChat = true) {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start_chat: startChat }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to create project')
  return data
}

export async function listProjects() {
  const res = await fetch(API_BASE)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to list projects')
  return data
}

export async function getChat(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/chat`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to get chat')
  return data
}

export async function postChat(projectId, message) {
  const res = await fetch(`${API_BASE}/${projectId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message.trim() }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to send message')
  return data
}

export async function getStatus(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/status`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to get status')
  return data
}

export function createEventSource(projectId, onMessage) {
  return new EventSource(`${API_BASE}/${projectId}/events`)
}

export async function listFiles(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/files`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to list files')
  return data
}

export async function getFile(projectId, filePath) {
  const res = await fetch(
    `${API_BASE}/${projectId}/file/${encodeURIComponent(filePath)}`
  )
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to get file')
  return data
}

export async function getPreviewUrl(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/preview-url`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to get preview')
  return data
}
