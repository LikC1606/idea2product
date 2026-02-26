<script setup>
import { ref, watch, computed, nextTick, onMounted, onUnmounted } from 'vue'
import Header from './components/Header.vue'
import HistoryDrawer from './components/HistoryDrawer.vue'
import ChatPanel from './components/ChatPanel.vue'
import CodePanel from './components/CodePanel.vue'
import PreviewPanel from './components/PreviewPanel.vue'
import StatusBar from './components/StatusBar.vue'
import { useProject } from './composables/useProject'
import { useChat } from './composables/useChat'
import { useStatus } from './composables/useStatus'
import * as api from './api/projects'

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

const { messages, sending, typing, sendMessage, setMessages, clearMessages } =
  useChat()

const { status, statusText, currentStage, setStatus, updateFromPayload, pollStatus, createEventSource } =
  useStatus()

const historyOpen = ref(false)
const historyProjects = ref([])
const activeTab = ref('code') // 'code' | 'preview'
const evtSource = ref(null)
const pollTimer = ref(null)

const showWelcome = computed(() => messages.value.length === 0)
const buildingVisible = computed(() => status.value === 'processing')
const buildingStage = computed(() => currentStage.value)

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
  startPolling()
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

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  stopPolling()
})

watch(projectId, (pid) => {
  if (pid) refreshHistory()
})
</script>

<template>
  <div class="app">
    <Header
      :project-id="projectId"
      @toggle-history="historyOpen = !historyOpen"
      @new-project="handleNewProject"
    />
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
        @send="handleSend"
        @quick-send="handleQuickSend"
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
          <div v-show="activeTab === 'code'" class="tab-pane code-pane">
            <CodePanel
              :files="files"
              :current-file="currentFile"
              :file-content="fileContent"
              @select-file="handleSelectFile"
            />
          </div>
          <div v-show="activeTab === 'preview'" class="tab-pane preview-pane">
            <PreviewPanel
              :project-id="projectId"
              :status="status"
              :visible="activeTab === 'preview'"
            />
          </div>
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

.main {
  display: flex;
  flex: 1;
  min-height: 0;
}

.panel-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  min-width: 0;
}

.right-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  height: 40px;
}

.right-tab {
  padding: 0 20px;
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  cursor: pointer;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.right-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.right-tab:hover {
  color: var(--text-primary);
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
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
