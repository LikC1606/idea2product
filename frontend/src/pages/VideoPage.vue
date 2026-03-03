<script setup>
import { useRouter } from 'vue-router'
import { resolveDirectionImage } from '../visuals/directionVisuals'

const router = useRouter()

function startFromHere() {
  router.push({ path: '/code', query: { direction: 'video' } })
}
</script>

<template>
  <div class="direction-page">
    <header class="page-header">
      <div class="page-title-block">
        <p class="eyebrow">生成方向 · 视频</p>
        <h1>视频生成工作台</h1>
        <p class="subtitle">
          从故事脚本到分镜与画面规划的 AI 助手。
          当前阶段先通过需求对话梳理结构，后续可无缝接入视频生成后台。
        </p>
      </div>
      <button type="button" class="ghost-button" @click="router.push('/')">
        返回首页
      </button>
    </header>

    <main class="page-main">
      <section class="layout">
        <div class="panel panel-left">
          <h2>描述你想要的视频</h2>
          <p class="panel-text">
            想象这里是一块专注于视频需求的输入区域，例如：脚本文本、场景列表、镜头节奏等。
            目前我们先通过通用工作台对话梳理这些信息。
          </p>
          <ul class="hint-list">
            <li>说明视频用途：宣传、教学、产品介绍、故事短片等。</li>
            <li>描述主要场景、角色、情绪基调和时长范围。</li>
            <li>如果有参考风格，可以在对话中一并给出。</li>
          </ul>
          <button type="button" class="primary-button" @click="startFromHere">
            从这里开始需求对话
          </button>
        </div>
        <div class="panel panel-right">
          <div class="preview-shell video-shell">
            <img
              :src="resolveDirectionImage('video')"
              alt="视频生成工作台的界面插画"
              class="preview-image"
            />
            <div class="preview-overlay">
              <p class="preview-title">视频预览 / 时间线（预留区域）</p>
              <p class="preview-desc">
                未来这里可以展示分镜预览、时间线以及生成进度。
                当前版本会在进入通用工作台后，通过对话和代码预览帮助你完善产品。
              </p>
            </div>
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

.preview-shell {
  position: relative;
  height: 100%;
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.4);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.95);
}

.video-shell {
  background: radial-gradient(circle at top left, rgba(94, 234, 212, 0.18), transparent 60%),
    radial-gradient(circle at bottom right, rgba(129, 140, 248, 0.28), rgba(15, 23, 42, 0.98));
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.preview-overlay {
  position: absolute;
  inset: auto 0 0;
  padding: 12px 16px 16px;
  background: linear-gradient(to top, rgba(15, 23, 42, 0.92), transparent);
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

