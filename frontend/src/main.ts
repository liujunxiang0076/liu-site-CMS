// frontend/src/main.ts
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './style/main.scss'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { config } from 'md-editor-v3'

// Disable md-editor-v3 link shortener so long URLs aren't collapsed to "..."
config({
  codeMirrorExtensions(extensions) {
    return extensions.filter((ext) => ext.type !== 'linkShortener')
  }
})

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
