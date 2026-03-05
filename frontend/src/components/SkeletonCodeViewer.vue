<script setup>
import SkeletonBlock from './SkeletonBlock.vue'
</script>

<template>
  <div class="skeleton-code">
    <div class="skeleton-code__header">
      <SkeletonBlock variant="rect" width="64px" height="0.8rem" />
      <SkeletonBlock variant="rect" width="40%" height="0.8rem" />
    </div>
    <div class="skeleton-code__body">
      <SkeletonBlock
        v-for="i in 12"
        :key="i"
        variant="rect"
        height="0.85rem"
        :width="i % 4 === 0 ? '42%' : i % 3 === 0 ? '78%' : '92%'"
      />
    </div>
  </div>
</template>

<style scoped>
.skeleton-code {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.skeleton-code__header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
}

.skeleton-code__body {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>

