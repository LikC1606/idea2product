<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.min.css'
import BentoGrid from './BentoGrid.vue'
import SkeletonChat from './SkeletonChat.vue'

const props = defineProps({
  messages: Array,
  sending: Boolean,
  typing: Boolean,
  showWelcome: Boolean,
  buildingStage: String,
  buildingVisible: Boolean,
  projectId: String,
  generating: Boolean,
})

const emit = defineEmits(['send', 'quick-send', 'generate'])

const canGenerate = computed(() => {
  if (!props.projectId || !props.messages?.length) return false
  return props.messages.some((m) => m.role === 'user')
})

const inputEl = ref(null)
const messagesEl = ref(null)

// 本轮澄清回答：{ [questionId]: Set<optionLabel> }
const clarificationAnswers = ref({})
// 选择「其它」时的自定义输入：{ [questionId]: string }
const clarificationOtherText = ref({})
const OTHER_OPTION_LABEL = '其它'

const QUICK_CHIPS = [
  { text: 'Build a todo list app with add, delete, and mark as done', label: 'Todo App' },
  { text: 'Build a blog with create, edit, delete posts and comments', label: 'Blog' },
  { text: 'Build a Markdown note-taking app with live preview', label: 'Notes App' },
  { text: 'Build a weather dashboard that shows forecasts', label: 'Weather' },
]

const FEATURE_ITEMS = [
  {
    id: 'pipeline',
    title: '4 阶段 Agent Pipeline',
    description: '从需求 → 规划 → 代码生成 → 验证，整条链路由专门 Agent 协同完成。',
    accent: 'Pipeline',
    sizeVariant: 'large',
  },
  {
    id: 'fullstack',
    title: '全栈代码一键生成',
    description: '自动产出 Flask 后端 + 前端模板 + BDD 测试，直接在浏览器内预览与调试。',
    accent: 'Full‑stack',
    sizeVariant: 'wide',
  },
  {
    id: 'validation',
    title: '验证 & 微调闭环',
    description: 'Full‑cycle Testing 与 Fine‑tuning 轮流运行，直到测试通过并认可产品效果。',
    accent: 'Validation',
    sizeVariant: 'small',
  },
  {
    id: 'multimodal',
    title: '多模态能力扩展',
    description: '按需接入图像、视频、PPT、PDF 等外部生成服务，形成一体化产品体验。',
    accent: 'Multimodal',
    sizeVariant: 'small',
  },
]

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
  const el = inputEl.value  // ref value = textarea DOM element
  const text = el?.value?.trim()
  if (!text || props.sending) return
  if (el) el.value = ''
  emit('send', text)
  nextTick(() => el?.focus())
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

import { watch, computed } from 'vue'

const showChatSkeleton = computed(() => {
  if (!props.generating) return false
  const len = props.messages?.length || 0
  return len > 0 && len <= 4
})

const hasClarificationSelection = computed(() => {
  const value = clarificationAnswers.value || {}
  return Object.values(value).some((set) => set instanceof Set && set.size > 0)
})

const lastMessage = computed(() => {
  const list = props.messages || []
  if (!list.length) return null
  return list[list.length - 1]
})

const isAssistantQuestion = computed(() => {
  const m = lastMessage.value
  if (!m || m.role !== 'assistant') return false
  const text = (m.content || '').trim()
  if (!text) return false
  return text.endsWith('?') || text.endsWith('？')
})

const shouldSuggestClarifications = computed(() => {
  if (!props.projectId) return false
  if (props.generating) return false
  if (!isAssistantQuestion.value) return false
  const hasUser = props.messages?.some((m) => m.role === 'user')
  return !!hasUser
})

const clarificationQuestions = computed(() => {
  if (!shouldSuggestClarifications.value) return []
  const m = lastMessage.value
  if (!m || m.role !== 'assistant') return []
  const qs = m?.clarification?.questions
  if (!Array.isArray(qs)) return []
  return qs
    .filter((q) => q && q.need_options !== false)
    .slice(0, 6)
})

function toggleMulti(q, optLabel) {
  const key = q.id || q.question
  const existing = clarificationAnswers.value[key]
  const set = existing instanceof Set ? existing : new Set()
  if (set.has(optLabel)) set.delete(optLabel)
  else set.add(optLabel)
  clarificationAnswers.value = { ...clarificationAnswers.value, [key]: set }
}

function toggleSingle(q, optLabel) {
  const key = q.id || q.question
  const set = new Set()
  set.add(optLabel)
  clarificationAnswers.value = { ...clarificationAnswers.value, [key]: set }
}

function setClarificationOther(questionKey, value) {
  clarificationOtherText.value = { ...clarificationOtherText.value, [questionKey]: value }
}

function submitClarifications() {
  const qs = clarificationQuestions.value || []
  const answers = clarificationAnswers.value || {}
  const otherTexts = clarificationOtherText.value || {}
  const lines = []
  for (const q of qs) {
    const key = q.id || q.question
    const set = answers[key]
    if (!(set instanceof Set) || set.size === 0) continue
    let labels = Array.from(set)
    if (labels.includes(OTHER_OPTION_LABEL)) {
      const custom = (otherTexts[key] || '').trim()
      labels = labels.filter((l) => l !== OTHER_OPTION_LABEL)
      if (custom) labels.push(custom)
      else labels.push(OTHER_OPTION_LABEL)
    }
    // Send answer-only to avoid "echoing" the question in the user's message bubble.
    lines.push(labels.join('、'))
  }
  if (!lines.length) return
  const text = lines.join('\n')
  emit('send', text)
  clarificationAnswers.value = {}
  clarificationOtherText.value = {}
}

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

watch(
  () => props.projectId,
  () => {
    clarificationAnswers.value = {}
    clarificationOtherText.value = {}
  }
)

watch(
  () =>
    (clarificationQuestions.value || [])
      .map((q) => q.id || q.question)
      .join('|'),
  () => {
    clarificationAnswers.value = {}
    clarificationOtherText.value = {}
  }
)
</script>

<template>
  <div class="panel-chat" role="region" aria-label="Chat">
    <div
      ref="messagesEl"
      class="chat-messages"
      role="log"
      aria-label="Chat messages"
    >
      <div v-if="showWelcome" class="welcome" v-reveal-on-scroll>
        <h2>What would you like to build?</h2>
        <p>Describe your app idea. Add details in the chat, then click Generate when ready.</p>
        <div class="quick-chips">
          <button
            v-for="(chip, i) in QUICK_CHIPS"
            :key="i"
            type="button"
            class="chip interactive-scale-sm"
            @click="quickSend(chip.text)"
          >
            {{ chip.label }}
          </button>
        </div>
        <BentoGrid :items="FEATURE_ITEMS" />
      </div>

      <template v-for="(m, i) in messages" :key="i">
        <div v-if="m.role === 'user'" class="msg user" v-reveal-on-scroll>
          {{ m.content }}
        </div>
        <div v-else-if="m.role === 'system'" class="msg system" v-reveal-on-scroll>
          {{ m.content }}
        </div>
        <div
          v-else
          class="msg assistant"
          v-reveal-on-scroll
          v-html="renderContent('assistant', m.content)"
        ></div>
      </template>

      <div v-if="!showWelcome && showChatSkeleton" class="chat-skeleton-wrapper">
        <SkeletonChat />
      </div>

      <div
        v-if="!showWelcome && shouldSuggestClarifications && clarificationQuestions.length > 0"
        class="clarify-panel"
        v-reveal-on-scroll
      >
        <div class="clarify-title">快速补充几个关键规格</div>
        <div class="clarify-questions">
          <div v-for="q in clarificationQuestions" :key="q.id || q.question" class="clarify-q">
            <div class="clarify-q-text">{{ q.question }}</div>
            <div class="clarify-options">
              <button
                v-for="opt in (q.options || []).slice(0, 6)"
                :key="opt.id || opt.label"
                type="button"
                class="clarify-chip interactive-scale-sm"
                :class="{
                  selected:
                    (clarificationAnswers[q.id || q.question] instanceof Set) &&
                    clarificationAnswers[q.id || q.question].has(opt.label),
                }"
                @click="
                  q.allow_multiple
                    ? toggleMulti(q, opt.label)
                    : toggleSingle(q, opt.label)
                "
              >
                {{ opt.label }}
              </button>
              <template v-if="q.allow_other !== false">
                <button
                  type="button"
                  class="clarify-chip clarify-chip-other interactive-scale-sm"
                  :class="{
                    selected:
                      (clarificationAnswers[q.id || q.question] instanceof Set) &&
                      clarificationAnswers[q.id || q.question].has(OTHER_OPTION_LABEL),
                  }"
                  @click="
                    q.allow_multiple
                      ? toggleMulti(q, OTHER_OPTION_LABEL)
                      : toggleSingle(q, OTHER_OPTION_LABEL)
                  "
                >
                  {{ OTHER_OPTION_LABEL }}
                </button>
                <input
                  v-if="
                    clarificationAnswers[q.id || q.question] instanceof Set &&
                    clarificationAnswers[q.id || q.question].has(OTHER_OPTION_LABEL)
                  "
                  type="text"
                  class="clarify-other-input"
                  placeholder="请输入你的想法…"
                  :value="clarificationOtherText[q.id || q.question] || ''"
                  @input="(e) => setClarificationOther(q.id || q.question, e.target.value)"
                />
              </template>
            </div>
          </div>
          <button
            type="button"
            class="clarify-continue interactive-scale-sm"
            :disabled="!hasClarificationSelection"
            @click="submitClarifications"
          >
            Continue
          </button>
        </div>
      </div>

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
        <span class="stage-dots">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </span>
      </div>
    </div>

    <div class="chat-input-area">
      <div class="input-row">
        <textarea
          ref="inputEl"
          placeholder="Describe the app you want to build..."
          rows="1"
          :disabled="sending"
          aria-label="Chat message input"
          @keydown="handleKeydown"
        ></textarea>
        <button
          type="button"
          class="send-btn interactive-scale"
          aria-label="Send message"
          :disabled="sending"
          @click="doSend"
        >
          <span class="send-icon">↑</span>
        </button>
      </div>
      <button
        v-if="canGenerate"
        type="button"
        class="generate-btn interactive-scale"
        :class="{ 'generating': generating }"
        :disabled="generating"
        aria-label="Generate app"
        @click="emit('generate')"
      >
        <span v-if="generating" class="btn-spinner"></span>
        {{ generating ? 'Generating...' : 'Generate' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.panel-chat {
  width: 420px;
  min-width: 320px;
  max-width: 100%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  background: var(--bg-panel);
}

@media (max-width: 1024px) {
  .panel-chat {
    width: 360px;
    min-width: 280px;
  }
}

@media (max-width: 768px) {
  .panel-chat {
    width: 100%;
    min-width: 0;
    max-height: 45vh;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-24);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.msg {
  max-width: 90%;
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  line-height: 1.6;
  font-size: 0.9rem;
  word-break: break-word;
  transition: opacity var(--transition-fast);
}

.msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%);
  color: white;
  box-shadow: var(--shadow-md);
  border-bottom-right-radius: 4px;
  white-space: pre-wrap;
}

.msg.assistant {
  align-self: flex-start;
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-bottom-left-radius: 4px;
  box-shadow: var(--shadow-sm);
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
  background: rgba(0, 0, 0, 0.35);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.84rem;
}

.msg.assistant :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
  border: 1px solid var(--border);
}

.msg.assistant :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.82rem;
}

.msg.system {
  align-self: center;
  background: var(--bg-surface);
  color: var(--text-muted);
  font-size: 0.8rem;
  padding: 8px 16px;
  border-radius: var(--radius-md);
}

.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-40);
  text-align: center;
}

.welcome h2 {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: var(--spacing-12);
  color: var(--text-primary);
}

.welcome p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-32);
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 320px;
}

.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-12);
  justify-content: center;
}

.chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.chip:hover {
  background: var(--bg-hover);
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.chip:active {
  transform: translateY(0);
}

.chip:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.building-banner {
  align-self: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(124, 58, 237, 0.08) 100%);
  border: 1px solid rgba(99, 102, 241, 0.25);
  color: var(--accent);
  padding: 10px 20px;
  border-radius: var(--radius-xl);
  font-size: 0.82rem;
  font-weight: 500;
  display: none;
  gap: 12px;
  align-items: center;
  box-shadow: 0 0 20px var(--accent-glow);
}

.building-banner.show {
  display: flex;
  animation: bannerPulse 2s ease-in-out infinite;
}

@keyframes bannerPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

.building-banner .spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(99, 102, 241, 0.3);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stage-dots {
  display: flex;
  gap: 4px;
  margin-left: 4px;
}

.stage-dots .dot {
  width: 4px;
  height: 4px;
  background: var(--accent);
  border-radius: 50%;
  opacity: 0.5;
  animation: dotPulse 1.2s ease-in-out infinite;
}

.stage-dots .dot:nth-child(2) { animation-delay: 0.15s; }
.stage-dots .dot:nth-child(3) { animation-delay: 0.3s; }
.stage-dots .dot:nth-child(4) { animation-delay: 0.45s; }

@keyframes dotPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 14px 18px;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  width: fit-content;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: bounce 0.6s infinite alternate;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  to { transform: translateY(-4px); opacity: 0.5; }
}

.chat-input-area {
  padding: var(--spacing-16) var(--spacing-24);
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
  background: var(--bg-elevated);
}

.clarify-panel {
  border: 1px solid rgba(99, 102, 241, 0.25);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(124, 58, 237, 0.06) 100%);
  border-radius: var(--radius-xl);
  padding: 14px 16px;
}

.clarify-title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  letter-spacing: 0.02em;
}

.clarify-sub {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.clarify-retry {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.45);
  background: rgba(99, 102, 241, 0.14);
  color: var(--accent);
  font-size: 0.78rem;
  cursor: pointer;
}

.clarify-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.clarify-q-text {
  font-size: 0.82rem;
  color: var(--text-primary);
  margin-bottom: 8px;
  line-height: 1.5;
}

.clarify-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.clarify-chip {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.6);
  color: var(--text-secondary);
  font-size: 0.78rem;
  cursor: pointer;
}

.clarify-chip:hover {
  border-color: rgba(99, 102, 241, 0.6);
  color: rgba(125, 211, 252, 1);
}

.clarify-chip.selected {
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.22);
  color: var(--accent);
}

.clarify-chip-other {
  border-style: dashed;
}

.clarify-other-input {
  min-width: 140px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.6);
  color: var(--text-primary);
  font-size: 0.78rem;
  outline: none;
}

.clarify-other-input:focus {
  border-color: rgba(99, 102, 241, 0.6);
}

.clarify-send {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.5);
  background: rgba(99, 102, 241, 0.18);
  color: var(--accent);
  font-size: 0.78rem;
  cursor: pointer;
}

.clarify-continue {
  margin-top: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  align-self: flex-start;
  opacity: 0.95;
}

.clarify-continue:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-row {
  display: flex;
  gap: var(--spacing-12);
}

.generate-btn {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%);
  color: white;
  border: none;
  align-self: flex-start;
  box-shadow: 0 2px 8px var(--accent-glow);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px var(--accent-glow);
}

.generate-btn:active:not(:disabled) {
  transform: translateY(0);
}

.generate-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.generate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.generate-btn.generating {
  pointer-events: none;
}

.generate-btn .btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-right: 8px;
  vertical-align: middle;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.chat-input-area textarea {
  flex: 1;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  padding: 14px 18px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: none;
  min-height: 48px;
  max-height: 140px;
  transition: all var(--transition-fast);
}

.chat-input-area textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-muted);
}

.chat-input-area textarea::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-fast);
  box-shadow: 0 2px 8px var(--accent-glow);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px var(--accent-glow);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-icon {
  font-size: 1.25rem;
  font-weight: 600;
}

@media (prefers-reduced-motion: reduce) {
  .chip,
  .building-banner,
  .generate-btn,
  .send-btn,
  .typing-indicator span,
  .stage-dots .dot {
    animation: none !important;
    transition: none;
  }
  .chip:hover {
    transform: none;
  }
  .generate-btn:hover:not(:disabled),
  .send-btn:hover:not(:disabled) {
    transform: none;
  }
  .building-banner.show {
    animation: none;
  }
}
</style>
