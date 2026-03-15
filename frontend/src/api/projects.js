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

/** Backend health URL (same origin as API_BASE). */
function getHealthUrl() {
  return API_BASE.replace(/\/api\/projects\/?$/, '') + '/api/health'
}

/**
 * Check if backend is reachable. Uses GET /api/health when possible.
 * Returns { ok: true } when healthy, { ok: false } when unreachable, { ok: true, degraded: true } when 503.
 */
export async function checkBackend() {
  try {
    const url = getHealthUrl()
    const res = await fetch(url, { method: 'GET' })
    const ct = res.headers.get('content-type') || ''
    if (!ct.includes('application/json')) return { ok: false }
    const data = await res.json()
    if (res.status === 503) return { ok: true, degraded: true, checks: data.checks }
    return { ok: res.ok && data.status !== 'degraded', degraded: data.status === 'degraded', checks: data.checks }
  } catch {
    try {
      const res = await fetch(API_BASE, { method: 'GET' })
      if (res.ok) return { ok: true }
    } catch {}
    return { ok: false }
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

export async function postChat(projectId, message, { clientMessageId } = {}) {
  const payload = { message: message.trim() }
  if (clientMessageId) payload.client_message_id = clientMessageId
  const res = await fetch(`${API_BASE}/${projectId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to send message')
  return {
    reply: data.reply || '',
    clarification: data.clarification || null,
  }
}

/**
 * Stream chat reply via SSE. Calls onChunk(chunk) for each chunk, onDone() when finished.
 * Returns the full accumulated reply.
 */
export async function postChatStream(projectId, message, { onChunk, onDone, clientMessageId } = {}) {
  const payload = { message: message.trim() }
  if (clientMessageId) payload.client_message_id = clientMessageId
  const res = await fetch(`${API_BASE}/${projectId}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const data = await parseJson(res).catch(() => ({}))
    throw new Error(data.error || 'Failed to send message')
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let fullReply = ''
  let donePayload = null
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
          if (data.done) {
            donePayload = data
            onDone?.(data)
          }
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
      if (data.done) {
        donePayload = data
        onDone?.(data)
      }
    } catch (_) {}
  }
  return {
    reply: fullReply,
    clarification: donePayload?.clarification || null,
  }
}

export async function triggerGeneration(projectId, body = {}) {
  const url = `${API_BASE}/${projectId}/generate`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await parseJson(res, url)
  if (res.status === 429) {
    return { status: data.status || 'rejected_backpressure', ...data }
  }
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

export async function getClarificationQuestions(projectId) {
  const url = `${API_BASE}/${projectId}/clarification-questions`
  // This endpoint is LLM-backed and can be slow; add a UI-friendly timeout.
  const controller = new AbortController()
  const t = setTimeout(() => controller.abort(), 25000)
  let res
  try {
    res = await fetch(url, { signal: controller.signal })
  } catch (e) {
    if (e?.name === 'AbortError') {
      throw new Error('生成选项超时（25s）。请重试，或检查 LLM 配置/网络/额度。')
    }
    throw e
  } finally {
    clearTimeout(t)
  }
  const data = await parseJson(res, url)
  if (!res.ok) throw new Error(data.error || 'Failed to load clarification questions')
  return data
}

/**
 * Delete a project. Backend: DELETE /api/projects/<id>.
 * Throws on 404 (not found) or 409 (generation in progress; cancel or wait first).
 */
export async function deleteProject(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}`, { method: 'DELETE' })
  const data = await parseJson(res)
  if (res.status === 409) throw new Error(data.error || 'Cannot delete while generation is running')
  if (!res.ok) throw new Error(data.error || 'Failed to delete project')
  return data
}

/** Request cancellation of the current generation. Backend: POST /api/projects/<id>/cancel. */
export async function cancelGeneration(projectId) {
  const res = await fetch(`${API_BASE}/${projectId}/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  })
  const data = await parseJson(res)
  if (!res.ok) throw new Error(data.error || 'Failed to cancel')
  return data
}
