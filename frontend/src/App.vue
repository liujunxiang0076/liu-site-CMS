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
          :no-front-matter="true"
          @onSave="handleSave"
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
// 修改后的保存函数
const handleSave = async () => {
  if (!currentArticle.value) return

  try {
    const res = await axios.post('/api/article/save', {
      path: currentArticle.value.path,
      content: currentArticle.value.content,
      sha: currentArticle.value.sha // 必须是当前文件最新的 SHA
    })

    if (res.data.status === 'success') {
      ElMessage.success('保存成功，已同步至 GitHub')
      
      // 【关键修复】：保存成功后，重新获取一次详情以同步最新的 SHA
      // 否则第二次保存会因为 SHA 不匹配而报 409 错误（显示为保存失败）
      const detailRes = await axios.get('/api/article/detail', {
        params: { path: currentArticle.value.path }
      })
      currentArticle.value.sha = detailRes.data.sha
    }
  } catch (err: any) {
    console.error('保存报错详情:', err.response?.data || err)
    ElMessage.error(err.response?.data?.detail || '保存失败，请检查 Token 权限或网络')
  }
}

const createNewArticle = () => {
  ElMessage.info('新建功能开发中...')
}

onMounted(fetchList)
</script>

<style lang="scss" scoped>
/* 1. 彻底锁死外层，禁止出现任何原生滚动条 */
.cms-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden; // 核心：强制隐藏浏览器最右侧和底部的滚动条
  background-color: #f5f7f9;

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh; // 必须撑满高度
    min-width: 0;
    background: #fff;

    .editor-container {
      display: flex;
      flex-direction: column;
      height: 100%; 
      width: 100%;
      overflow: hidden; // 再次锁死

      .editor-header {
        height: 50px; 
        padding: 0 20px;
        background: #fff;
        border-bottom: 1px solid #e8e8e8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0; // 确保头部不会被压缩
        
        .breadcrumb { font-size: 13px; color: #909399; font-family: monospace; }
      }

      /* 2. 核心修复：强制编辑器填满剩余高度，不准超出 */
      .pro-editor {
        flex: 1;
        height: calc(100vh - 50px) !important; // 屏幕高度减去 Header 高度
        border: none !important;
      }
    }
  }
}

/* 3. 深度选择器：修正编辑器内部组件的样式，防止产生横向滚动 */
:deep(.md-editor) {
  height: 100% !important;
}

:deep(.md-editor-content) {
  height: 100% !important;
  overflow: hidden; // 让滚动发生在编辑区域内部，而不是组件外层
}
</style>
