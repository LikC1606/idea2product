<script setup>
defineProps({
  open: Boolean,
  projects: Array,
  activeProjectId: String,
})
defineEmits(['select-project'])
</script>

<template>
  <aside
    class="history-drawer"
    :class="{ open }"
    role="navigation"
    aria-label="Project history"
  >
    <div class="history-drawer-inner">
      <div class="history-title">Projects</div>
      <div class="history-list">
        <button
          v-for="p in projects"
          :key="p.project_id"
          type="button"
          class="history-item"
          :class="{
            active: p.project_id === activeProjectId,
            [p.status || 'idle']: true,
          }"
          :title="p.project_id"
          @click="$emit('select-project', p.project_id)"
        >
          <span class="status-badge" :class="p.status || 'idle'"></span>
          {{ p.requirement ? p.requirement.substring(0, 40) : p.project_id }}
        </button>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.history-drawer {
  width: 0;
  overflow: hidden;
  background: var(--bg-panel);
  border-right: 1px solid var(--border);
  transition: width 0.2s ease;
  flex-shrink: 0;
}

.history-drawer.open {
  width: 260px;
}

.history-drawer-inner {
  width: 260px;
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-12) 0;
}

.history-title {
  padding: 4px var(--spacing-16) var(--spacing-12);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-item {
  width: 100%;
  padding: var(--spacing-8) var(--spacing-16);
  font-size: 0.82rem;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border: none;
  border-left: 3px solid transparent;
  background: none;
  text-align: left;
  transition: all 0.15s;
}

.history-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.history-item.active {
  border-left-color: var(--accent);
  color: var(--accent);
  background: var(--bg-surface);
}

.status-badge {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.status-badge.idle {
  background: var(--text-muted);
}

.status-badge.processing {
  background: var(--yellow);
}

.status-badge.completed {
  background: var(--green);
}

.status-badge.failed {
  background: var(--red);
}
</style>
