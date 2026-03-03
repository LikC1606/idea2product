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
  background: radial-gradient(circle at top left, rgba(88, 101, 242, 0.16), transparent 55%),
    radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.12), transparent 55%),
    var(--bg-base);
  color: var(--text-primary);
}
</style>
