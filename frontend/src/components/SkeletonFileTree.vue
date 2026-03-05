<script setup>
import SkeletonBlock from './SkeletonBlock.vue'
</script>

<template>
  <div class="skeleton-tree" aria-hidden="true">
    <div class="skeleton-tree__section">
      <SkeletonBlock variant="line" width="48%" height="0.75rem" />
    </div>
    <div class="skeleton-tree__items">
      <SkeletonBlock
        v-for="i in 6"
        :key="`root-${i}`"
        variant="line"
        height="0.8rem"
        :width="`${70 + (i % 3) * 6}%`"
      />
    </div>
    <div class="skeleton-tree__section">
      <SkeletonBlock variant="line" width="40%" height="0.75rem" />
    </div>
    <div class="skeleton-tree__items skeleton-tree__items--nested">
      <SkeletonBlock
        v-for="i in 5"
        :key="`nested-${i}`"
        variant="line"
        height="0.8rem"
        :width="`${60 + (i % 3) * 8}%`"
      />
    </div>
  </div>
</template>

<style scoped>
.skeleton-tree {
  padding: 8px 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skeleton-tree__section {
  margin-top: 4px;
}

.skeleton-tree__items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-tree__items--nested {
  padding-left: 10px;
}
</style>

