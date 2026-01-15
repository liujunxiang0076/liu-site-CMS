<template>
  <div class="editor-container">
    <div class="toolbar">
      <div class="status-dot" :class="articleStatus" :title="statusTip"></div>

      <input v-model="currentArticle.title" class="title-input" placeholder="输入文章标题..." />
      <div class="actions">
        <span v-if="isSaving" class="status-text">同步中...</span>
        <button @click="handleSave" class="save-btn" :disabled="isSaving">
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
import { ElMessage } from 'element-plus'
import { ref, watch, computed, onMounted } from 'vue'
import { articleApi } from '@/api/article'

const props = defineProps<{
  articleData: any
}>()

const emit = defineEmits(['refresh'])

// --- 状态定义 ---
const vditor = ref<Vditor | null>(null)
const isSaving = ref(false)
const originalContent = ref('') // 记录刚打开时的内容
const isModifiedLocally = ref(false) // 局部状态，用于强制触发实时变色

// 内部维护的当前文章状态
const currentArticle = ref({
  path: '',
  sha: '',
  title: '',
  content: ''
})

// --- 核心逻辑：状态判断 ---

const articleStatus = computed(() => {
  // 1. 如果正在保存
  if (isSaving.value) return 'is-syncing'

  // 2. 如果没有 SHA，说明是新建但从未同步过 GitHub 的虚拟文件
  if (!currentArticle.value.sha) return 'is-new'

  // 3. 如果当前内容与原始内容不一致，说明修改了
  // 这里的 isModifiedLocally 确保在输入时能触发 computed 重新计算
  // 注意：我们假设 originalContent 就是“已同步”的内容
  if (isModifiedLocally.value) {
    return 'is-modified'
  }

  // 4. 否则是已同步状态
  return 'is-synced'
})

const statusTip = computed(() => {
  const tips: Record<string, string> = { 
    'is-new': '新文档 (未同步)', 
    'is-modified': '已修改 (待保存)', 
    'is-synced': '内容已同步',
    'is-syncing': '同步中...'
  }
  return tips[articleStatus.value]
})

// 监听父组件数据变化
watch(() => props.articleData, (newVal) => {
  if (!newVal) return

  // 同步基础信息
  currentArticle.value.path = newVal.path
  currentArticle.value.sha = newVal.sha
  currentArticle.value.title = newVal.title || newVal.name?.replace('.md', '') || ''

  // 关键：记录初始内容
  originalContent.value = newVal.content || ''
  isModifiedLocally.value = false // 重置修改状态

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
    const res = await articleApi.save({
      path: currentArticle.value.path,
      content: content || '',
      sha: currentArticle.value.sha,
      // 标题若修改，可以在这里处理 Frontmatter 更新逻辑（如果后端没处理的话）
      message: `Update: ${currentArticle.value.title}`
    })

    if (res.code === 200) {
      ElMessage.success('已安全同步至 GitHub')
      
      // 更新 SHA 避免下次提交 409 冲突
      currentArticle.value.sha = res.sha || ''

      // 重要：保存后将当前内容设为“原始内容”，让点变绿
      originalContent.value = content || ''
      isModifiedLocally.value = false

      emit('refresh')
    }
  } catch (e: any) {
    // 错误已由拦截器处理，此处仅做兜底或特定逻辑
    console.error(e)
  } finally {
    isSaving.value = false
  }
}

// --- 初始化编辑器 ---
onMounted(() => {
  vditor.value = new Vditor('vditor', {
    height: 'calc(100vh - 70px)',
    mode: 'ir',
    cache: { enable: false },
    placeholder: '输入正文内容...',
    // 监听输入事件，实现小点实时变色
    input: (value) => {
      // 简单判断：只要内容不等于原始内容，就是 modified
      isModifiedLocally.value = value !== originalContent.value
    },
    // 图片上传配置
    upload: {
      url: '/api/upload/image', // 保持原样，Vditor 内部使用 XHR
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

    // --- 指示灯样式 ---
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-right: 15px;
      transition: all 0.3s ease;

      &.is-new {
        background: #f56c6c; // 红色：新文档
        box-shadow: 0 0 6px rgba(245, 108, 108, 0.5);
      }

      &.is-modified {
        background: #795548; // 棕色：已修改 (未同步)
        box-shadow: 0 0 6px rgba(121, 85, 72, 0.5);
      }

      &.is-synced {
        background: #008000; // 深绿色：已同步
        box-shadow: 0 0 5px rgba(0, 128, 0, 0.5);
      }

      &.is-syncing {
        background: #2196F3; // 蓝色：同步中
        box-shadow: 0 0 5px rgba(33, 150, 243, 0.5);
        animation: breath 2s infinite ease-in-out;
      }
    }

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

  // 呼吸动画，让黄色小点更有提示感
  @keyframes breath {
    0% {
      opacity: 1;
      transform: scale(1);
    }

    50% {
      opacity: 0.6;
      transform: scale(1.2);
    }

    100% {
      opacity: 1;
      transform: scale(1);
    }
  }
}
</style>
