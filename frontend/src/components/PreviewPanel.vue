<script setup>
import { ref, watch, computed } from 'vue'
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
  <div class="preview-pane">
    <iframe
      v-if="previewUrl"
      :src="previewUrl"
      title="App preview"
      class="preview-iframe"
    ></iframe>
    <div v-else class="no-preview">
      <span v-if="errorMsg" class="preview-error-msg">{{ errorMsg }}</span>
      <span v-else-if="statusVal === 'processing' || loading" class="preview-loading">
        Preview is starting...
      </span>
      <span v-else class="no-preview-text">
        Live preview will appear here after generation
      </span>
      <div v-if="isCompleted || errorMsg" class="preview-actions">
        <button type="button" @click="retryWithBackoff">Retry</button>
        <button
          v-if="lastKnownUrl"
          type="button"
          @click="openExternal"
        >
          Open in new tab
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.preview-iframe {
  flex: 1;
  border: none;
  background: #fff;
  min-height: 0;
}

.no-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.9rem;
  gap: var(--spacing-12);
  min-height: 0;
}

.preview-error-msg {
  color: var(--red);
  font-size: 0.82rem;
  max-width: 400px;
  text-align: center;
  word-break: break-word;
}

.preview-actions {
  display: flex;
  gap: var(--spacing-8);
}

.preview-actions button {
  padding: 6px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.82rem;
  transition: all 0.15s;
}

.preview-actions button:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
