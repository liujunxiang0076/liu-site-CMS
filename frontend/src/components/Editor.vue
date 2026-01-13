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

const props = defineProps<{
  articleData: any // 从 App.vue 传下来的当前文章详情
}>()

const emit = defineEmits(['refresh'])

// 响应式变量绑定
const title = ref('')
const currentSha = ref('')
const currentPath = ref('')
const metadata = ref({})

// 监听从父组件传下来的文章数据
// 修改 Editor.vue 中的 watch 部分
watch(() => props.articleData, (newVal) => {
  // 核心：不仅要判断 newVal，还要确保 vditor 已经实例化完成
  if (newVal && vditor.value) {
    title.value = newVal.metadata?.title || ''
    // 只有 vditor.value 存在时才调用 setValue
    vditor.value.setValue(newVal.content || '')
  }
}, { immediate: true })

const handleSave = async () => {
  if (!title.value) return alert('请输入标题')

  const content = vditor.value?.getValue()

  try {
    const res = await axios.post('/api/save', {
      path: currentPath.value,
      title: title.value,
      content: content,
      sha: currentSha.value,
      metadata: metadata.value
    })

    if (res.data.status === 'success') {
      alert('保存成功！')
      // 更新当前的 sha，防止下次保存冲突
      currentSha.value = res.data.sha
      // 通知 App.vue 刷新左侧列表
      emit('refresh')
    }
  } catch (e: any) {
    console.error(e)
    alert('保存失败：' + (e.response?.data?.detail || '网络错误'))
  }
}
// 确保在挂载后初始化
onMounted(() => {
  vditor.value = new Vditor('vditor', {
    height: 'calc(100vh - 100px)',
    mode: 'ir',
    upload: {
      url: '/api/upload/image',
      fieldName: 'file',
      // ... 其他配置
    },
    after: () => {
      // 渲染完成后，如果已经有数据，就填入内容
      if (props.articleData) {
        vditor.value?.setValue(props.articleData.content)
      }
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
