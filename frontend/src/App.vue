<script setup>
import { RouterView } from 'vue-router'
import ToastHost from './components/ToastHost.vue'
</script>

<template>
  <div class="app-root">
    <Transition name="page-transition" mode="out-in">
      <RouterView />
    </Transition>
    <ToastHost />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  position: relative;
  background:
    radial-gradient(circle at top left, rgba(88, 101, 242, 0.22), transparent 55%),
    radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.18), transparent 55%),
    var(--bg-base);
  color: var(--text-primary);
}

.app-root::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 120px 120px;
  opacity: 0.35;
  mix-blend-mode: soft-light;
}

.app-root::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 10% 0%, rgba(79, 70, 229, 0.55), transparent 60%),
    radial-gradient(circle at 80% 20%, rgba(124, 58, 237, 0.5), transparent 55%),
    radial-gradient(circle at 20% 80%, rgba(56, 189, 248, 0.4), transparent 60%);
  opacity: var(--aurora-opacity);
  mix-blend-mode: screen;
  animation: auroraShift var(--aurora-animation-duration) ease-in-out infinite alternate;
}

@keyframes auroraShift {
  0% {
    transform: translate3d(0, 0, 0) scale(1.05);
    filter: hue-rotate(0deg);
  }
  50% {
    transform: translate3d(-3%, -2%, 0) scale(1.08);
    filter: hue-rotate(10deg);
  }
  100% {
    transform: translate3d(3%, 2%, 0) scale(1.12);
    filter: hue-rotate(-8deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-root::before {
    opacity: 0.2;
  }
  .app-root::after {
    animation: none;
    opacity: calc(var(--aurora-opacity) * 0.6);
  }
}
</style>
