<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'rect', // rect | line | circle
  },
  width: {
    type: [String, Number],
    default: '100%',
  },
  height: {
    type: [String, Number],
    default: '1rem',
  },
  rounded: {
    type: Boolean,
    default: true,
  },
})

const style = computed(() => {
  const w = typeof props.width === 'number' ? `${props.width}px` : props.width
  const h = typeof props.height === 'number' ? `${props.height}px` : props.height
  return {
    width: w,
    height: h,
  }
})
</script>

<template>
  <div
    class="skeleton-block"
    :class="[
      `skeleton-block--${variant}`,
      { 'skeleton-block--rounded': rounded && variant !== 'circle' },
    ]"
    :style="style"
  />
</template>

<style scoped>
.skeleton-block {
  position: relative;
  overflow: hidden;
  background: rgba(148, 163, 184, 0.18);
}

.skeleton-block--rounded {
  border-radius: 999px;
}

.skeleton-block--rect {
  border-radius: 0.5rem;
}

.skeleton-block--line {
  border-radius: 999px;
}

.skeleton-block--circle {
  border-radius: 999px;
}

.skeleton-block::before {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    rgba(15, 23, 42, 0) 0%,
    rgba(148, 163, 184, 0.35) 50%,
    rgba(15, 23, 42, 0) 100%
  );
  animation: skeletonShimmer 1.4s ease-in-out infinite;
}

@keyframes skeletonShimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-block::before {
    animation: none;
    background: none;
  }
}
</style>

