// frontend/src/main.ts
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import './style/main.scss'

const app = createApp(App)
app.use(ElementPlus) // 确保这一行存在，它会注册 v-loading 等所有指令
app.mount('#app')
