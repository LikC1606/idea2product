<script setup>
import SkeletonBlock from './SkeletonBlock.vue'
</script>

<template>
  <div class="skeleton-chat">
    <div class="skeleton-chat__item skeleton-chat__item--assistant">
      <SkeletonBlock variant="rect" width="72%" height="0.9rem" />
      <SkeletonBlock variant="rect" width="58%" height="0.9rem" />
    </div>
    <div class="skeleton-chat__item skeleton-chat__item--user">
      <SkeletonBlock variant="rect" width="64%" height="0.9rem" />
    </div>
    <div class="skeleton-chat__item skeleton-chat__item--assistant">
      <SkeletonBlock variant="rect" width="80%" height="0.9rem" />
      <SkeletonBlock variant="rect" width="46%" height="0.9rem" />
    </div>
    <div class="skeleton-chat__item skeleton-chat__item--user">
      <SkeletonBlock variant="rect" width="52%" height="0.9rem" />
    </div>
  </div>
</template>

<style scoped>
.skeleton-chat {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 4px;
}

.skeleton-chat__item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 80%;
}

.skeleton-chat__item--assistant {
  align-self: flex-start;
}

.skeleton-chat__item--user {
  align-self: flex-end;
}
</style>

