<script setup>
defineProps({
  projectId: String,
  historyOpen: { type: Boolean, default: false },
})
defineEmits(['toggle-history', 'new-project'])
</script>

<template>
  <header class="header" role="banner">
    <div class="logo-wrap">
      <span class="logo">Idea2Product</span>
      <span class="logo-badge">AI Build Studio</span>
    </div>
    <span class="project-id" :title="projectId || ''">{{ projectId || '' }}</span>
    <span class="spacer" aria-hidden="true"></span>
    <button
      class="history-btn interactive-scale-sm"
      type="button"
      aria-label="Toggle project history"
      :aria-expanded="historyOpen"
      @click="$emit('toggle-history')"
    >
      History
    </button>
    <button
      class="new-btn interactive-scale"
      type="button"
      aria-label="Create new project"
      @click="$emit('new-project')"
    >
      + New Project
    </button>
  </header>
</template>

<style scoped>
.header {
  height: 56px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-24);
  gap: var(--spacing-16);
  box-shadow: var(--shadow-sm);
}

.logo-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
}

.logo {
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-badge {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-muted);
  padding: 2px 8px;
  background: var(--accent-muted);
  border-radius: var(--radius-full);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.project-id {
  font-size: 0.75rem;
  color: var(--text-muted);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono);
}

.spacer {
  flex: 1;
}

.history-btn,
.new-btn {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  border: 1px solid var(--border);
}

.history-btn {
  background: var(--bg-surface);
  color: var(--text-secondary);
}

.history-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

.history-btn:active,
.new-btn:active {
  transform: none;
}

.history-btn:focus-visible,
.new-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.new-btn {
  background: var(--accent);
  color: white;
  border: none;
  box-shadow: 0 2px 8px var(--accent-glow);
}

.new-btn:hover {
  background: var(--accent-hover);
  box-shadow: 0 4px 16px var(--accent-glow);
  transform: translateY(-1px);
}

@media (prefers-reduced-motion: reduce) {
  .history-btn,
  .new-btn {
    transition: none;
  }
  .new-btn:hover {
    transform: none;
  }
}
</style>
