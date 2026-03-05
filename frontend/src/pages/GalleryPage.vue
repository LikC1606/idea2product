<script setup>
import MasonryGrid from '../components/MasonryGrid.vue'

const demoImages = [
  {
    id: 'hero-dashboard',
    src: 'https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '代码编辑器与数据面板的暗色界面截图',
  },
  {
    id: 'workflow-nodes',
    src: 'https://images.pexels.com/photos/2706379/pexels-photo-2706379.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '带有流程节点与连线的系统白板',
  },
  {
    id: 'terminal-logs',
    src: 'https://images.pexels.com/photos/546819/pexels-photo-546819.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '终端窗口与日志输出的屏幕特写',
  },
  {
    id: 'design-system',
    src: 'https://images.pexels.com/photos/1181467/pexels-photo-1181467.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '界面设计系统与组件库预览',
  },
  {
    id: 'charts',
    src: 'https://images.pexels.com/photos/669610/pexels-photo-669610.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '折线图与柱状图的数据可视化界面',
  },
  {
    id: 'timeline',
    src: 'https://images.pexels.com/photos/1367272/pexels-photo-1367272.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '带有任务卡片的产品路线图白板',
  },
  {
    id: 'code-review',
    src: 'https://images.pexels.com/photos/4974915/pexels-photo-4974915.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '多人在大屏幕前审查代码的场景',
  },
  {
    id: 'gallery-grid',
    src: 'https://images.pexels.com/photos/2706373/pexels-photo-2706373.jpeg?auto=compress&cs=tinysrgb&w=800',
    alt: '贴满便签与截图的墙面',
  },
]
</script>

<template>
  <div class="gallery-page">
    <header class="gallery-header">
      <h1 class="gallery-title">Masonry Layout 示例</h1>
      <p class="gallery-subtitle">
        用于展示生成应用的截图、作品集或图片墙。列数会根据屏幕宽度自动变化，并尽量减少大块空白。
      </p>
    </header>

    <section class="gallery-section">
      <MasonryGrid :items="demoImages" :min-column-width="220" :gap="16" />
    </section>
  </div>
</template>

<style scoped>
.gallery-page {
  min-height: 100vh;
  padding: 24px 40px 40px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.gallery-header {
  max-width: 720px;
}

.gallery-title {
  font-size: 1.6rem;
  font-weight: 620;
  margin-bottom: 8px;
}

.gallery-subtitle {
  font-size: 0.94rem;
  color: var(--text-secondary);
}

.gallery-section {
  border-top: 1px solid rgba(15, 23, 42, 0.6);
  padding-top: 20px;
}

@media (max-width: 768px) {
  .gallery-page {
    padding: 16px 16px 28px;
  }
}
</style>

