import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'

export default defineConfig({
  plugins: [
    vue(),
    // 自动导入 Vue 相关函数
    AutoImport({
      imports: ['vue', 'vue-router'],
      dts: 'src/auto-import.d.ts', // 生成类型定义文件
    }),
    // 自动导入 src/components 下的组件
    Components({
      extensions: ['vue'],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 如果你有全局变量文件（如 variables.scss），可以在这里引入
        // additionalData: `@import "@/assets/styles/variables.scss";`
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3000', // 后端地址
        changeOrigin: true,
        // 如果后端接口本身不带 /api 前缀，需要重写路径
        // rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  }
})
