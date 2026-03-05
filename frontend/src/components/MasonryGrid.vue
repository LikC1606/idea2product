<script setup>
const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  minColumnWidth: {
    type: Number,
    default: 220,
  },
  gap: {
    type: Number,
    default: 16,
  },
})
</script>

<template>
  <div
    class="masonry-grid"
    :style="{
      columnWidth: props.minColumnWidth + 'px',
      columnGap: props.gap + 'px',
    }"
    aria-label="Masonry image gallery"
  >
    <article
      v-for="item in props.items"
      :key="item.id"
      class="masonry-item"
    >
      <figure class="masonry-item-inner">
        <img
          class="masonry-image"
          :src="item.src"
          :alt="item.alt || ''"
          loading="lazy"
        />
      </figure>
    </article>
  </div>
</template>

<style scoped>
.masonry-grid {
  width: 100%;
  max-width: 960px;
  margin: 24px auto 0;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: var(--masonry-gap, 16px);
}

.masonry-item-inner {
  position: relative;
  display: block;
  overflow: hidden;
  border-radius: 14px;
  background: radial-gradient(circle at top, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 1));
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.9);
}

.masonry-image {
  display: block;
  width: 100%;
  height: auto;
  object-fit: cover;
  transition: transform 0.22s ease-out, filter 0.22s ease-out;
}

.masonry-item-inner:hover .masonry-image {
  transform: scale(1.03) translateY(-1px);
  filter: saturate(1.1);
}

/* Responsive column behavior using column-width */
@media (max-width: 640px) {
  .masonry-grid {
    column-width: 180px !important;
  }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .masonry-grid {
    column-width: 220px !important;
  }
}

@media (min-width: 1025px) {
  .masonry-grid {
    column-width: 260px !important;
  }
}
</style>

