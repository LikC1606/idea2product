import { ref, readonly } from 'vue'
import * as api from '../api/projects'
import { useProject } from './useProject'

export const messages = ref([])
export const sending = ref(false)
export const typing = ref(false)

export function useChat() {
  const { ensureProject } = useProject()

  const sendMessage = async (text) => {
    if (!text?.trim() || sending.value) return
    const msg = text.trim()
    messages.value.push({ role: 'user', content: msg })
    sending.value = true
    typing.value = true

    try {
      const pid = await ensureProject()
      try {
        const fullReply = await api.postChatStream(pid, msg, {
          onChunk: (chunk) => {
            const last = messages.value[messages.value.length - 1]
            if (last?.role === 'assistant') {
              last.content += chunk
            } else {
              messages.value.push({ role: 'assistant', content: chunk })
            }
          },
        })
        const last = messages.value[messages.value.length - 1]
        if (last?.role === 'assistant' && last.content !== fullReply) {
          last.content = fullReply
        } else if (last?.role !== 'assistant' && fullReply) {
          messages.value.push({ role: 'assistant', content: fullReply })
        }
      } catch (streamErr) {
        try {
          const data = await api.postChat(pid, msg)
          if (data.reply) {
            messages.value.push({ role: 'assistant', content: data.reply })
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
