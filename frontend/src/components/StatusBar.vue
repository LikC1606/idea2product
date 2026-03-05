<script setup>
defineProps({
  status: String,
  statusText: String,
  currentStage: String,
  statusError: String,
})
const emit = defineEmits(['retry'])
</script>

<template>
  <div class="status-bar" role="status" aria-live="polite">
    <div class="status-left">
      <span class="status-dot" :class="status || 'idle'"></span>
      <span class="status-text">{{ statusText || 'Ready' }}</span>
      <template v-if="status === 'failed' && statusError">
        <span class="status-error"> · {{ statusError }}</span>
        <button
          type="button"
          class="status-retry"
          @click="emit('retry')"
        >
          重试生成
        </button>
      </template>
    </div>
    <Transition name="stage-fade" mode="out-in">
      <span
        v-if="currentStage && status !== 'failed'"
        :key="currentStage"
        class="stage-indicator"
      >
        {{ currentStage }}
      </span>
    </Transition>
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

.status-error {
  color: var(--red, #f87171);
  font-size: 0.75rem;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-retry {
  margin-left: 8px;
  padding: 2px 10px;
  font-size: 0.75rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  cursor: pointer;
}

.status-retry:hover {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.stage-indicator {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-family: var(--font-mono);
}

.stage-fade-enter-active,
.stage-fade-leave-active {
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast);
}

.stage-fade-enter-from,
.stage-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.stage-fade-enter-to,
.stage-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (prefers-reduced-motion: reduce) {
  .status-dot.processing {
    animation: none;
  }
  .stage-fade-enter-active,
  .stage-fade-leave-active {
    transition: none;
  }
  .stage-fade-enter-from,
  .stage-fade-enter-to,
  .stage-fade-leave-from,
  .stage-fade-leave-to {
    transform: none;
  }
}
</style>
