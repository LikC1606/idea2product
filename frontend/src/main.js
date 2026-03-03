import { createApp } from 'vue'
import './assets/styles/variables.css'
import './assets/styles/components.css'
import './assets/styles/base.css'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
