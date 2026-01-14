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
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from './components/Sidebar.vue'
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

// --- 状态定义 ---
const treeData = ref<any[]>([])
const isSideLoading = ref(false)
const isContentLoading = ref(false)
const isSaving = ref(false) 
const originalContent = ref('') 
const selectedNode = ref<any>(null) // 统一记录当前选中的节点

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

// --- 核心逻辑 ---

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

// 2. 选中节点处理
const handleSelectArticle = async (data: any) => {
  selectedNode.value = data 
  if (data.type !== 'file') return
  
  isContentLoading.value = true
  try {
    const res = await axios.get('/api/article/detail', { params: { path: data.path } })
    currentArticle.value = res.data
    originalContent.value = res.data.content
  } catch (err) {
    ElMessage.error('读取内容失败')
  } finally {
    isContentLoading.value = false
  }
}

// 3. 智能获取当前目标目录路径 (VS Code 逻辑)
const getTargetDirPath = () => {
  // 如果没有选中，或者选中的是根部文件，默认放在 posts 根目录
  if (!selectedNode.value) return 'src/posts'
  
  if (selectedNode.value.type === 'folder') {
    return selectedNode.value.path
  } else {
    // 如果选中的是文件，返回该文件所在的父级目录
    const pathParts = selectedNode.value.path.split('/')
    pathParts.pop() // 移除文件名
    return pathParts.join('/')
  }
}

// 4. 新建文章逻辑
const handleNewArticle = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入文章标题', '新建文章', {
      inputPattern: /\S+/,
      inputErrorMessage: '标题不能为空'
    })
    
    if (name) {
      const parentPath = getTargetDirPath()
      const fileName = name.endsWith('.md') ? name : `${name}.md`
      
      currentArticle.value = {
        path: `${parentPath}/${fileName}`,
        title: name,
        content: `---\ntitle: ${name}\ndate: ${new Date().toISOString().split('T')[0]}\n---\n\n开始你的创作...`,
        sha: "" // 标记为新建
      }
      originalContent.value = ""
      ElMessage.success(`草稿已在目录 [${parentPath}] 下准备就绪`)
    }
  } catch (e) {}
}

// 5. 新建文件夹逻辑 (本地虚拟节点)
const handleNewFolder = async () => {
  try {
    const { value: folderName } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹')
    if (!folderName) return

    const parentPath = getTargetDirPath()
    
    // 创建虚拟节点
    const newNode = {
      name: folderName,
      path: `${parentPath}/${folderName}`,
      type: 'folder',
      children: [],
      isVirtual: true // Sidebar 会通过这个字段显示绿色斜体和“本地”标签
    }

    // 如果父目录就是根
    if (parentPath === 'src/posts' || parentPath === 'src/drafts') {
       // 直接找对应根节点插入
       const rootFolder = treeData.value.find(n => n.path === parentPath)
       if(rootFolder) rootFolder.children.unshift(newNode)
       else treeData.value.unshift(newNode)
    } else {
      // 递归寻找并插入
      insertNodeToTree(treeData.value, parentPath, newNode)
    }
    
    ElMessage.success('临时文件夹已创建（推送文件后将自动同步）')
  } catch (e) {}
}

// 6. 保存/推送文章
const handleSave = async () => {
  if (!currentArticle.value || isSaving.value || !isModified.value) return

  try {
    const { value: userInputMsg } = await ElMessageBox.prompt(
      '请输入推送备注', '确认推送至 GitHub', {
        confirmButtonText: '确定推送',
        cancelButtonText: '取消',
        inputPlaceholder: '系统将自动生成默认备注...'
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
      ElMessage.success('GitHub 同步成功')
      originalContent.value = currentArticle.value.content
      // 必须刷新列表，让虚拟文件夹变成真实文件夹
      await fetchList()
      
      // 重新获取详情以拿到最新的 SHA
      const detailRes = await axios.get('/api/article/detail', {
        params: { path: currentArticle.value.path }
      })
      currentArticle.value.sha = detailRes.data.sha
    }
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

// 7. 重命名与删除 (对接后端接口)
const handleRename = async ({ data, newName }: { data: any, newName: string }) => {
  try {
    const newPath = data.path.substring(0, data.path.lastIndexOf('/') + 1) + newName
    isSideLoading.value = true
    await axios.post('/api/article/rename', {
      old_path: data.path,
      new_path: newPath,
      sha: data.sha
    })
    ElMessage.success('重命名成功')
    await fetchList()
  } catch (err) {
    ElMessage.error('重命名失败')
  } finally {
    isSideLoading.value = false
  }
}

const handleDelete = async (data: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除 ${data.name} 吗？`, '警告', { type: 'warning' })
    isSideLoading.value = true
    await axios.post('/api/article/delete', { path: data.path, sha: data.sha })
    ElMessage.success('文件已从 GitHub 删除')
    if (currentArticle.value?.path === data.path) currentArticle.value = null
    await fetchList()
  } catch (e) {} finally {
    isSideLoading.value = false
  }
}

// --- 辅助工具函数 ---

const insertNodeToTree = (nodes: any[], targetPath: string, newNode: any): boolean => {
  for (const node of nodes) {
    if (node.path === targetPath && node.type === 'folder') {
      if (!node.children) node.children = []
      node.children.unshift(newNode)
      return true
    }
    if (node.children && insertNodeToTree(node.children, targetPath, newNode)) return true
  }
  return false
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
