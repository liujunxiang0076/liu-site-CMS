<template>
  <div class="cms-layout">
    <Sidebar :tree-data="treeData" :loading="isSideLoading" @select="handleSelectArticle"
      @create-article="handleNewArticle" @create-folder="handleNewFolder" @refresh="fetchList" @rename="handleRename"
      @delete="handleDelete" />
    <main class="main-content" v-loading="isContentLoading">
      <div v-if="currentArticle" class="editor-container">
        <div class="editor-header">
          <span class="path-tag" :class="articleStatus">{{ currentArticle.path }}</span>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from './components/Sidebar.vue'
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { articleApi } from '@/api/article'


// --- 状态定义 ---
const treeData = ref<any[]>([])
const isSideLoading = ref(false)
const isContentLoading = ref(false)
const isSaving = ref(false)
const originalContent = ref('')
const localSavedContent = ref('') // 新增：本地保存的内容快照
const selectedNode = ref<any>(null) // 统一记录当前选中的节点

const currentArticle = ref<{
  path: string;
  title: string;
  content: string;
  sha: string;
  isSynced?: boolean; // 新增：标识是否来自同步源
} | null>(null)

// 计算属性：判断内容是否被修改
const isModified = computed(() => {
  if (!currentArticle.value) return false
  return currentArticle.value.content !== originalContent.value
})

// --- 状态点逻辑 ---
const articleStatus = computed(() => {
  if (!currentArticle.value) return ''
  
  // 0. 正在保存/同步中 (中间状态)
  if (isSaving.value) {
    return 'status-syncing'
  }

  const currentHash = currentArticle.value.content
  const lastSyncedHash = originalContent.value
  // 使用 explicit isSynced 标记或 sha 存在性
  const isFromSyncSource = currentArticle.value.isSynced || !!currentArticle.value.sha
  const isSavedLocally = currentHash === localSavedContent.value
  const hasUnsavedChanges = currentHash !== localSavedContent.value
  const isNewArticle = !currentArticle.value.sha && !currentArticle.value.isSynced

  // 1. 已同步：来自同步源 且 内容未变 (或者是新建并推送成功的)
  // 注意：只要是同步源且内容一致，就是绿色，不管是否本地保存了一次(只要内容没变)
  if (isFromSyncSource && currentHash === lastSyncedHash) {
    return 'status-synced'
  }
  
  // 2. 新建文章：是新文章 且 未本地保存
  if (isNewArticle && !isSavedLocally) {
    return 'status-new'
  }

  // 3. 修改未保存：有未保存变更 且 未本地保存
  if (hasUnsavedChanges && !isSavedLocally) {
    return 'status-modified-unsaved'
  }

  // 4. 修改已保存：已本地保存 且 (未推送到GitHub 或 内容有变更)
  if (isSavedLocally && (currentHash !== lastSyncedHash || !isFromSyncSource)) {
    return 'status-modified-saved'
  }

  return ''
})

// --- 核心逻辑 ---

/**
 * 核心修复 1: 确保 getTargetDirPath 能够拿到准确的父级路径
 */
const getTargetDirPath = () => {
  // 1. 如果完全没选，默认根目录
  if (!selectedNode.value) return 'src/posts'

  // 2. 如果选中的是文件夹，直接返回该文件夹路径
  if (selectedNode.value.type === 'folder') {
    return selectedNode.value.path
  }

  // 3. 如果选中的是文件，提取该文件所在的目录
  const parts = selectedNode.value.path.split('/')
  parts.pop() // 移除文件名
  return parts.join('/')
}

// 1. 获取文章列表
const fetchList = async () => {
  isSideLoading.value = true
  try {
    // 此时 res 直接就是后端返回的数据，因为 client.ts 做了拦截处理
    const res = await articleApi.getList()
    treeData.value = res.data
  } finally {
    isSideLoading.value = false
  }
}

// 选中处理：记录当前节点位置
const handleSelectArticle = async (data: any) => {
  selectedNode.value = data
  if (data.type !== 'file') return

  isContentLoading.value = true
  try {
    const res = await articleApi.getDetail(data.path)
    // 修复：手动合并 SHA，因为后端将其放在顶层而非 data 中
    currentArticle.value = {
      ...res.data,
      sha: res.sha,
      isSynced: true // 明确标记为同步源文章
    }
    originalContent.value = res.data.content
    localSavedContent.value = res.data.content
  } catch (err) {
    ElMessage.error('读取内容失败')
  } finally {
    isContentLoading.value = false
  }
}


/**
 * 新建文章
 */
const handleNewArticle = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入文章标题', '新建文章', {
      inputPattern: /\S+/,
      inputErrorMessage: '标题不能为空'
    })

    if (name) {
      const parentPath = getTargetDirPath();
      const fileName = name.endsWith('.md') ? name : `${name}.md`;
      const fullPath = `${parentPath}/${fileName}`;

      // 1. 设置编辑器为待推送状态
      currentArticle.value = {
        path: fullPath,
        title: name,
        content: `---\ntitle: ${name}\ndate: ${new Date().toISOString().split('T')[0]}\n---\n\n开始创作...`,
        sha: "",
        isSynced: false
      }
      originalContent.value = ""
      localSavedContent.value = ""

      // 2. 构造虚拟节点（用于左侧显示）
      const newVirtualFile = {
        name: fileName,
        path: fullPath,
        type: 'file',
        isDraft: true,
        isVirtual: true // 绿色斜体+本地标识
      }

      // 3. 智能插入：如果 parentPath 是根部，直接在最外层找
      const success = insertNodeToTree(treeData.value, parentPath, newVirtualFile);

      // 如果递归没找到（比如在根目录下），则直接放最前面
      if (!success && (parentPath === 'src/posts' || parentPath === 'src')) {
        treeData.value.unshift(newVirtualFile);
      }

      ElMessage.success(`草稿已在目录 [${parentPath}] 下创建`);
    }
  } catch (e) { }
}

/**
 * 新建文件夹
 */
const handleNewFolder = async () => {
  try {
    const { value: folderName } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹')
    if (!folderName) return

    const parentPath = getTargetDirPath();
    const fullPath = `${parentPath}/${folderName}`;

    const newNode = {
      name: folderName,
      path: fullPath,
      type: 'folder',
      children: [],
      isVirtual: true
    }

    const success = insertNodeToTree(treeData.value, parentPath, newNode);
    if (!success) {
      treeData.value.unshift(newNode);
    }

    ElMessage.success('本地文件夹已就绪');
  } catch (e) { }
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
    const res = await articleApi.save({
      path: currentArticle.value.path,
      content: currentArticle.value.content,
      sha: currentArticle.value.sha,
      message: userInputMsg
    })

    if (res.code === 200) {
      ElMessage.success('同步成功')
      originalContent.value = currentArticle.value.content
      localSavedContent.value = currentArticle.value.content
      // 关键：同步成功后重新拉取列表，消除“本地”状态
      await fetchList()
      // 更新 SHA 和同步状态
      currentArticle.value.sha = res.sha
      currentArticle.value.isSynced = true
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
    await articleApi.rename(data.path, newPath, data.sha)
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
    await articleApi.delete(data.path, data.sha)
    ElMessage.success('文件已从 GitHub 删除')
    if (currentArticle.value?.path === data.path) currentArticle.value = null
    await fetchList()
  } catch (e) { } finally {
    isSideLoading.value = false
  }
}

// --- 辅助工具函数 ---

/**
 * 核心修复 2: 完善节点插入逻辑，并确保响应式生效
 */
const insertNodeToTree = (nodes: any[], targetPath: string, newNode: any): boolean => {
  // 处理特殊情况：直接在根列表插入 (对应 src/posts 或 src/drafts)
  // 如果 targetPath 就是当前层级某个节点的 path，说明找到了父文件夹
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];

    // 找到目标文件夹
    if (node.path === targetPath && node.type === 'folder') {
      if (!node.children) node.children = [];
      node.children.unshift(newNode);
      // 关键：强制触发 Vue 对 treeData 的深度更新
      treeData.value = [...treeData.value];
      return true;
    }

    // 递归查找子目录
    if (node.children && node.children.length > 0) {
      if (insertNodeToTree(node.children, targetPath, newNode)) return true;
    }
  }
  return false;
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
          
          /* 状态点样式系统 */
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: all 0.3s ease;

          &::before {
            content: '';
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            transition: all 0.3s ease;
          }

          /* 状态颜色定义 */
          &.status-synced::before { background-color: #008000; }           /* 已同步 - 深绿色 RGB(0,128,0) */
          &.status-syncing::before { background-color: #2196F3; }          /* 同步中 - 蓝色 */
          &.status-modified-unsaved::before { background-color: #795548; } /* 修改未保存 - 棕色 */
          &.status-modified-saved::before { background-color: #FFC107; }   /* 修改已保存 - 黄色 */
          &.status-new::before { background-color: #F44336; }              /* 新建文章 - 红色 */
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
