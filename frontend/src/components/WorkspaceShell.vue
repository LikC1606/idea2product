<script setup>
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import Header from './Header.vue'
import HistoryDrawer from './HistoryDrawer.vue'
import ChatPanel from './ChatPanel.vue'
import CodePanel from './CodePanel.vue'
import PreviewPanel from './PreviewPanel.vue'
import StatusBar from './StatusBar.vue'
import { useProject } from '../composables/useProject'
import { useChat } from '../composables/useChat'
import { useStatus } from '../composables/useStatus'
import * as api from '../api/projects'

const route = useRoute()

const {
  projectId,
  files,
  currentFile,
  fileContent,
  createProject,
  loadProject,
  loadFiles,
  loadFileContent,
  resetProject,
} = useProject()

const { messages, sending, typing, sendMessage, setMessages, clearMessages, appendSystemMessage } =
  useChat()

const { status, statusText, currentStage, setStatus, updateFromPayload, pollStatus, createEventSource } =
  useStatus()

const historyOpen = ref(false)
const historyProjects = ref([])
const activeTab = ref('code') // 'code' | 'preview'
const evtSource = ref(null)
const pollTimer = ref(null)
const backendConnected = ref(true)
let backendCheckInterval = null

const showWelcome = computed(() => messages.value.length === 0)
const buildingVisible = computed(() => status.value === 'processing')
const buildingStage = computed(() => currentStage.value)

const directionLabel = computed(() => {
  const key = route.query.direction
  if (!key) return ''
  const map = {
    code: '全栈代码生成',
    video: '视频生成',
    audio: '音频生成',
    slides: 'Slides 生成',
    pdf: 'PDF 报告生成',
  }
  return map[key] || ''
})

function stopPolling() {
  if (evtSource.value) {
    evtSource.value.close()
    evtSource.value = null
  }
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

function startPolling() {
  if (evtSource.value || pollTimer.value || !projectId.value) return
  if (typeof EventSource !== 'undefined') {
    evtSource.value = createEventSource((s) => handleStatusUpdate(s))
    evtSource.value.onerror = () => {
      stopPolling()
      startPollingFallback()
    }
  } else {
    startPollingFallback()
  }
}

function startPollingFallback() {
  if (pollTimer.value) return
  pollTimer.value = setInterval(pollStatus, 2500)
  pollStatus()
}

function handleStatusUpdate(payload) {
  updateFromPayload(payload)
  loadFiles()
  if (payload?.status === 'completed' || payload?.status === 'failed') {
    stopPolling()
  }
}

async function refreshHistory() {
  try {
    const data = await api.listProjects()
    historyProjects.value = data.projects || []
  } catch {
    historyProjects.value = []
  }
}

async function handleNewProject() {
  stopPolling()
  resetProject()
  clearMessages()
  setStatus('idle', 'Ready', '')
  await createProject()
  historyOpen.value = false
  refreshHistory()
}

async function handleLoadProject(pid) {
  stopPolling()
  const msgs = await loadProject(pid)
  setMessages(msgs)
  historyOpen.value = false
  refreshHistory()
  await loadFiles()
  await nextTick()
  await pollStatus()
  startPolling()
  const entryPoints = ['app.py', 'main.py', 'server.py', 'run.py', 'manage.py']
  const list = files.value
  const entry = list?.find((f) => entryPoints.includes(f.path.split('/').pop()))
  if (entry) loadFileContent(entry.path)
}

async function handleSend(text) {
  await sendMessage(text)
}

async function handleGenerate() {
  if (!projectId.value) return
  try {
    await api.triggerGeneration(projectId.value)
    startPolling()
  } catch (err) {
    appendSystemMessage(err.message || 'Failed to start generation')
  }
}

function handleQuickSend(text) {
  handleSend(text)
}

function handleSelectFile(path) {
  loadFileContent(path)
}

function switchTab(tab) {
  activeTab.value = tab
}

function handleKeydown(e) {
  if (e.key === 'Escape') historyOpen.value = false
}

async function checkBackendConnection() {
  const ok = await api.checkBackend()
  backendConnected.value = ok
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  checkBackendConnection()
  backendCheckInterval = setInterval(checkBackendConnection, 10000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (backendCheckInterval) clearInterval(backendCheckInterval)
  stopPolling()
})

watch(projectId, (pid) => {
  if (pid) refreshHistory()
})
</script>

<template>
  <div class="app">
    <div v-if="!backendConnected" class="backend-banner">
      后端服务未连接。请确保已启动: <code>python -m src.web.app</code>
    </div>
    <div class="app-header">
      <Header
        :project-id="projectId"
        :history-open="historyOpen"
        @toggle-history="historyOpen = !historyOpen"
        @new-project="handleNewProject"
      />
      <div v-if="directionLabel" class="direction-banner">
        <span class="direction-dot" />
        <span class="direction-label">当前方向：{{ directionLabel }}</span>
      </div>
    </div>
    <div class="main">
      <HistoryDrawer
        :open="historyOpen"
        :projects="historyProjects"
        :active-project-id="projectId"
        @select-project="handleLoadProject"
      />
      <ChatPanel
        :messages="messages"
        :sending="sending"
        :typing="typing"
        :show-welcome="showWelcome"
        :building-stage="buildingStage"
        :building-visible="buildingVisible"
        :project-id="projectId"
        :generating="status === 'processing'"
        @send="handleSend"
        @quick-send="handleQuickSend"
        @generate="handleGenerate"
      />
      <div class="panel-right">
        <div class="right-tabs">
          <button
            type="button"
            class="right-tab"
            :class="{ active: activeTab === 'code' }"
            @click="switchTab('code')"
          >
            Code
          </button>
          <button
            type="button"
            class="right-tab"
            :class="{ active: activeTab === 'preview' }"
            @click="switchTab('preview')"
          >
            Preview
          </button>
        </div>
        <div class="right-content">
          <Transition name="tab-fade" mode="out-in">
            <div v-if="activeTab === 'code'" key="code" class="tab-pane code-pane">
              <CodePanel
                :files="files"
                :current-file="currentFile"
                :file-content="fileContent"
                @select-file="handleSelectFile"
              />
            </div>
            <div v-else key="preview" class="tab-pane preview-pane">
              <PreviewPanel
                :project-id="projectId"
                :status="status"
                :visible="activeTab === 'preview'"
              />
            </div>
          </Transition>
        </div>
      </div>
    </div>
    <StatusBar
      :status="status"
      :status-text="statusText"
      :current-stage="currentStage"
    />
  </div>
</template>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  position: relative;
  z-index: var(--z-sticky, 20);
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.85);
}

.backend-banner {
  background: var(--error-bg, #3d1f1f);
  color: var(--error-fg, #f8b4b4);
  padding: var(--spacing-8) var(--spacing-16);
  font-size: 0.875rem;
  text-align: center;
}

.backend-banner code {
  background: rgba(0, 0, 0, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
}

.direction-banner {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px var(--spacing-24);
  font-size: 0.78rem;
  background: radial-gradient(circle at left, rgba(56, 189, 248, 0.18), transparent 70%),
    rgba(15, 23, 42, 0.92);
  color: var(--accent);
  border-bottom: 1px solid rgba(88, 101, 242, 0.3);
}

.direction-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: radial-gradient(circle, #22c55e, #16a34a);
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.9);
}

.direction-label {
  letter-spacing: 0.03em;
}

.main {
  display: flex;
  flex: 1;
  min-height: 0;
}

@media (max-width: 1024px) {
  .main {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .main {
    flex-direction: column;
  }
}

.panel-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-base);
  min-width: 0;
}

.right-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  height: 44px;
  background: var(--bg-elevated);
  padding: 0 var(--spacing-16);
}

.right-tab {
  padding: 0 24px;
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--text-muted);
  transition: all var(--transition-fast);
  margin-bottom: -1px;
}

.right-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.right-tab:hover:not(.active) {
  color: var(--text-secondary);
}

.right-tab:active {
  color: var(--text-primary);
}

.right-tab:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.right-content {
  flex: 1;
  overflow: hidden;
  display: flex;
}

.tab-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
}

.tab-fade-enter-active,
.tab-fade-leave-active {
  transition: opacity var(--transition-normal);
}

.tab-fade-enter-from,
.tab-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .right-tab {
    transition: none;
  }
  .tab-fade-enter-active,
  .tab-fade-leave-active {
    transition: none;
  }
}
</style>

