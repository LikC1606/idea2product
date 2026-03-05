<script setup>
import EmptyState from './EmptyState.vue'

defineProps({
  open: Boolean,
  projects: Array,
  activeProjectId: String,
})
defineEmits(['select-project'])
</script>

<template>
  <aside
    class="history-drawer glass-panel"
    :class="{ open }"
    role="navigation"
    aria-label="Project history"
    :aria-hidden="!open"
  >
    <div class="history-drawer-inner">
      <div class="history-title">Projects</div>
      <EmptyState
        v-if="!projects?.length"
        icon="📋"
        title="No projects yet"
        description="Create a new project to get started."
      />
      <div v-else class="history-list">
        <button
          v-for="p in projects"
          :key="p.project_id"
          type="button"
          class="history-item"
          :aria-current="p.project_id === activeProjectId ? 'true' : undefined"
          :class="{
            active: p.project_id === activeProjectId,
            [p.status || 'idle']: true,
          }"
          :title="p.project_id"
          @click="$emit('select-project', p.project_id)"
        >
          <span class="status-badge" :class="p.status || 'idle'"></span>
          <span class="item-text">{{ (p.requirement || p.project_id || '').substring(0, 38) }}</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.history-drawer {
  width: 0;
  overflow: hidden;
  transition: width var(--transition-normal);
  flex-shrink: 0;
  will-change: width;
}

.history-drawer.open {
  width: 280px;
}

.history-drawer-inner {
  width: 280px;
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-16) 0;
}

.history-title {
  padding: var(--spacing-12) var(--spacing-16) var(--spacing-16);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.history-item {
  width: 100%;
  padding: 12px 20px;
  font-size: 0.875rem;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border: none;
  border-left: 3px solid transparent;
  background: none;
  text-align: left;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 var(--spacing-8);
  border-radius: var(--radius-md);
}

.history-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.history-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.history-item.active {
  border-left-color: var(--accent);
  color: var(--accent);
  background: var(--accent-muted);
}

.item-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 6px currentColor;
}

.status-badge.idle {
  background: var(--text-muted);
}

.status-badge.processing {
  background: var(--accent);
  animation: pulse 1.5s ease-in-out infinite;
}

.status-badge.completed {
  background: var(--green);
}

.status-badge.failed {
  background: var(--red);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (prefers-reduced-motion: reduce) {
  .history-drawer {
    transition: none;
  }
  .history-item {
    transition: none;
  }
  .status-badge.processing {
    animation: none;
  }
}
</style>
