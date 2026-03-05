<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { directionVisuals, directionIconStrip, resolveDirectionImage } from '../visuals/directionVisuals'

const router = useRouter()

const directions = computed(() => [
  {
    key: 'code',
    path: '/code',
    title: '全栈 Web 应用',
    subtitle: '从自然语言到可运行的前后端代码',
    description: '适合 MVP、内部工具和原型验证，一次性完成数据模型、API 和前端界面。',
    tag: '代码',
  },
  {
    key: 'video',
    path: '/video',
    title: '视频生成工作台',
    subtitle: '从脚本到可预览的视频成品',
    description: '未来将支持故事板、镜头脚本与多场景合成，现在先从需求开始设计流程。',
    tag: '视频',
  },
  {
    key: 'audio',
    path: '/audio',
    title: '音频 / 配音生成',
    subtitle: '从文稿到自然流畅的音频内容',
    description: '适用于播客、旁白、教学录音等场景，支持多种风格与语言配置。',
    tag: '音频',
  },
  {
    key: 'slides',
    path: '/slides',
    title: 'Slides 演示文稿',
    subtitle: '自动生成结构化的 Pitch Deck / 汇报',
    description: '从要点或文档中提炼逻辑结构，快速搭建演示文稿骨架。',
    tag: 'Slides',
  },
  {
    key: 'pdf',
    path: '/pdf',
    title: 'PDF 报告 / 文档',
    subtitle: '从原始资料到排版精美的报告',
    description: '适合技术报告、分析文档、白皮书等高要求场景。',
    tag: 'PDF',
  },
])

function goTo(path, directionKey) {
  if (path === '/code' && directionKey) {
    router.push({ path, query: { direction: directionKey } })
  } else {
    router.push(path)
  }
}
</script>

<template>
  <div class="landing">
    <header class="landing-header">
      <div class="logo" @click="router.push('/')">
        <span class="logo-mark">∴</span>
        <span class="logo-text">
          <span class="logo-title">Idea2Product</span>
          <span class="logo-subtitle">AI Build Studio</span>
        </span>
      </div>
      <div class="header-actions">
        <button class="ghost-button interactive-scale-sm" type="button" @click="goTo('/code', 'code')">
          直接进入工作台
        </button>
      </div>
    </header>

    <main class="landing-main">
      <section class="hero">
        <div class="hero-left">
          <p class="eyebrow">从想法出发，落地为真实产品</p>
          <h1 class="hero-title">
            用自然语言
            <span class="hero-highlight">描述需求</span>
            ，即可生成完整产品形态。
          </h1>
          <p class="hero-subtitle">
            Idea2Product 将复杂的工程流程抽象为四个阶段：需求澄清、方案规划、代码生成与验证。
            你只需要选择想要的输出形态，其余交给系统来完成。
          </p>
          <div class="hero-actions">
            <button
              type="button"
              class="primary-button interactive-scale"
              @click="goTo('/code', 'code')"
            >
              快速开始：全栈应用生成
            </button>
            <button
              type="button"
              class="secondary-button interactive-scale-sm"
              @click="document.getElementById('directions-section')?.scrollIntoView({ behavior: 'smooth' })"
            >
              浏览全部生成方向
            </button>
          </div>
          <ul class="hero-points">
            <li>4 阶段流水线：Requirements → Planning → Code → Validation</li>
            <li>支持代码、视频、音频、Slides、PDF 等多种交付形态</li>
            <li>专为实验、Demo 及内部工具快速迭代设计</li>
          </ul>
        </div>
        <div class="hero-right">
          <figure class="hero-visual" aria-hidden="true">
            <div class="hero-visual-glass interactive-scale-sm">
              <img
                class="hero-visual-image"
                :src="resolveDirectionImage('code')"
                alt="AI 工作室的多模态输出面板插画"
              />
              <div class="hero-visual-strip">
                <img
                  class="hero-visual-strip-image"
                  :src="directionIconStrip"
                  alt="代码、视频、音频、Slides 与 PDF 的发光图标"
                />
              </div>
            </div>
          </figure>
        </div>
      </section>

      <section id="directions-section" class="directions">
        <div class="section-header">
          <h2>选择你想要的生成方向</h2>
          <p>不同方向对应不同的工作流，但都以同一套 AI 规划与验证能力为基础。</p>
        </div>
        <div class="directions-grid">
          <article
            v-for="item in directions"
            :key="item.key"
            class="direction-card interactive-scale-sm"
          >
            <header class="direction-card-header">
              <span class="direction-tag">{{ item.tag }}</span>
              <h3 class="direction-title">{{ item.title }}</h3>
              <p class="direction-subtitle">{{ item.subtitle }}</p>
            </header>
            <p class="direction-description">
              {{ item.description }}
            </p>
            <button
              type="button"
              class="card-button interactive-scale-sm"
              @click="goTo(item.path, item.key === 'code' ? 'code' : item.key)"
            >
              开始这个方向
              <span class="arrow">→</span>
            </button>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  padding: 18px 40px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.landing-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.logo-mark {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: radial-gradient(circle at 20% 20%, #38bdf8, #4f46e5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 700;
  font-size: 18px;
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.logo-title {
  font-weight: 600;
  font-size: 1rem;
}

.logo-subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ghost-button {
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(15, 23, 42, 0.4);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast),
    color var(--transition-fast), transform var(--transition-fast);
}

.ghost-button:hover {
  background: rgba(15, 23, 42, 0.7);
  border-color: rgba(148, 163, 184, 0.8);
  color: var(--text-primary);
  transform: translateY(-0.5px);
}

.landing-main {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 3.2fr) minmax(0, 2fr);
  gap: 40px;
  align-items: center;
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.eyebrow {
  font-size: 0.85rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
}

.hero-title {
  font-size: 2.4rem;
  line-height: 1.2;
  font-weight: 650;
}

.hero-highlight {
  color: var(--accent);
}

.hero-subtitle {
  font-size: 0.98rem;
  color: var(--text-secondary);
  max-width: 42rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}

.primary-button {
  padding: 10px 22px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #4f46e5, #38bdf8);
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 550;
  cursor: pointer;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.55);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast),
    filter var(--transition-fast);
}

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.7);
  filter: brightness(1.03);
}

.secondary-button {
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: rgba(15, 23, 42, 0.6);
  color: var(--text-secondary);
  font-size: 0.88rem;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast),
    color var(--transition-fast);
}

.secondary-button:hover {
  background: rgba(15, 23, 42, 0.9);
  border-color: rgba(148, 163, 184, 0.8);
  color: var(--text-primary);
}

.hero-points {
  margin-top: 6px;
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.hero-right {
  display: flex;
  justify-content: flex-end;
}

.hero-visual {
  width: 100%;
  max-width: 520px;
  display: flex;
  justify-content: flex-end;
}

.hero-visual-glass {
  position: relative;
  width: 100%;
  border-radius: 24px;
  padding: 10px;
  background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 55%),
    radial-gradient(circle at bottom right, rgba(99, 102, 241, 0.28), rgba(15, 23, 42, 0.98));
  border: 1px solid rgba(148, 163, 184, 0.5);
  box-shadow: 0 26px 72px rgba(15, 23, 42, 0.95);
  overflow: hidden;
}

.hero-visual-image {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 18px;
  object-fit: cover;
}

.hero-visual-strip {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
  padding: 4px 10px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(148, 163, 184, 0.5);
}

.hero-visual-strip-image {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}

.directions {
  padding-top: 8px;
  border-top: 1px solid rgba(15, 23, 42, 0.6);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 18px;
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
}

.section-header p {
  font-size: 0.88rem;
  color: var(--text-secondary);
}

.directions-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.direction-card {
  padding: 16px 16px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(31, 41, 55, 0.9);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.8);
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
  overflow: hidden;
}

.direction-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 65%);
  opacity: 0;
  transition: opacity var(--transition-normal);
  pointer-events: none;
}

.direction-card-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.direction-tag {
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  font-size: 0.7rem;
  color: var(--text-muted);
}

.direction-title {
  font-size: 0.98rem;
  font-weight: 560;
}

.direction-subtitle {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.direction-description {
  font-size: 0.8rem;
  color: var(--text-muted);
  flex: 1;
}

.card-button {
  margin-top: 6px;
  align-self: flex-start;
  padding: 7px 14px;
  border-radius: 999px;
  border: none;
  background: rgba(56, 189, 248, 0.08);
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: background var(--transition-fast), transform var(--transition-fast);
}

.card-button .arrow {
  font-size: 0.9rem;
}

.direction-card:hover::before {
  opacity: 1;
}

.direction-card:hover .card-button {
  background: rgba(56, 189, 248, 0.18);
  transform: translateY(-0.5px);
}

@media (max-width: 1024px) {
  .landing {
    padding-inline: 20px;
  }
  .hero {
    grid-template-columns: minmax(0, 1.2fr);
    align-items: flex-start;
  }
  .hero-right {
    justify-content: flex-start;
  }
  .directions-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .landing {
    padding: 16px 16px 28px;
  }
  .landing-header {
    gap: 12px;
  }
  .hero {
    gap: 26px;
  }
  .hero-title {
    font-size: 1.8rem;
  }
  .directions-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>

