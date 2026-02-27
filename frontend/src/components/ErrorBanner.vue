<script setup>
defineProps({
  message: { type: String, default: '' },
  retryable: { type: Boolean, default: false },
})
defineEmits(['retry'])
</script>

<template>
  <div class="error-banner" role="alert">
    <span class="error-banner__icon" aria-hidden="true">⚠</span>
    <span class="error-banner__message">{{ message }}</span>
    <button
      v-if="retryable"
      type="button"
      class="error-banner__retry btn btn-secondary"
      aria-label="Retry"
      @click="$emit('retry')"
    >
      Retry
    </button>
  </div>
</template>

<style scoped>
.error-banner {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  padding: var(--spacing-12) var(--spacing-16);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: 0.875rem;
}

.error-banner__icon {
  flex-shrink: 0;
  font-size: 1.25rem;
}

.error-banner__message {
  flex: 1;
  word-break: break-word;
}

.error-banner__retry {
  flex-shrink: 0;
  padding: 6px 12px;
  font-size: 0.8rem;
}
</style>
