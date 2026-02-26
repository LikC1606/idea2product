<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.min.css'

const props = defineProps({
  messages: Array,
  sending: Boolean,
  typing: Boolean,
  showWelcome: Boolean,
  buildingStage: String,
  buildingVisible: Boolean,
})

const emit = defineEmits(['send', 'quick-send'])

const inputEl = ref(null)
const messagesEl = ref(null)

const QUICK_CHIPS = [
  'Build a todo list app with add, delete, and mark as done',
  'Build a blog with create, edit, delete posts and comments',
  'Build a Markdown note-taking app with live preview',
  'Build a weather dashboard that shows forecasts',
]

const chipLabels = ['Todo App', 'Blog', 'Notes App', 'Weather']

marked.setOptions({
  breaks: true,
  gfm: true,
  highlight(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch {}
    }
    return hljs.highlightAuto(code).value
  },
})

function renderContent(role, content) {
  if (role === 'assistant') {
    try {
      return marked.parse(content)
    } catch {
      return content
    }
  }
  return content
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    doSend()
  }
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
    e.preventDefault()
    doSend()
  }
}

function doSend() {
  const text = inputEl.value?.trim()
  if (!text || props.sending) return
  inputEl.value = ''
  emit('send', text)
  nextTick(() => inputEl.focus())
}

function quickSend(text) {
  emit('quick-send', text)
}

onMounted(() => {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight
    }
  })
})

// Scroll to bottom when messages change
import { watch } from 'vue'
watch(
  () => props.messages?.length,
  () => {
    nextTick(() => {
      if (messagesEl.value) {
        messagesEl.value.scrollTop = messagesEl.value.scrollHeight
      }
    })
  }
)
</script>

<template>
  <div class="panel-chat">
    <div ref="messagesEl" class="chat-messages">
      <div v-if="showWelcome" class="welcome">
        <h2>Idea2Product</h2>
        <p>
          Describe the app you want to build. The AI will generate it in the
          background.<br />Keep chatting to refine your requirements.
        </p>
        <div class="quick-chips">
          <button
            v-for="(chip, i) in QUICK_CHIPS"
            :key="i"
            type="button"
            class="chip"
            @click="quickSend(chip)"
          >
            {{ chipLabels[i] }}
          </button>
        </div>
      </div>

      <template v-for="(m, i) in messages" :key="i">
        <div v-if="m.role === 'user'" class="msg user">{{ m.content }}</div>
        <div v-else-if="m.role === 'system'" class="msg system">{{ m.content }}</div>
        <div
          v-else
          class="msg assistant"
          v-html="renderContent('assistant', m.content)"
        ></div>
      </template>

      <div
        v-if="typing"
        class="typing-indicator"
        role="status"
        aria-label="AI is typing"
      >
        <span></span><span></span><span></span>
      </div>

      <div
        class="building-banner"
        :class="{ show: buildingVisible }"
        role="status"
      >
        <span class="spinner"></span>
        <span>{{ buildingStage || 'Building...' }}</span>
      </div>
    </div>

    <div class="chat-input-area">
      <textarea
        ref="inputEl"
        placeholder="Describe the app you want..."
        rows="1"
        :disabled="sending"
        aria-label="Chat message input"
        @keydown="handleKeydown"
      ></textarea>
      <button
        type="button"
        class="send-btn"
        aria-label="Send message"
        :disabled="sending"
        @click="doSend"
      >
        &#x2191;
      </button>
    </div>
  </div>
</template>

<style scoped>
.panel-chat {
  width: 420px;
  min-width: 320px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  background: var(--bg-panel);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-16);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
}

.msg {
  max-width: 92%;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  line-height: 1.55;
  font-size: 0.9rem;
  word-break: break-word;
}

.msg.user {
  align-self: flex-end;
  background: var(--accent);
  color: var(--bg-secondary);
  border-bottom-right-radius: 2px;
  white-space: pre-wrap;
}

.msg.assistant {
  align-self: flex-start;
  background: var(--bg-surface);
  color: var(--text-primary);
  border-bottom-left-radius: 2px;
}

.msg.assistant :deep(p) {
  margin: 0 0 8px;
}

.msg.assistant :deep(p:last-child) {
  margin-bottom: 0;
}

.msg.assistant :deep(ul),
.msg.assistant :deep(ol) {
  margin: 4px 0 8px 18px;
}

.msg.assistant :deep(code) {
  background: rgba(0, 0, 0, 0.25);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.84rem;
}

.msg.assistant :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 6px 0;
}

.msg.assistant :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.82rem;
}

.msg.system {
  align-self: center;
  background: transparent;
  color: var(--text-muted);
  font-size: 0.8rem;
  text-align: center;
}

.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-32);
  text-align: center;
}

.welcome h2 {
  font-size: 1.4rem;
  margin-bottom: 8px;
  color: var(--accent);
}

.welcome p {
  color: var(--text-secondary);
  margin-bottom: 24px;
  font-size: 0.9rem;
  line-height: 1.5;
}

.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-8);
  justify-content: center;
}

.chip {
  padding: var(--spacing-8) 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.82rem;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.chip:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.building-banner {
  align-self: center;
  background: rgba(249, 226, 175, 0.08);
  border: 1px solid rgba(249, 226, 175, 0.2);
  color: var(--yellow);
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.78rem;
  display: none;
  gap: 6px;
  align-items: center;
}

.building-banner.show {
  display: flex;
}

.building-banner .spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(249, 226, 175, 0.3);
  border-top-color: var(--yellow);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 0.6s infinite alternate;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  to {
    transform: translateY(-5px);
    opacity: 0.4;
  }
}

.chat-input-area {
  padding: var(--spacing-12) var(--spacing-16);
  border-top: 1px solid var(--border);
  display: flex;
  gap: var(--spacing-8);
}

.chat-input-area textarea {
  flex: 1;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 12px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: none;
  min-height: 42px;
  max-height: 120px;
}

.chat-input-area textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.chat-input-area textarea::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: var(--bg-secondary);
  cursor: pointer;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.send-btn:hover {
  background: var(--accent-hover);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
