<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import EmptyState from './EmptyState.vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.min.css'

const props = defineProps({
  files: Array,
  currentFile: String,
  fileContent: Object,
})

const emit = defineEmits(['select-file'])

const codeEl = ref(null)
const ENTRY_POINTS = new Set(['app.py', 'main.py', 'server.py', 'run.py', 'manage.py'])

function guessLang(path) {
  const ext = path.split('.').pop()
  const map = {
    py: 'python',
    js: 'javascript',
    html: 'html',
    css: 'css',
    json: 'json',
    md: 'markdown',
    yml: 'yaml',
    yaml: 'yaml',
    sh: 'bash',
    sql: 'sql',
    txt: 'plaintext',
  }
  return map[ext] || 'plaintext'
}

const groupedFiles = computed(() => {
  const list = props.files || []
  const dirs = {}
  const rootFiles = []
  list.forEach((f) => {
    const parts = f.path.split('/')
    if (parts.length === 1) {
      rootFiles.push(f)
    } else {
      const dir = parts.slice(0, -1).join('/')
      if (!dirs[dir]) dirs[dir] = []
      dirs[dir].push(f)
    }
  })
  return { dirs, rootFiles, sortedDirs: Object.keys(dirs).sort() }
})

const currentLang = computed(() => {
  if (!props.currentFile || !props.fileContent) return ''
  return props.fileContent.language || guessLang(props.currentFile)
})

watch(
  () => [props.fileContent, props.currentFile],
  () => {
    nextTick(() => {
      if (codeEl.value) {
        codeEl.value.querySelectorAll('pre code').forEach((block) => {
          try {
            hljs.highlightElement(block)
          } catch {}
        })
      }
    })
  },
  { immediate: true }
)
</script>

<template>
  <div class="code-pane" role="region" aria-label="Code files">
    <nav class="file-tree" aria-label="File tree">
      <template v-if="!files?.length">
        <EmptyState
          icon="📂"
          title="No files yet"
          description="Files will appear here after you generate an app. Describe what you want to build in the chat, then click Generate."
        />
      </template>
      <template v-else>
        <button
          v-for="f in groupedFiles.rootFiles"
          :key="f.path"
          type="button"
          class="file-item root-file interactive-scale-sm"
          v-reveal-on-scroll
          :class="{
            active: f.path === currentFile,
            'entry-point': ENTRY_POINTS.has(f.path.split('/').pop()),
          }"
          :title="f.path"
          :aria-current="f.path === currentFile ? 'true' : undefined"
          @click="emit('select-file', f.path)"
        >
          {{ f.path }}
        </button>
        <template v-for="dir in groupedFiles.sortedDirs" :key="dir">
          <div class="file-tree-dir" v-reveal-on-scroll>{{ dir }}/</div>
          <button
            v-for="f in groupedFiles.dirs[dir]"
            :key="f.path"
            type="button"
            class="file-item interactive-scale-sm"
            v-reveal-on-scroll
            :class="{
              active: f.path === currentFile,
              'entry-point': ENTRY_POINTS.has(f.path.split('/').pop()),
            }"
            :title="f.path"
            :aria-current="f.path === currentFile ? 'true' : undefined"
            @click="emit('select-file', f.path)"
          >
            {{ f.path.split('/').pop() }}
          </button>
        </template>
      </template>
    </nav>
    <div ref="codeEl" class="code-viewer" role="region" aria-label="Code viewer">
      <template v-if="fileContent?.error">
        <EmptyState
          icon="⚠️"
          title="Cannot preview this file"
          :description="fileContent.error"
        />
      </template>
      <template v-else-if="fileContent?.content != null">
        <div class="code-header">
          <span class="lang-badge">{{ currentLang }}</span>
          <span class="file-name">{{ currentFile }}</span>
        </div>
        <pre><code :class="'language-' + currentLang">{{ fileContent.content }}</code></pre>
      </template>
      <EmptyState
        v-else
        icon="📄"
        title="Select a file"
        description="Choose a file from the tree to view its code."
      />
    </div>
  </div>
</template>

<style scoped>
.code-pane {
  display: flex;
  flex: 1;
  min-height: 0;
}

.file-tree {
  width: 240px;
  border-right: 1px solid var(--border);
  padding: var(--spacing-12) 0;
  background: var(--bg-elevated);
  flex-shrink: 0;
  max-height: calc(100vh - var(--shell-header-height) - var(--shell-status-height));
  overflow-y: auto;
}

.file-tree-dir {
  padding: 8px 16px;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  cursor: default;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px 10px 20px;
  font-size: 0.875rem;
  cursor: pointer;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all var(--transition-fast);
  border-left: 3px solid transparent;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
}

.file-item.root-file {
  padding-left: 16px;
}

.file-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.file-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.file-item.active {
  background: var(--accent-muted);
  color: var(--accent);
  border-left-color: var(--accent);
}

.file-item.entry-point {
  font-weight: 600;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: var(--spacing-32);
  color: var(--text-muted);
  font-size: 0.875rem;
}

.empty-icon {
  font-size: 2rem;
  opacity: 0.6;
}

.code-viewer {
  flex: 1;
  overflow: auto;
  padding: 0;
  background: var(--bg-panel);
}

.code-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border);
  font-size: 0.8rem;
}

.lang-badge {
  padding: 4px 10px;
  background: var(--accent-muted);
  color: var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 600;
  text-transform: uppercase;
}

.file-name {
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.code-viewer pre {
  margin: 0;
  padding: var(--spacing-24);
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--text-primary);
  white-space: pre;
  overflow-x: auto;
  background: transparent;
}

.code-viewer pre code {
  background: transparent;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.95rem;
  min-height: 200px;
}

@media (prefers-reduced-motion: reduce) {
  .file-item {
    transition: none;
  }
}
</style>
