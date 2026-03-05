/**
 * Projects API - fetch wrapper for Idea2Product backend
 * Set VITE_API_BASE in .env (e.g. http://127.0.0.1:8080) if backend runs on different origin.
 */

function getApiBase() {
  const envBase = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
  if (envBase) return envBase + '/api/projects'
  // file:// or unknown origin → must use explicit backend URL
  if (typeof window !== 'undefined') {
    if (window.location.protocol === 'file:') {
      return 'http://127.0.0.1:8080/api/projects'
    }
    if (window.location.port === '5173') {
      return `http://${window.location.hostname}:8080/api/projects`
    }
  }
  return '/api/projects'
}

const API_BASE = getApiBase()

async function parseJson(res, url = '') {
  const text = await res.text()
  const ct = res.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    if (text.trim().toLowerCase().startsWith('<!doctype') || text.trim().startsWith('<!')) {
      const hint = url ? `\nURL: ${url}` : ''
      throw new Error(
        `API 返回了 HTML 而非 JSON。请确认：1) 后端已启动：python -m src.web.app  2) 访问地址为 http://localhost:8080${hint}`
      )
    }
    throw new Error(text.slice(0, 200) || 'Invalid response')
  }
  try {
    return text ? JSON.parse(text) : {}
  } catch (e) {
    throw new Error('Invalid JSON: ' + text.slice(0, 100))
  }
}

/** Check if backend is reachable. Returns true if OK, false otherwise. */
export async function checkBackend() {
  try {
    const res = await fetch(API_BASE, { method: 'GET' })
    const ct = res.headers.get('content-type') || ''
    if (!ct.includes('application/json')) return false
    await res.json()
    return true
  } catch {
    return false
  }
}

export async function createProject(startChat = true) {
  const res = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start_chat: startChat }),
  })
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to create project')
  return data
}

export async function listProjects() {
  const res = await fetch(API_BASE)
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to list projects')
  return data
}

export async function getChat(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/chat`)
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to get chat')
  return data
}

export async function postChat(projectId, message) {
  const res = await fetch(`${API_BASE}/${projectId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message.trim() }),
  })
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to send message')
  return data
}

/**
 * Stream chat reply via SSE. Calls onChunk(chunk) for each chunk, onDone() when finished.
 * Returns the full accumulated reply.
 */
export async function postChatStream(projectId, message, { onChunk, onDone } = {}) {
  const res = await fetch(`${API_BASE}/${projectId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: message.trim() }),
  })
  if (!res.ok) {
    const data = await parseJson(res).catch(() => ({}))
    throw new Error(data.error || 'Failed to send message')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let fullReply = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.chunk) {
            fullReply += data.chunk
            onChunk?.(data.chunk)
          }
          if (data.done) onDone?.()
        } catch (_) {}
      }
    }
  }
  if (buffer.startsWith('data: ')) {
    try {
      const data = JSON.parse(buffer.slice(6))
      if (data.chunk) {
        fullReply += data.chunk
        onChunk?.(data.chunk)
      }
      if (data.done) onDone?.()
    } catch (_) {}
  }
  return fullReply
}

export async function triggerGeneration(projectId) {
  const url = `${API_BASE}/${projectId}/generate`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
  const data = await parseJson(res, url)
  if (!res.ok) throw new Error(data.error || 'Failed to trigger generation')
  return data
}

export async function getStatus(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/status`)
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to get status')
  return data
}

export function createEventSource(projectId, onMessage) {
  return new EventSource(`${API_BASE}/${projectId}/events`)
}

export async function listFiles(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/files`)
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to list files')
  return data
}

export async function getFile(projectId, filePath) {
  const res = await fetch(
    `${API_BASE}/${projectId}/file/${encodeURIComponent(filePath)}`
  )
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to get file')
  return data
}

export async function getPreviewUrl(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/preview-url`)
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to get preview')
  return data
}

/**
 * Fetch Stage 2 EngineeringPlan JSON for a project.
 * Returns the full plan object as produced by the backend.
 */
export async function getPlan(projectId) {
  const url = `${API_BASE}/${projectId}/plan`
  const res = await fetch(url)
  const data = await parseJson(res, url)
  if (!res.ok) throw new Error(data.error || 'Failed to get plan')
  return data
}
