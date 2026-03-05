<script setup>
const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div class="bento-grid" aria-label="Idea2Product feature overview">
    <article
      v-for="item in props.items"
      :key="item.id"
      class="bento-card"
      :class="`bento-card--${item.sizeVariant || 'small'}`"
    >
      <header class="bento-card__header">
        <span v-if="item.accent" class="bento-card__accent">
          {{ item.accent }}
        </span>
        <h3 class="bento-card__title">
          {{ item.title }}
        </h3>
      </header>
      <p class="bento-card__description">
        {{ item.description }}
      </p>
    </article>
  </div>
</template>

<style scoped>
.bento-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--spacing-16, 16px);
  width: 100%;
  max-width: 720px;
  margin: 32px auto 0;
}

.bento-card {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px 18px;
  border-radius: 16px;
  background:
    radial-gradient(circle at top left, rgba(148, 163, 184, 0.26), transparent 55%),
    rgba(15, 23, 42, 0.96);
  border: 1px solid rgba(148, 163, 184, 0.22);
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.7);
  color: var(--text-primary);
  overflow: hidden;
  transition: transform var(--transition-fast, 0.16s ease-out),
    box-shadow var(--transition-fast, 0.16s ease-out),
    border-color var(--transition-fast, 0.16s ease-out),
    background var(--transition-fast, 0.16s ease-out);
}

.bento-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.bento-card__accent {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.12);
  color: rgba(125, 211, 252, 0.9);
  border: 1px solid rgba(56, 189, 248, 0.5);
  white-space: nowrap;
}

.bento-card__title {
  font-size: 0.98rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0;
  flex: 1;
  text-align: left;
}

.bento-card__description {
  margin: 4px 0 0;
  font-size: 0.84rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

.bento-card--large {
  grid-column: span 6;
  grid-row: span 3;
  min-height: 180px;
}

.bento-card--wide {
  grid-column: span 6;
  grid-row: span 2;
  min-height: 150px;
}

.bento-card--small {
  grid-column: span 3;
  grid-row: span 1;
  min-height: 120px;
}

.bento-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 22px 55px rgba(15, 23, 42, 0.9);
  border-color: rgba(129, 140, 248, 0.7);
}

@media (max-width: 1024px) {
  .bento-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    max-width: 640px;
  }

  .bento-card--large,
  .bento-card--wide {
    grid-column: span 6;
  }

  .bento-card--small {
    grid-column: span 3;
  }
}

@media (max-width: 768px) {
  .bento-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 24px;
  }

  .bento-card {
    grid-column: span 2;
    min-height: 110px;
  }
}
</style>

