<script setup>
import { computed } from 'vue'
import { useToast } from '../composables/useToast'

const { toasts, dismissToast } = useToast()

const orderedToasts = computed(() => toasts.value.slice().reverse())
</script>

<template>
  <div class="toast-host" aria-live="polite" aria-atomic="true">
    <transition-group name="toast" tag="div" class="toast-stack">
      <div
        v-for="toast in orderedToasts"
        :key="toast.id"
        class="toast"
        :class="{
          'toast--success': toast.type === 'success',
          'toast--error': toast.type === 'error',
        }"
        :role="toast.type === 'error' ? 'alert' : 'status'"
      >
        <div class="toast__content">
          <span class="toast__message">
            {{ toast.message }}
          </span>
        </div>
        <button
          type="button"
          class="toast__close"
          aria-label="Dismiss notification"
          @click="dismissToast(toast.id)"
        >
          ×
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 60;
}

.toast-stack {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: min(360px, 90vw);
}

.toast {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(15, 15, 15, 0.96);
  color: #f9fafb;
  border-radius: 999px;
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.4);
  font-size: 0.85rem;
}

.toast--success {
  border-color: rgba(34, 197, 94, 0.6);
}

.toast--error {
  border-color: rgba(248, 113, 113, 0.8);
}

.toast__content {
  flex: 1;
  min-width: 0;
}

.toast__message {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.toast__close {
  pointer-events: auto;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 0 2px;
  font-size: 1rem;
  line-height: 1;
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 160ms ease-out,
    transform 160ms ease-out;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate3d(0, 6px, 0);
}

@media (max-width: 640px) {
  .toast-stack {
    left: 50%;
    right: auto;
    transform: translateX(-50%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active {
    transition: none;
  }
  .toast-enter-from,
  .toast-leave-to {
    transform: none;
  }
}
</style>

