<script setup>
defineProps({
  status: String,
  statusText: String,
  currentStage: String,
})
</script>

<template>
  <div class="status-bar" role="status" aria-live="polite">
    <span>
      <span class="status-dot" :class="status || 'idle'"></span>
      {{ statusText || 'Ready' }}
    </span>
    <span v-if="currentStage" class="stage-indicator">{{ currentStage }}</span>
  </div>
</template>

<style scoped>
.status-bar {
  height: 28px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-16);
  font-size: 0.75rem;
  color: var(--text-muted);
  gap: 16px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.status-dot.idle {
  background: var(--text-muted);
}

.status-dot.processing {
  background: var(--yellow);
  animation: pulse 1s infinite;
}

.status-dot.completed {
  background: var(--green);
}

.status-dot.failed {
  background: var(--red);
}

.stage-indicator {
  color: var(--text-secondary);
  font-size: 0.72rem;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}
</style>
