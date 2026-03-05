import { ref, readonly } from 'vue'
import * as api from '../api/projects'
import { useProject } from './useProject'

export const status = ref('idle') // idle | processing | completed | failed
export const statusText = ref('Ready')
export const currentStage = ref('')
export const progress = ref(0)
export const statusError = ref('') // error message when status === 'failed'

function statusLabel(s, p) {
  if (s === 'processing') return `Generating... ${p || 0}%`
  if (s === 'completed') return 'Done'
  if (s === 'failed') return 'Failed'
  return 'Ready'
}

export function useStatus() {
  const { projectId } = useProject()

  const setStatus = (s, text, stage, prog = 0) => {
    status.value = s || 'idle'
    statusText.value = text || statusLabel(s, prog)
    currentStage.value = stage || ''
    progress.value = prog || 0
    if (s !== 'failed') statusError.value = ''
  }

  const updateFromPayload = (payload) => {
    const s = payload.status || 'idle'
    const stage = payload.current_stage || ''
    const prog = payload.progress ?? 0
    statusError.value = (s === 'failed' && payload.error) ? String(payload.error) : ''
    setStatus(s, statusLabel(s, prog), stage, prog)
  }

  const pollStatus = async () => {
    if (!projectId.value) return
    try {
      const s = await api.getStatus(projectId.value)
      updateFromPayload(s)
      return s
    } catch {
      return null
    }
  }

  const createEventSource = (onUpdate) => {
    if (!projectId.value) return null
    const evtSource = api.createEventSource(projectId.value, null)
    evtSource.onmessage = (event) => {
      try {
        const s = JSON.parse(event.data)
        onUpdate?.(s)
      } catch {}
    }
    return evtSource
  }

  return {
    status: readonly(status),
    statusText: readonly(statusText),
    currentStage: readonly(currentStage),
    progress: readonly(progress),
    statusError: readonly(statusError),
    setStatus,
    updateFromPayload,
    pollStatus,
    createEventSource,
  }
}
