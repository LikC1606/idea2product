import { createRouter, createWebHistory } from 'vue-router'

import LandingPage from '../pages/LandingPage.vue'
import VideoPage from '../pages/VideoPage.vue'
import AudioPage from '../pages/AudioPage.vue'
import SlidesPage from '../pages/SlidesPage.vue'
import PdfPage from '../pages/PdfPage.vue'
import CodePage from '../pages/CodePage.vue'
import GalleryPage from '../pages/GalleryPage.vue'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingPage,
  },
  {
    path: '/code',
    name: 'code',
    component: CodePage,
  },
  {
    path: '/video',
    name: 'video',
    component: VideoPage,
  },
  {
    path: '/audio',
    name: 'audio',
    component: AudioPage,
  },
  {
    path: '/slides',
    name: 'slides',
    component: SlidesPage,
  },
  {
    path: '/pdf',
    name: 'pdf',
    component: PdfPage,
  },
  {
    path: '/gallery',
    name: 'gallery',
    component: GalleryPage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

