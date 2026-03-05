<script setup>
defineProps({
  icon: { type: String, default: '📂' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
defineEmits(['action'])
</script>

<template>
  <div class="empty-state" v-reveal-on-scroll>
    <span class="empty-state__icon" aria-hidden="true">{{ icon }}</span>
    <h3 v-if="title" class="empty-state__title">{{ title }}</h3>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>
    <slot name="action"></slot>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-40);
  text-align: center;
  color: var(--text-muted);
}

.empty-state__icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-16);
  opacity: 0.6;
  line-height: 1;
}

.empty-state__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 var(--spacing-8);
}

.empty-state__desc {
  font-size: 0.9rem;
  max-width: 320px;
  line-height: 1.5;
  margin: 0 0 var(--spacing-24);
}
</style>
