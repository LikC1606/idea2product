<script setup>
import { ref, watch, computed } from 'vue'
import EmptyState from './EmptyState.vue'
import ErrorBanner from './ErrorBanner.vue'
import * as api from '../api/projects'
import { useProject } from '../composables/useProject'
import { useStatus } from '../composables/useStatus'

const props = defineProps({
  projectId: String,
  status: String,
  visible: Boolean,
})

const { projectId: projectIdRef } = useProject()
const { status: statusRef } = useStatus()

const previewUrl = ref(null)
const lastKnownUrl = ref(null)
const errorMsg = ref(null)
const loading = ref(false)

const pid = computed(() => props.projectId || projectIdRef.value)
const statusVal = computed(() => props.status || statusRef.value)

async function refreshPreview() {
  if (!pid.value) return false
  loading.value = true
  errorMsg.value = null
  try {
    const data = await api.getPreviewUrl(pid.value)
    if (data.running && data.preview_url) {
      previewUrl.value = data.preview_url
      lastKnownUrl.value = data.preview_url
      return true
    }
    errorMsg.value = data.preview_error || null
    return false
  } catch {
    errorMsg.value = 'Failed to get preview'
    return false
  } finally {
    loading.value = false
  }
}

async function retryWithBackoff(maxRetries = 5, delayMs = 2000) {
  let attempt = 0
  const tryOnce = async () => {
    attempt++
    const ok = await refreshPreview()
    if (ok || attempt >= maxRetries) return
    setTimeout(tryOnce, delayMs)
  }
  await tryOnce()
}

function openExternal() {
  const url = previewUrl.value || lastKnownUrl.value
  if (url) window.open(url, '_blank')
}

const isCompleted = computed(
  () => statusVal.value === 'completed' || statusVal.value === 'failed'
)

watch(
  statusVal,
  (s) => {
    if (s === 'completed') retryWithBackoff()
  },
  { immediate: true }
)

watch(
  () => props.visible,
  (visible) => {
    if (visible && statusVal.value === 'completed' && pid.value) {
      refreshPreview()
    }
  }
)

watch(
  pid,
  (newPid, oldPid) => {
    if (!newPid || newPid !== oldPid) {
      previewUrl.value = null
      errorMsg.value = null
    }
  }
)
</script>

<template>
  <div class="preview-pane" role="region" aria-label="Live preview">
    <iframe
      v-if="previewUrl"
      :src="previewUrl"
      title="App preview"
      class="preview-iframe"
    ></iframe>
    <div v-else class="no-preview">
      <ErrorBanner
        v-if="errorMsg"
        :message="errorMsg"
        :retryable="true"
        @retry="retryWithBackoff"
      />
      <div v-else-if="statusVal === 'processing' || loading" class="preview-loading" role="status" aria-live="polite">
        <span class="loading-dots">
          <span></span><span></span><span></span>
        </span>
        Preview is starting...
      </div>
      <EmptyState
        v-else
        icon="🖥"
        title="Live preview"
        description="The app preview will appear here after generation completes. Click Generate to start."
      >
        <template #action>
          <div v-if="isCompleted || errorMsg" class="preview-actions">
            <button type="button" class="btn-retry" aria-label="Retry loading preview" @click="retryWithBackoff">Retry</button>
            <button
              v-if="lastKnownUrl"
              type="button"
              class="btn-external"
              aria-label="Open preview in new tab"
              @click="openExternal"
            >
              Open in new tab ↗
            </button>
          </div>
        </template>
      </EmptyState>
    </div>
  </div>
</template>

<style scoped>
.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-panel);
}

.preview-iframe {
  flex: 1;
  border: 1px solid var(--border);
  background: #fff;
  min-height: 0;
  border-radius: var(--radius-lg);
  margin: var(--spacing-12);
  box-shadow: var(--shadow-lg);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.preview-iframe:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-glow);
}

.no-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.95rem;
  gap: var(--spacing-24);
  min-height: 0;
  padding: var(--spacing-40);
}

.preview-error-msg {
  color: var(--red);
  font-size: 0.875rem;
  max-width: 360px;
  text-align: center;
  word-break: break-word;
}

.preview-loading {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}

.loading-dots span {
  width: 6px;
  height: 6px;
  background: var(--accent);
  border-radius: 50%;
  animation: loadBounce 0.6s ease-in-out infinite alternate;
}

.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes loadBounce {
  to { transform: translateY(-4px); opacity: 0.5; }
}

.no-preview-text {
  color: var(--text-secondary);
}

.preview-actions {
  display: flex;
  gap: var(--spacing-12);
  margin-top: var(--spacing-8);
}

.preview-actions button {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-retry {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

.btn-retry:hover {
  background: var(--bg-hover);
  border-color: var(--accent);
  color: var(--accent);
}

.btn-external {
  background: var(--accent);
  border: none;
  color: white;
}

.btn-external:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--accent-glow);
}
</style>
