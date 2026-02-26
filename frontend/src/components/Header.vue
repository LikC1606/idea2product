<script setup>
defineProps({
  projectId: String,
  historyOpen: Boolean,
})
defineEmits(['toggle-history', 'new-project'])
</script>

<template>
  <header class="header" role="banner">
    <span class="logo">Idea2Product</span>
    <span class="project-id" :title="projectId || ''">{{ projectId || '' }}</span>
    <span class="spacer" aria-hidden="true"></span>
    <button
      class="history-btn"
      aria-label="Toggle project history"
      @click="$emit('toggle-history')"
    >
      History
    </button>
    <button
      class="new-btn"
      aria-label="Create new project"
      @click="$emit('new-project')"
    >
      + New
    </button>
  </header>
</template>

<style scoped>
.header {
  height: 48px;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-16);
  gap: var(--spacing-12);
}

.logo {
  font-weight: 700;
  font-size: 1rem;
  color: var(--accent);
}

.project-id {
  font-size: 0.75rem;
  color: var(--text-muted);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.spacer {
  flex: 1;
}

.history-btn,
.new-btn {
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  transition: all 0.15s;
}

.history-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.new-btn {
  background: var(--accent);
  color: var(--bg-secondary);
  border: none;
  font-weight: 600;
}

.new-btn:hover {
  background: var(--accent-hover);
}
</style>
