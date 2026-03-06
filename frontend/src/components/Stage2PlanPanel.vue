<script setup>
import { ref, computed, watch } from 'vue'
import * as api from '../api/projects'

const props = defineProps({
  projectId: {
    type: String,
    default: '',
  },
  status: {
    type: String,
    default: '',
  },
  active: {
    type: Boolean,
    default: false,
  },
})

const loading = ref(false)
const errorMsg = ref('')
const plan = ref(null)

const hasPlan = computed(() => !!plan.value)

const metaStats = computed(() => {
  if (!plan.value) {
    return {
      taskCount: 0,
      fileCount: 0,
      dependencyCount: 0,
      bddCount: 0,
    }
  }
  return {
    taskCount: plan.value.tasks?.length || 0,
    fileCount: plan.value.file_structure?.length || 0,
    dependencyCount: plan.value.dependencies?.length || 0,
    bddCount: plan.value.bdd_test_cases?.length || 0,
  }
})

const groupedTasks = computed(() => {
  if (!plan.value?.tasks?.length) return []
  const groups = {}
  for (const t of plan.value.tasks) {
    const key = t.type || 'other'
    if (!groups[key]) groups[key] = []
    groups[key].push(t)
  }
  const labelMap = {
    frontend: '前端 / 交互',
    backend: '后端 / API',
    testing: '测试与质量',
    deployment: '部署与环境',
    database: '数据与存储',
    other: '其他任务',
  }
  return Object.entries(groups).map(([type, tasks]) => ({
    type,
    label: labelMap[type] || type,
    tasks: tasks.sort((a, b) => (a.priority || 0) - (b.priority || 0)),
  }))
})

const algorithmHighlights = computed(() => {
  if (!plan.value?.algorithms) return []
  const entries = Object.values(plan.value.algorithms)
  return entries.slice(0, 6)
})

const fileTiles = computed(() => {
  if (!plan.value?.file_structure?.length) return []
  const files = plan.value.file_structure.slice(0, 12)
  return files.map((file, index) => {
    let size = 'small'
    if (index === 0) size = 'hero'
    else if (index % 5 === 0) size = 'tall'
    else if (index % 3 === 0) size = 'wide'
    return {
      ...file,
      size,
    }
  })
})

const imageSpecs = computed(() => plan.value?.image_specs || [])

async function loadPlan() {
  if (!props.projectId || loading.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    const data = await api.getPlan(props.projectId)
    plan.value = data.plan || data
  } catch (err) {
    errorMsg.value = err.message || 'Failed to load planning story'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.projectId,
  (pid) => {
    if (!pid) {
      plan.value = null
      errorMsg.value = ''
      return
    }
    if (props.active) {
      loadPlan()
    }
  }
)

watch(
  () => props.active,
  (isActive) => {
    if (!isActive) return
    if (!props.projectId) return
    if (!hasPlan.value && !loading.value) {
      loadPlan()
    }
  },
  { immediate: true }
)

watch(
  () => props.status,
  (s) => {
    if (!props.projectId) return
    if (s === 'processing') return
    if (!props.active) return
    if (s === 'completed' || s === 'failed') {
      // Refresh when generation finishes so the story stays in sync.
      loadPlan()
    }
  }
)
</script>

<template>
  <div class="plan-shell" role="region" aria-label="Stage 2 planning">
    <div v-if="!projectId" class="plan-empty">
      <h2 class="plan-empty-title">Planning spreads will appear here</h2>
      <p class="plan-empty-desc">
        Start a project in the chat, describe what you want to build, then run generation.
        Stage&nbsp;2 will craft an engineering plan that is presented in this magazine-style layout.
      </p>
    </div>

    <div v-else-if="loading && !hasPlan" class="plan-loading">
      <span class="plan-loading-dots">
        <span></span><span></span><span></span>
      </span>
      正在整理 Stage 2 规划故事…
    </div>

    <div v-else-if="errorMsg && !hasPlan" class="plan-error">
      <p class="plan-error-title">暂时无法获取规划结果</p>
      <p class="plan-error-body">
        {{ errorMsg }}
      </p>
      <button type="button" class="plan-error-btn interactive-scale-sm" @click="loadPlan">
        重试加载规划
      </button>
    </div>

    <div v-else-if="hasPlan" class="plan-layout">
      <!-- Editorial spine -->
      <div class="plan-spine" aria-hidden="true"></div>

      <!-- Spread 1: FlowSimulation / Overview -->
      <section class="spread spread-overview" v-reveal-on-scroll>
        <header class="spread-header">
          <div class="spread-kicker">Stage 2 · Planning</div>
          <h2 class="spread-title">FlowSimulation · 从对话到工程蓝图</h2>
        </header>
        <div class="spread-grid">
          <article class="spread-column spread-column--primary">
            <p class="lede">
              {{ plan.architecture_notes || 'The planning agent has produced an overall architecture for this project.' }}
            </p>
            <p class="lede-meta">
              该规划由多个专门 Agent 协同完成：先在抽象层模拟用户与系统交互，再拆解为工程任务与文件结构。
            </p>
          </article>
          <aside class="spread-column spread-column--meta">
            <dl class="meta-list">
              <div class="meta-item">
                <dt>Tasks</dt>
                <dd>{{ metaStats.taskCount }}</dd>
              </div>
              <div class="meta-item">
                <dt>Files</dt>
                <dd>{{ metaStats.fileCount }}</dd>
              </div>
              <div class="meta-item">
                <dt>Dependencies</dt>
                <dd>{{ metaStats.dependencyCount }}</dd>
              </div>
              <div class="meta-item">
                <dt>BDD Cases</dt>
                <dd>{{ metaStats.bddCount }}</dd>
              </div>
            </dl>
            <div v-if="plan.dependencies?.length" class="meta-footnotes">
              <h3>关键依赖</h3>
              <ul>
                <li v-for="(dep, i) in plan.dependencies.slice(0, 6)" :key="i">
                  {{ dep }}
                </li>
              </ul>
            </div>
          </aside>
        </div>
      </section>

      <!-- Spread 2: TaskDivision -->
      <section class="spread spread-tasks" v-reveal-on-scroll>
        <header class="spread-header spread-header--compact">
          <div class="spread-kicker">TaskDivision</div>
          <h2 class="spread-title">把产品拆成可以交付的工程块</h2>
        </header>
        <div class="spread-grid spread-grid--offset">
          <article class="spread-column spread-column--taskflow">
            <div
              v-for="group in groupedTasks"
              :key="group.type"
              class="task-group"
            >
              <h3 class="task-group-title">{{ group.label }}</h3>
              <ol class="task-list">
                <li
                  v-for="task in group.tasks.slice(0, 4)"
                  :key="task.id"
                  class="task-item"
                >
                  <div class="task-badge">#{{ task.id }}</div>
                  <div class="task-body">
                    <div class="task-name">{{ task.name }}</div>
                    <p class="task-desc">
                      {{ task.description }}
                    </p>
                    <div class="task-meta-row">
                      <span class="pill">
                        优先级 · {{ task.priority ?? 1 }}
                      </span>
                      <span class="pill pill-ghost">
                        复杂度 · {{ task.estimated_complexity }}
                      </span>
                    </div>
                  </div>
                </li>
              </ol>
            </div>
          </article>
          <aside class="spread-column spread-column--timeline">
            <p class="timeline-eyebrow">Execution Timeline</p>
            <ul class="timeline-list">
              <li
                v-for="task in (plan.tasks || []).slice(0, 6)"
                :key="task.id"
                class="timeline-item"
              >
                <span class="timeline-dot"></span>
                <div class="timeline-content">
                  <div class="timeline-title">
                    {{ task.name }}
                  </div>
                  <p class="timeline-sub">
                    {{ task.description }}
                  </p>
                </div>
              </li>
            </ul>
          </aside>
        </div>
      </section>

      <!-- Spread 3: AlgorithmAnalysis -->
      <section class="spread spread-algorithms" v-reveal-on-scroll>
        <header class="spread-header spread-header--dark">
          <div class="spread-kicker">AlgorithmAnalysis</div>
          <h2 class="spread-title">在实现细节里寻找最稳妥的路径</h2>
        </header>
        <div class="spread-grid spread-grid--algos">
          <article class="spread-column spread-column--quotes">
            <blockquote
              v-for="(algo, index) in algorithmHighlights"
              :key="algo.task_id || index"
              class="algo-quote"
            >
              <p class="algo-quote-type">
                {{ algo.algorithm_type }}
              </p>
              <p class="algo-quote-body">
                {{ algo.implementation_approach }}
              </p>
              <footer class="algo-quote-footer">
                关联任务 · {{ algo.task_id }}
              </footer>
            </blockquote>
          </article>
          <aside class="spread-column spread-column--notes">
            <h3 class="algo-notes-title">Implementation notes</h3>
            <ul class="algo-notes-list">
              <li
                v-for="(algo, i) in algorithmHighlights"
                :key="`note-${i}`"
                class="algo-note"
              >
                <div class="algo-note-header">
                  <span class="algo-note-tag">
                    {{ algo.algorithm_type }}
                  </span>
                  <span v-if="algo.libraries?.length" class="algo-note-lib">
                    {{ algo.libraries.join(', ') }}
                  </span>
                </div>
                <p v-if="algo.notes" class="algo-note-body">
                  {{ algo.notes }}
                </p>
              </li>
            </ul>
          </aside>
        </div>
      </section>

      <!-- Spread 4: SchemePlanning -->
      <section class="spread spread-schemes" v-reveal-on-scroll>
        <header class="spread-header spread-header--wide">
          <div class="spread-kicker">SchemePlanning</div>
          <h2 class="spread-title">用文件与界面草图排出产品的版式</h2>
        </header>
        <div class="spread-grid spread-grid--schemes">
          <article class="spread-column spread-column--tiles">
            <div class="scheme-tiles">
              <article
                v-for="file in fileTiles"
                :key="file.path"
                class="scheme-tile"
                :class="`scheme-tile--${file.size}`"
              >
                <header class="scheme-tile-header">
                  <span class="scheme-tile-path">{{ file.path }}</span>
                  <span v-if="file.layer" class="scheme-tile-layer">
                    {{ file.layer }}
                  </span>
                </header>
                <p class="scheme-tile-body">
                  {{ file.purpose }}
                </p>
              </article>
            </div>
          </article>
          <aside class="spread-column spread-column--images" v-if="imageSpecs.length">
            <p class="images-eyebrow">ImageSpecs</p>
            <ul class="images-list">
              <li
                v-for="img in imageSpecs"
                :key="img.id"
                class="images-item"
              >
                <div class="images-label">
                  <span class="images-id">{{ img.id }}</span>
                  <span v-if="img.role" class="images-role">{{ img.role }}</span>
                </div>
                <p class="images-prompt">
                  {{ img.prompt }}
                </p>
                <p class="images-path">
                  {{ img.suggested_path }}
                </p>
              </li>
            </ul>
          </aside>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.plan-shell {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--spacing-32);
  background: radial-gradient(circle at top left, rgba(15, 23, 42, 0.9), rgba(0, 0, 0, 1));
  color: var(--text-primary);
  font-family: var(--font-sans);
}

.plan-empty,
.plan-loading,
.plan-error {
  max-width: 640px;
  margin: 0 auto;
  text-align: left;
}

.plan-empty-title {
  font-size: 1.4rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-12);
}

.plan-empty-desc {
  font-size: 0.95rem;
  color: var(--text-muted);
  line-height: 1.7;
}

.plan-loading {
  display: flex;
  align-items: center;
  gap: var(--spacing-12);
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.plan-loading-dots {
  display: inline-flex;
  gap: 4px;
}

.plan-loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--accent);
  animation: planDots 0.8s ease-in-out infinite alternate;
}

.plan-loading-dots span:nth-child(2) {
  animation-delay: 0.15s;
}

.plan-loading-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes planDots {
  to {
    transform: translateY(-4px);
    opacity: 0.6;
  }
}

.plan-error-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: var(--spacing-8);
}

.plan-error-body {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: var(--spacing-16);
}

.plan-error-btn {
  padding: 8px 18px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
}

.plan-layout {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-40);
}

.plan-spine {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, rgba(148, 163, 184, 0.4), transparent 60%);
  transform: translateX(8px);
}

.spread {
  position: relative;
  padding-left: 32px;
}

.spread-header {
  margin-bottom: var(--spacing-16);
}

.spread-header--compact {
  margin-bottom: var(--spacing-12);
}

.spread-header--dark {
  margin-bottom: var(--spacing-20);
}

.spread-header--wide {
  margin-bottom: var(--spacing-24);
}

.spread-kicker {
  font-size: 0.7rem;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.spread-title {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 1.8rem;
  letter-spacing: 0.02em;
  line-height: 1.25;
  margin: 0;
}

.spread-grid {
  display: grid;
  grid-template-columns: minmax(0, 2.2fr) minmax(0, 1.4fr);
  gap: var(--spacing-24);
  align-items: flex-start;
}

.spread-grid--offset {
  grid-template-columns: minmax(0, 2.5fr) minmax(0, 1.2fr);
}

.spread-grid--algos {
  grid-template-columns: minmax(0, 1.8fr) minmax(0, 1.4fr);
}

.spread-grid--schemes {
  grid-template-columns: minmax(0, 2.1fr) minmax(0, 1.2fr);
}

.spread-column {
  position: relative;
}

.spread-column--primary {
  max-width: 640px;
}

.lede {
  font-size: 1.02rem;
  line-height: 1.8;
  color: var(--text-accent);
  margin: 0 0 var(--spacing-16);
}

.lede-meta {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-secondary);
  max-width: 520px;
}

.spread-column--meta {
  padding-top: 4px;
}

.meta-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 18px;
  margin: 0 0 var(--spacing-16);
}

.meta-item dt {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.meta-item dd {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.meta-footnotes h3 {
  font-size: 0.8rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 6px;
}

.meta-footnotes ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-footnotes li {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.spread-column--taskflow {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-24);
}

.task-group-title {
  font-size: 0.86rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 8px;
}

.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px 14px;
  padding-bottom: 10px;
  border-bottom: 1px dashed rgba(148, 163, 184, 0.3);
}

.task-badge {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  color: var(--text-secondary);
  align-self: flex-start;
}

.task-body {
  min-width: 0;
}

.task-name {
  font-size: 0.92rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.task-desc {
  margin: 0 0 6px;
  font-size: 0.84rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.task-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill {
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.16);
  color: rgba(125, 211, 252, 1);
  font-size: 0.72rem;
}

.pill-ghost {
  background: rgba(148, 163, 184, 0.16);
  color: var(--text-secondary);
}

.spread-column--timeline {
  padding-top: 12px;
}

.timeline-eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 10px;
}

.timeline-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px 12px;
}

.timeline-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  border: 2px solid rgba(59, 130, 246, 0.8);
  margin-top: 4px;
}

.timeline-content {
  min-width: 0;
}

.timeline-title {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 2px;
}

.timeline-sub {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.spread-algorithms {
  background: radial-gradient(circle at top, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 1));
  border-radius: var(--radius-xl);
  padding: var(--spacing-24) var(--spacing-24) var(--spacing-24) 32px;
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(148, 163, 184, 0.5);
}

.spread-algorithms .spread-title {
  font-size: 1.6rem;
}

.spread-column--quotes {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-16);
}

.algo-quote {
  margin: 0;
  padding: 14px 16px;
  border-left: 2px solid rgba(129, 140, 248, 0.9);
  background: rgba(15, 23, 42, 0.8);
  border-radius: 0 12px 12px 0;
}

.algo-quote-type {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 4px;
}

.algo-quote-body {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-accent);
  margin: 0 0 6px;
}

.algo-quote-footer {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.spread-column--notes {
  padding-top: 6px;
}

.algo-notes-title {
  font-size: 0.86rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 10px;
}

.algo-notes-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.algo-note {
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.7);
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.5);
}

.algo-note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.algo-note-tag {
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.algo-note-lib {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.algo-note-body {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.spread-schemes {
  padding-bottom: var(--spacing-8);
}

.spread-column--tiles {
  min-width: 0;
}

.scheme-tiles {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--spacing-12);
}

.scheme-tile {
  background: rgba(15, 23, 42, 0.9);
  border-radius: 14px;
  padding: 12px 14px;
  border: 1px solid rgba(31, 41, 55, 0.9);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.8);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.scheme-tile--hero {
  grid-column: span 4;
  grid-row: span 2;
}

.scheme-tile--tall {
  grid-column: span 2;
  grid-row: span 2;
}

.scheme-tile--wide {
  grid-column: span 3;
  grid-row: span 1;
}

.scheme-tile--small {
  grid-column: span 2;
  grid-row: span 1;
}

.scheme-tile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.scheme-tile-path {
  font-size: 0.8rem;
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scheme-tile-layer {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  color: var(--text-muted);
}

.scheme-tile-body {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.spread-column--images {
  padding-top: 6px;
}

.images-eyebrow {
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 10px;
}

.images-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.images-item {
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.5);
  padding: 10px 12px;
}

.images-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.images-id {
  font-size: 0.78rem;
  font-weight: 600;
}

.images-role {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.16);
  color: rgba(125, 211, 252, 1);
}

.images-prompt {
  margin: 0 0 4px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.images-path {
  margin: 0;
  font-size: 0.76rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

@media (max-width: 1024px) {
  .plan-shell {
    padding: var(--spacing-24);
  }

  .spread-grid,
  .spread-grid--offset,
  .spread-grid--algos,
  .spread-grid--schemes {
    grid-template-columns: minmax(0, 1fr);
  }

  .spread-column--meta,
  .spread-column--timeline,
  .spread-column--images {
    order: 2;
  }

  .spread-column--primary,
  .spread-column--taskflow,
  .spread-column--tiles {
    order: 1;
  }

  .scheme-tiles {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .scheme-tile--hero {
    grid-column: span 3;
  }
}

@media (max-width: 768px) {
  .plan-shell {
    padding: var(--spacing-16);
  }

  .spread {
    padding-left: 20px;
  }

  .spread-title {
    font-size: 1.4rem;
  }

  .plan-spine {
    transform: translateX(4px);
  }

  .scheme-tiles {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (prefers-reduced-motion: reduce) {
  .plan-loading-dots span {
    animation: none;
  }
}
</style>

