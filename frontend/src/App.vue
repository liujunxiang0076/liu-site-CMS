<template>
  <div class="cms-layout">
    <Sidebar :tree-data="treeData" :loading="isSideLoading" @select="handleSelectArticle"
      @create-article="handleNewArticle" @create-folder="handleNewFolder" @refresh="fetchList" @rename="handleRename"
      @delete="handleDelete" />
    <main class="main-content" v-loading="isContentLoading">
      <div v-if="currentArticle" class="editor-container">
        <div class="editor-header">
          <span class="path-tag">{{ currentArticle.path }}</span>
          <el-button type="primary" :loading="isSaving" @click="handleSave" :disabled="!isModified">
            {{ isSaving ? '同步中...' : '推送至 GitHub' }}
          </el-button>
        </div>

        <MdEditor v-model="currentArticle.content" editor-id="my-editor" class="pro-editor"
          placeholder="开始你的 Typora 式体验..." :no-front-matter="true" @onSave="handleSave" />
      </div>

      <div v-else class="empty-state">
        <el-empty description="点选左侧文章开启编辑" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue' // 修复：必须显式导入 computed
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from './components/Sidebar.vue'
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

// --- 状态定义 ---
const treeData = ref([])
const isSideLoading = ref(false)
const isContentLoading = ref(false)
const isSaving = ref(false) 
const originalContent = ref('') 

const currentArticle = ref<{
  path: string;
  title: string;
  content: string;
  sha: string;
} | null>(null)

// 计算属性：判断内容是否被修改
const isModified = computed(() => {
  if (!currentArticle.value) return false
  return currentArticle.value.content !== originalContent.value
})

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

// 2. 选中文章
const handleSelectArticle = async (data: any) => {
  if (data.type !== 'file') return
  isContentLoading.value = true
  try {
    const res = await axios.get('/api/article/detail', {
      params: { path: data.path }
    })
    currentArticle.value = res.data
    originalContent.value = res.data.content
  } catch (err) {
    ElMessage.error('读取文章内容失败')
  } finally {
    isContentLoading.value = false
  }
}

// 3. 保存/推送文章
const handleSave = async () => {
  if (!currentArticle.value || isSaving.value || !isModified.value) return

  try {
    const { value: userInputMsg } = await ElMessageBox.prompt(
      '请输入推送备注（留空将自动生成记录）',
      '确认推送至 GitHub',
      {
        confirmButtonText: '确定推送',
        cancelButtonText: '取消',
        inputPlaceholder: '例如：优化了开头段落...',
      }
    )

    isSaving.value = true
    const res = await axios.post('/api/article/save', {
      path: currentArticle.value.path,
      content: currentArticle.value.content,
      sha: currentArticle.value.sha,
      message: userInputMsg
    })

    if (res.data.status === 'success') {
      ElMessage.success('保存成功')
      originalContent.value = currentArticle.value.content
      // 重新获取 SHA 避免冲突
      const detailRes = await axios.get('/api/article/detail', {
        params: { path: currentArticle.value.path }
      })
      currentArticle.value.sha = detailRes.data.sha
      fetchList() // 刷新列表以更新可能的显示状态
    }
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 4. 重命名处理 (VS Code 逻辑补全)
const handleRename = async ({ data, newName }: { data: any, newName: string }) => {
  // 注意：GitHub 重命名通常需要 API 支持（先删后建或 Move 接口）
  // 这里先实现前端提示，待后端 main.py 补全接口
  ElMessage.info(`准备重命名为: ${newName} (正在开发中)`)
  // 操作成功后刷新列表
  // await axios.post('/api/article/rename', { oldPath: data.path, newName })
  // fetchList()
}

// 5. 删除处理 (右键菜单补全)
const handleDelete = async (data: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除 ${data.name} 吗？此操作不可撤销`, '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    ElMessage.warning(`正在请求删除: ${data.path} (需要后端接口支持)`)
    // 操作成功后刷新并清空当前编辑器
    // await axios.post('/api/article/delete', { path: data.path })
    // if (currentArticle.value?.path === data.path) currentArticle.value = null
    // fetchList()
  } catch { /* 取消删除 */ }
}

const handleNewArticle = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入文章标题', '新建文章', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '不要包含 .md 后缀',
    })

    if (name) {
      currentArticle.value = {
        path: `src/posts/2026/${name}.md`,
        title: name,
        content: `---\ntitle: ${name}\ndate: ${new Date().toISOString().split('T')[0]}\n---\n\n开始你的创作...`,
        sha: "" 
      }
      originalContent.value = ""
      ElMessage.success('草稿就绪，点击推送同步')
    }
  } catch (e) {}
}

const handleNewFolder = async () => {
  try {
    const { value: folderName } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    if (folderName) {
      ElMessage.info(`文件夹 "${folderName}" 已就绪，在该目录下创建文件即可同步。`)
    }
  } catch {}
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
        height: 54px; // 稍微加高一点，视觉更协调
        padding: 0 20px;
        background: #fff;
        border-bottom: 1px solid #e8e8e8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0; // 确保头部不会被压缩

        .path-tag {
          font-size: 13px;
          color: #666;
          background: #f0f2f5;
          padding: 4px 10px;
          border-radius: 4px;
          font-family: 'Fira Code', monospace;
        }
      }

      /* 2. 核心修复：强制编辑器填满剩余高度 */
      .pro-editor {
        flex: 1;
        height: calc(100vh - 54px) !important; // 屏幕高度减去 Header 高度
        border: none !important;
      }
    }

    /* 空状态居中样式 */
    .empty-state {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}

/* 3. 深度选择器：修正编辑器内部组件的样式 */
:deep(.md-editor) {
  height: 100% !important;
  border: none !important;
}

/* 优化预览区域的间距，让它看起来更像博客文章 */
:deep(.md-editor-preview) {
  padding: 40px !important;
  word-break: break-word;
}

/* 隐藏 Frontmatter 后，给顶部留一点空白，美观一些 */
:deep(.md-editor-content) {
  height: 100% !important;
}

/* 针对保存按钮的微调：让 Loading 旋转更平滑 */
.el-button {
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
  font-weight: 500;

  // 当处于加载状态时，轻微改变透明度
  &.is-loading {
    opacity: 0.85;
  }
}
</style>
