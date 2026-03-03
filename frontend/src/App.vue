<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="app-root">
    <RouterView />
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

@media (prefers-reduced-motion: reduce) {
  .app-root::before {
    opacity: 0.2;
  }
}
</style>
