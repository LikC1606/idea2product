<script setup>
defineProps({
  status: String,
  statusText: String,
  currentStage: String,
})
</script>

<template>
  <div class="status-bar" role="status" aria-live="polite">
    <div class="status-left">
      <span class="status-dot" :class="status || 'idle'"></span>
      <span class="status-text">{{ statusText || 'Ready' }}</span>
    </div>
    <span v-if="currentStage" class="stage-indicator">{{ currentStage }}</span>
  </div>
</template>

<style scoped>
.status-bar {
  height: 32px;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-24);
  font-size: 0.8rem;
  color: var(--text-muted);
}

.status-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.idle {
  background: var(--text-muted);
}

.status-dot.processing {
  background: var(--accent);
  animation: pulse 1.5s ease-in-out infinite;
  box-shadow: 0 0 8px var(--accent-glow);
}

.status-dot.completed {
  background: var(--green);
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.4);
}

.status-dot.failed {
  background: var(--red);
}

.status-text {
  color: var(--text-secondary);
  font-weight: 500;
}

.stage-indicator {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-family: var(--font-mono);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (prefers-reduced-motion: reduce) {
  .status-dot.processing {
    animation: none;
  }
}
</style>
