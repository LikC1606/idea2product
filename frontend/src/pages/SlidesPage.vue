<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function startFromHere() {
  router.push({ path: '/code', query: { direction: 'slides' } })
}
</script>

<template>
  <div class="direction-page">
    <header class="page-header">
      <div class="page-title-block">
        <p class="eyebrow">生成方向 · Slides</p>
        <h1>Slides 演示文稿生成工作台</h1>
        <p class="subtitle">
          从零散想法到结构化 Pitch Deck 或内部汇报。
          当前阶段先通过对话澄清结构和内容，后续可以接入 PPT 生成与主题配置。
        </p>
      </div>
      <button type="button" class="ghost-button" @click="router.push('/')">
        返回首页
      </button>
    </header>

    <main class="page-main">
      <section class="layout">
        <div class="panel panel-left">
          <h2>为你的 Slides 规划骨架</h2>
          <p class="panel-text">
            想象这里是一块专注于大纲设计的区域：章节划分、每页要点、节奏控制等。
            进入工作台后，可以一步步把这些想法固化为可生成的结构化数据。
          </p>
          <ul class="hint-list">
            <li>说明场景：融资路演、产品发布、复盘汇报、技术分享等。</li>
            <li>列出核心章节，例如「问题」「方案」「产品」「进展」「计划」。</li>
            <li>如果有已有文档，可在对话中直接粘贴由系统协助提炼。</li>
          </ul>
          <button type="button" class="primary-button" @click="startFromHere">
            从这里开始需求对话
          </button>
        </div>
        <div class="panel panel-right">
          <div class="preview-placeholder">
            <p class="preview-title">结构预览 / 页缩略图（预留区域）</p>
            <p class="preview-desc">
              未来这里可以展示页面缩略图、章节导览和主题预览。
              当前版本聚焦在通过通用工作台建立高质量的内容与结构基础。
            </p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.direction-page {
  min-height: 100vh;
  padding: 18px 36px 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-title-block h1 {
  font-size: 1.8rem;
  font-weight: 650;
  margin-bottom: 4px;
}

.eyebrow {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--accent);
}

.subtitle {
  font-size: 0.9rem;
  color: var(--text-secondary);
  max-width: 40rem;
}

.ghost-button {
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: rgba(15, 23, 42, 0.7);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast),
    color var(--transition-fast), transform var(--transition-fast);
}

.ghost-button:hover {
  background: rgba(15, 23, 42, 0.95);
  border-color: rgba(148, 163, 184, 0.85);
  color: var(--text-primary);
  transform: translateY(-0.5px);
}

.page-main {
  flex: 1;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 22px;
}

.panel {
  border-radius: 18px;
  border: 1px solid rgba(31, 41, 55, 0.9);
  background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.08), transparent 55%),
    rgba(15, 23, 42, 0.96);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.9);
  padding: 18px 18px 20px;
}

.panel-left h2 {
  font-size: 1.1rem;
  margin-bottom: 8px;
}

.panel-text {
  font-size: 0.88rem;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.hint-list {
  list-style: disc;
  padding-left: 18px;
  margin-bottom: 14px;
  font-size: 0.82rem;
  color: var(--text-muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.primary-button {
  padding: 8px 18px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #4f46e5, #38bdf8);
  color: #ffffff;
  font-size: 0.86rem;
  font-weight: 540;
  cursor: pointer;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.7);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.9);
}

.preview-placeholder {
  height: 100%;
  border-radius: 14px;
  border: 1px dashed rgba(148, 163, 184, 0.6);
  padding: 16px 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.preview-title {
  font-size: 0.9rem;
  font-weight: 540;
}

.preview-desc {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

@media (max-width: 1024px) {
  .direction-page {
    padding-inline: 18px;
  }
  .layout {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 768px) {
  .direction-page {
    padding-inline: 14px;
  }
}
</style>

