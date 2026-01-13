<template>
  <div class="cms-layout">
    <Sidebar :tree-data="treeData" :loading="isSideLoading" @select="handleSelectArticle" />

    <main class="main-content" v-loading="isContentLoading">
      <div v-if="currentArticle" class="editor-container">
        <div class="editor-header">
          <span class="path-tag">{{ currentArticle.path }}</span>
          <el-button type="primary" @click="handleSave">推送至 GitHub</el-button>
        </div>

        <MdEditor 
          v-model="currentArticle.content" 
          editor-id="my-editor"
          class="pro-editor"
          placeholder="开始你的 Typora 式体验..."
        />
      </div>

      <div v-else class="empty-state">
        <el-empty description="点选左侧文章开启编辑" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import Sidebar from './components/Sidebar.vue'
import { MdEditor } from 'md-editor-v3'; 
import 'md-editor-v3/lib/style.css';

// --- 状态定义 ---
const treeData = ref([])
const isSideLoading = ref(false)
const isContentLoading = ref(false)

// 当前选中的文章详情
const currentArticle = ref<{
  path: string;
  title: string;
  content: string;
  sha: string;
} | null>(null)

// --- 逻辑处理 ---

// 1. 获取文章列表
const fetchList = async () => {
  isSideLoading.value = true
  try {
    const res = await axios.get('/api/articles')
    treeData.value = res.data
  } catch (err) {
    ElMessage.error('同步文章列表失败')
  } finally {
    isSideLoading.value = false
  }
}

// 2. 选中文章并获取详情
const handleSelectArticle = async (data: any) => {
  // 文件夹不触发读取
  if (data.type !== 'file') return

  isContentLoading.value = true
  try {
    const res = await axios.get('/api/article/detail', {
      params: { path: data.path }
    })
    currentArticle.value = res.data
  } catch (err) {
    ElMessage.error('读取文章内容失败')
  } finally {
    isContentLoading.value = false
  }
}

// 3. 保存文章
const handleSave = async () => {
  if (!currentArticle.value) return

  try {
    const res = await axios.post('/api/article/save', {
      path: currentArticle.value.path,
      content: currentArticle.value.content,
      sha: currentArticle.value.sha
    })

    if (res.data.status === 'success') {
      ElMessage.success('保存成功，已同步至 GitHub')
      // 这里的重点：保存后 GitHub 会生成新 SHA，所以要重新获取列表
      fetchList()
    }
  } catch (err) {
    ElMessage.error('保存失败，请检查网络或 Token 权限')
  }
}

const createNewArticle = () => {
  ElMessage.info('新建功能开发中...')
}

onMounted(fetchList)
</script>

<style lang="scss" scoped>
/* 1. 确保最外层占满全屏且不产生外部滚动条 */
.cms-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden; // 禁止外层浏览器滚动条
  background-color: #f5f7f9;

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0; // 防止 flex 子元素溢出
    background: #fff;

    .editor-container {
      display: flex;
      flex-direction: column;
      height: 100%; // 占满 main-content
      overflow: hidden;

      .editor-header {
        height: 50px; // 固定头部高度
        padding: 0 20px;
        background: #fff;
        border-bottom: 1px solid #e8e8e8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0; // 禁止头部被压缩
        
        .breadcrumb { 
          font-size: 13px; 
          color: #909399; 
          font-family: monospace;
        }
      }

      /* 2. 关键：让编辑器组件自适应剩余高度 */
      .pro-editor {
        flex: 1; 
        height: calc(100vh - 50px) !important; // 屏幕高度减去 Header 高度
        border: none !important;
      }
    }

    .empty-placeholder {
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
    }
  }
}

/* 3. 强制隐藏编辑器外部可能产生的滚动条（可选） */
:deep(.md-editor) {
  height: 100% !important;
}
</style>
