<script setup>
import SkeletonBlock from './SkeletonBlock.vue'
</script>

<template>
  <div class="skeleton-preview" aria-hidden="true">
    <div class="skeleton-preview__chrome">
      <div class="skeleton-preview__dots">
        <SkeletonBlock variant="circle" width="10px" height="10px" />
        <SkeletonBlock variant="circle" width="10px" height="10px" />
        <SkeletonBlock variant="circle" width="10px" height="10px" />
      </div>
      <SkeletonBlock variant="rect" width="40%" height="0.8rem" />
    </div>
    <div class="skeleton-preview__hero">
      <SkeletonBlock variant="rect" width="55%" height="1.1rem" />
      <SkeletonBlock variant="rect" width="36%" height="0.9rem" />
    </div>
    <div class="skeleton-preview__content">
      <div class="skeleton-preview__sidebar">
        <SkeletonBlock
          v-for="i in 5"
          :key="`nav-${i}`"
          variant="rect"
          height="0.8rem"
          width="80%"
        />
      </div>
      <div class="skeleton-preview__main">
        <SkeletonBlock
          v-for="i in 6"
          :key="`row-${i}`"
          variant="rect"
          height="0.9rem"
          :width="i % 3 === 0 ? '56%' : '92%'"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-preview {
  width: 100%;
  max-width: 720px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: radial-gradient(circle at top, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.98));
  padding: 14px 16px 18px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-preview__chrome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.skeleton-preview__dots {
  display: flex;
  align-items: center;
  gap: 6px;
}

.skeleton-preview__hero {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-preview__content {
  display: grid;
  grid-template-columns: 1fr 2.2fr;
  gap: 18px;
  margin-top: 4px;
}

.skeleton-preview__sidebar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-preview__main {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

@media (max-width: 768px) {
  .skeleton-preview {
    max-width: 100%;
    padding: 12px 12px 16px;
  }
  .skeleton-preview__content {
    grid-template-columns: 1fr;
  }
}
</style>

