<script setup>
import { ref, watch, computed, nextTick } from 'vue'
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
  <div class="code-pane">
    <div class="file-tree">
      <template v-if="!files?.length">
        <div class="file-item root-file placeholder">Waiting for generation...</div>
      </template>
      <template v-else>
        <div
          v-for="f in groupedFiles.rootFiles"
          :key="f.path"
          class="file-item root-file"
          :class="{
            active: f.path === currentFile,
            'entry-point': ENTRY_POINTS.has(f.path.split('/').pop()),
          }"
          :title="f.path"
          @click="emit('select-file', f.path)"
        >
          {{ f.path }}
        </div>
        <template v-for="dir in groupedFiles.sortedDirs" :key="dir">
          <div class="file-tree-dir">{{ dir }}/</div>
          <div
            v-for="f in groupedFiles.dirs[dir]"
            :key="f.path"
            class="file-item"
            :class="{
              active: f.path === currentFile,
              'entry-point': ENTRY_POINTS.has(f.path.split('/').pop()),
            }"
            :title="f.path"
            @click="emit('select-file', f.path)"
          >
            {{ f.path.split('/').pop() }}
          </div>
        </template>
      </template>
    </div>
    <div ref="codeEl" class="code-viewer">
      <template v-if="fileContent?.content != null">
        <pre><code :class="'language-' + (fileContent.language || guessLang(currentFile))">{{ fileContent.content }}</code></pre>
      </template>
      <div v-else class="placeholder">Select a file to view its code</div>
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
  width: 220px;
  overflow-y: auto;
  border-right: 1px solid var(--border);
  padding: 8px 0;
  background: var(--bg-panel);
  flex-shrink: 0;
}

.file-tree-dir {
  padding: 6px 12px;
  font-size: 0.78rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  cursor: default;
}

.file-item {
  padding: 5px 12px 5px 24px;
  font-size: 0.82rem;
  cursor: pointer;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-item.root-file {
  padding-left: 12px;
}

.file-item.placeholder {
  color: var(--text-muted);
  cursor: default;
}

.file-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.file-item.active {
  background: var(--bg-surface);
  color: var(--accent);
}

.file-item.entry-point {
  font-weight: 600;
}

.code-viewer {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.code-viewer pre {
  margin: 0;
  padding: var(--spacing-16);
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre;
  overflow-x: auto;
  background: transparent;
}

.code-viewer pre code {
  background: transparent;
}

.code-viewer .placeholder {
  color: var(--text-muted);
  text-align: center;
  margin-top: 80px;
  font-size: 0.9rem;
}
</style>
