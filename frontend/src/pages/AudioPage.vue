<script setup>
import { useRouter } from 'vue-router'
import { resolveDirectionImage } from '../visuals/directionVisuals'

const router = useRouter()

function startFromHere() {
  router.push({ path: '/code', query: { direction: 'audio' } })
}
</script>

<template>
  <div class="direction-page">
    <header class="page-header">
      <div class="page-title-block">
        <p class="eyebrow">生成方向 · 音频</p>
        <h1>音频 / 配音生成工作台</h1>
        <p class="subtitle">
          面向播客、旁白和教学内容的 AI 音频助手。
          当前版本通过通用工作台帮助你梳理脚本与结构，后续可接入 TTS / 音乐生成服务。
        </p>
      </div>
      <button type="button" class="ghost-button" @click="router.push('/')">
        返回首页
      </button>
    </header>

    <main class="page-main">
      <section class="layout">
        <div class="panel panel-left">
          <h2>规划你想要的音频内容</h2>
          <p class="panel-text">
            在这里你可以先思考栏目的定位、受众、单集结构等要素。
            进入工作台后，系统会以对话形式帮你完善脚本和章节结构。
          </p>
          <ul class="hint-list">
            <li>说明音频类型：访谈、独白、讲解、故事等。</li>
            <li>描述每一集的大致长度，以及希望的节奏和语气。</li>
            <li>如果已有文本草稿，可以直接在对话中贴入。</li>
          </ul>
          <button type="button" class="primary-button" @click="startFromHere">
            从这里开始需求对话
          </button>
        </div>
        <div class="panel panel-right">
          <div class="preview-shell audio-shell">
            <img
              :src="resolveDirectionImage('audio')"
              alt="音频与配音生成工作台插画"
              class="preview-image"
            />
            <div class="preview-overlay">
              <p class="preview-title">波形 / 试听预览（预留区域）</p>
              <p class="preview-desc">
                未来这里可以展示音频波形、播放控件和多轨道混音视图。
                当前阶段专注于规划和生成逻辑，落地在通用代码工作台中实现能力组合。
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

.audio-shell {
  background: radial-gradient(circle at top left, rgba(45, 212, 191, 0.26), transparent 60%),
    radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.32), rgba(15, 23, 42, 0.98));
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

