<template>
  <div class="editor-container">
    <div class="toolbar">
      <input 
        v-model="currentArticle.title" 
        class="title-input" 
        placeholder="输入文章标题..." 
      />
      <div class="actions">
        <span v-if="isSaving" class="status-text">正在同步同步...</span>
        <button 
          @click="handleSave" 
          class="save-btn" 
          :disabled="isSaving"
        >
          {{ isSaving ? '保存中...' : '保存到 GitHub' }}
        </button>
      </div>
    </div>
    <div id="vditor" class="editor-main"></div>
  </div>
</template>

<script setup lang="ts">
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  articleData: any 
}>()

const emit = defineEmits(['refresh'])

// --- 状态定义 ---
const vditor = ref<Vditor | null>(null)
const isSaving = ref(false)

// 内部维护的当前文章状态
const currentArticle = ref({
  path: '',
  sha: '',
  title: '',
  content: ''
})

// --- 核心逻辑：数据同步 ---

// 监听父组件数据变化
watch(() => props.articleData, (newVal) => {
  if (!newVal) return

  // 同步基础信息
  currentArticle.value.path = newVal.path
  currentArticle.value.sha = newVal.sha
  currentArticle.value.title = newVal.title || newVal.name?.replace('.md', '') || ''
  
  // 确保编辑器存在后再填充内容
  if (vditor.value) {
    const vdContent = vditor.value.getValue()
    if (vdContent !== newVal.content) {
      // 这里的 content 可能包含 Frontmatter，Vditor 会自动处理
      vditor.value.setValue(newVal.content || '')
    }
  }
}, { immediate: true, deep: true })

// --- 保存逻辑 ---
const handleSave = async () => {
  if (!currentArticle.value.path) return
  
  // 获取编辑器最新内容
  const content = vditor.value?.getValue()
  if (isSaving.value) return

  isSaving.value = true
  try {
    const res = await axios.post('/api/article/save', {
      path: currentArticle.value.path,
      content: content,
      sha: currentArticle.value.sha,
      // 标题若修改，可以在这里处理 Frontmatter 更新逻辑（如果后端没处理的话）
      message: `Update: ${currentArticle.value.title}`
    })

    if (res.data.status === 'success') {
      ElMessage.success('已安全同步至 GitHub')
      
      // 更新 SHA 避免下次提交 409 冲突
      currentArticle.value.sha = res.data.sha
      
      // 触发列表刷新
      emit('refresh')
    }
  } catch (e: any) {
    console.error('Save Error:', e)
    ElMessage.error(e.response?.data?.detail || '保存失败，请检查网络')
  } finally {
    isSaving.value = false
  }
}

// --- 初始化编辑器 ---
onMounted(() => {
  vditor.value = new Vditor('vditor', {
    height: 'calc(100vh - 70px)', // 减去 toolbar 高度
    mode: 'ir', // 即时渲染，最接近 Typora 的体验
    cache: { enable: false }, // 必须关闭，否则多文章切换会串内容
    placeholder: '输入正文内容...',
    theme: 'classic',
    icon: 'ant', // 图标风格
    toolbarConfig: {
      pin: true // 工具栏置顶
    },
    // 图片上传配置
    upload: {
      url: '/api/upload/image', // 对接你的 main.py 中的上传接口
      fieldName: 'file',
      max: 5 * 1024 * 1024, // 5MB
      linkToImgUrl: '/api/fetch/image',
      // 格式化后端返回的图片地址
      format(files, responseText) {
        const res = JSON.parse(responseText)
        return JSON.stringify({
          msg: res.msg || '',
          code: res.code === 200 ? 0 : 1, // Vditor 成功 code 是 0
          data: {
            errFiles: [],
            succMap: {
              [res.fileName || 'image.png']: res.url // 这里的字段需根据你后端返回调整
            }
          }
        })
      }
    },
    after: () => {
      // 初始数据填充兜底
      if (props.articleData?.content) {
        vditor.value?.setValue(props.articleData.content)
      }
    }
  })
})
</script>

<style lang="scss" scoped>
.editor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;

  .toolbar {
    display: flex;
    padding: 0 24px;
    height: 70px;
    background: #ffffff;
    border-bottom: 1px solid #f0f0f0;
    align-items: center;
    justify-content: space-between;

    .title-input {
      flex: 1;
      font-size: 1.25rem;
      font-weight: 600;
      border: none;
      outline: none;
      color: #333;
      padding-right: 20px;

      &::placeholder {
        color: #c0c4cc;
      }
    }

    .actions {
      display: flex;
      align-items: center;
      gap: 15px;

      .status-text {
        font-size: 12px;
        color: #909399;
      }

      .save-btn {
        padding: 9px 24px;
        background: #42b883;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 2px 6px rgba(66, 184, 131, 0.2);

        &:hover {
          background: #33a06f;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(66, 184, 131, 0.3);
        }

        &:active {
          transform: translateY(0);
        }

        &:disabled {
          background: #a7e1c4;
          cursor: not-allowed;
          box-shadow: none;
        }
      }
    }
  }

  .editor-main {
    flex: 1;
    // 覆盖 Vditor 默认边框
    :deep(.vditor) {
      border: none;
    }
  }
}
</style>
