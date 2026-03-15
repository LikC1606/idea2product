import { ref, readonly } from 'vue'
import * as api from '../api/projects'
import { useProject } from './useProject'

export const messages = ref([])
export const sending = ref(false)
export const typing = ref(false)

function makeClientMessageId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

export function useChat() {
  const { ensureProject } = useProject()

  const sendMessage = async (text) => {
    if (!text?.trim() || sending.value) return
    const msg = text.trim()
    const clientMessageId = makeClientMessageId()
    messages.value.push({ role: 'user', content: msg })
    sending.value = true
    typing.value = true

    try {
      const pid = await ensureProject()
      try {
        const res = await api.postChatStream(pid, msg, {
          clientMessageId,
          onChunk: (chunk) => {
            const last = messages.value[messages.value.length - 1]
            if (last?.role === 'assistant') {
              last.content += chunk
            } else {
              messages.value.push({ role: 'assistant', content: chunk })
            }
          },
        })
        const fullReply = res?.reply || ''
        const last = messages.value[messages.value.length - 1]
        if (last?.role === 'assistant') {
          if (last.content !== fullReply) last.content = fullReply
          if (res?.clarification) last.clarification = res.clarification
        } else if (fullReply) {
          messages.value.push({
            role: 'assistant',
            content: fullReply,
            ...(res?.clarification ? { clarification: res.clarification } : {}),
          })
        }
      } catch (streamErr) {
        try {
          const res = await api.postChat(pid, msg, { clientMessageId })
          const reply = res?.reply || ''
          if (reply) {
            const last = messages.value[messages.value.length - 1]
            if (last?.role === 'assistant') {
              last.content = reply
              if (res?.clarification) last.clarification = res.clarification
            } else {
              messages.value.push({
                role: 'assistant',
                content: reply,
                ...(res?.clarification ? { clarification: res.clarification } : {}),
              })
            }
          } else throw streamErr
        } catch {
          throw streamErr
        }
      }
    } catch (err) {
      messages.value.push({
        role: 'system',
        content: 'Send failed: ' + (err.message || 'Unknown error'),
      })
    } finally {
      sending.value = false
      typing.value = false
    }
  }

  const setMessages = (msgs) => {
    messages.value = msgs || []
  }

  const clearMessages = () => {
    messages.value = []
  }

  const appendAssistantMessage = (content) => {
    messages.value.push({ role: 'assistant', content })
  }

  const appendSystemMessage = (content) => {
    messages.value.push({ role: 'system', content })
  }

  return {
    messages: readonly(messages),
    sending: readonly(sending),
    typing: readonly(typing),
    sendMessage,
    setMessages,
    clearMessages,
    appendAssistantMessage,
    appendSystemMessage,
  }
}
