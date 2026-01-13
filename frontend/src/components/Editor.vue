<template>
  <div class="editor-container">
    <div class="toolbar">
      <input v-model="title" class="title-input" placeholder="输入文章标题..." />
      <button @click="handleSave" class="save-btn">保存到 GitHub</button>
    </div>
    <div id="vditor" class="editor-main"></div>
  </div>
</template>

<script setup lang="ts">
// 自动导入插件已处理 ref, onMounted，无需手动 import
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import axios from 'axios'

const title = ref('')
const vditor = ref<Vditor | null>(null)

// 模拟 handleSave 函数
const handleSave = async () => {
  const content = vditor.value?.getValue()
  console.log('保存标题：', title.value)
  console.log('保存内容：', content)
  // 这里稍后对接后端的保存接口
  alert('点击了保存，逻辑即将对接！')
}

onMounted(() => {
  vditor.value = new Vditor('vditor', {
    height: 'calc(100vh - 100px)',
    mode: 'ir',
    upload: {
      url: '/api/upload/image',
      fieldName: 'file',
      max: 5 * 1024 * 1024,
      // 如果这里依然报红，可以尝试在末尾加 // @ts-ignore
      // 或者删除该行（Vditor 默认会自动处理链接插入）
      // @ts-ignore
      linkToImgUrl: true,
      format(files: any, response: string) {
        return response
      }
    },
    after: () => {
      console.log('Vditor 渲染完成')
    }
  })
})
</script>

<style lang="scss" scoped>
// 使用 SCSS 嵌套语法
.editor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;

  .toolbar {
    display: flex;
    padding: 10px 20px;
    background: #f8f9fa;
    border-bottom: 1px solid #ddd;
    align-items: center;

    .title-input {
      flex: 1;
      font-size: 1.5rem;
      border: none;
      outline: none;
      background: transparent;
    }

    .save-btn {
      padding: 8px 20px;
      background: #42b883;
      color: white;
      border: none;
      border-radius: 4px;
      transition: background 0.3s; // SCSS 方便写过渡

      &:hover {
        background: #33a06f;
      }
    }
  }

  .editor-main {
    flex: 1;
  }
}
</style>
