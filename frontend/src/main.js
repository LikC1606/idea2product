import { createApp } from 'vue'
import './assets/styles/variables.css'
import './assets/styles/components.css'
import './assets/styles/base.css'
import App from './App.vue'
import router from './router'
import revealOnScroll from './directives/revealOnScroll'

const app = createApp(App)

app.directive('reveal-on-scroll', revealOnScroll)

app.use(router).mount('#app')
