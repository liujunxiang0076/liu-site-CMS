<template>
  <div class="cms-layout">
    <Sidebar ref="sidebarRef" :tree-data="treeData" :loading="isSideLoading" @select="handleSelectArticle"
      @create-article="handleNewArticle" @create-folder="handleNewFolder" @refresh="fetchList" @rename="handleRename"
      @delete="handleDelete" />
    <main class="main-content" v-loading="isContentLoading">
      <div v-if="currentArticle" class="editor-container">
        <div class="editor-header">
          <span class="path-tag" :class="articleStatus">{{ currentArticle.path }}</span>
          <div class="header-actions">
            <span v-if="autoSaveStatus" class="autosave-status">{{ autoSaveStatus }}</span>
            <el-button type="primary" :loading="isSaving" @click="handleSave" :disabled="!isModified">
              {{ isSaving ? '同步中...' : '推送至 GitHub' }}
            </el-button>
          </div>
        </div>

        <MdEditor v-model="currentArticle.content" editor-id="my-editor" class="pro-editor"
          placeholder="开始你的 Typora 式体验..." :no-front-matter="true" 
          @onSave="handleSave" @onUploadImg="handleUploadImg" />
      </div>

      <div v-else class="empty-state">
        <el-empty description="点选左侧文章开启编辑" />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from './components/Sidebar.vue'
import { MdEditor } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';
import { articleApi } from '@/api/article'
import { v4 as uuidv4 } from 'uuid';
import * as storage from '@/utils/storage';
import { resolveTargetDir } from '@/utils/path';
import { getNextSequence, sortNodes } from '@/utils/fileNaming';
import { getChildrenByPath, findNodeByPath, removeNodeFromTree } from '@/utils/treeHelper';


const sidebarRef = ref()

// --- 状态定义 ---
const treeData = ref<any[]>([])
const isSideLoading = ref(false)
const isContentLoading = ref(false)
const isSaving = ref(false)
const originalContent = ref('')
const localSavedContent = ref('') // 新增：本地保存的内容快照
const selectedNode = ref<any>(null) // 统一记录当前选中的节点
const autoSaveStatus = ref('') // 自动保存状态提示

const currentArticle = ref<{
  id?: string; // 本地文章ID
  path: string;
  title: string;
  content: string;
  sha: string;
  isSynced?: boolean; // 新增：标识是否来自同步源
  isLocal?: boolean; // 新增：标识是否为纯本地文章
} | null>(null)

// 自动保存逻辑
let autoSaveTimer: any = null

// 监听内容变化进行自动保存
watch(() => currentArticle.value?.content, (newVal, oldVal) => {
  if (!currentArticle.value || newVal === oldVal) return
  
  // 清除旧定时器
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  
  autoSaveStatus.value = '输入中...'
  
  // 防抖 1秒 (虽然要求30s间隔，但实时防抖体验更好，只要不频繁IO即可)
  autoSaveTimer = setTimeout(async () => {
    if (currentArticle.value) {
      try {
        // 如果是本地新建的文章
        if (currentArticle.value.isLocal && currentArticle.value.id) {
          await storage.saveLocalArticle({
            id: currentArticle.value.id,
            title: currentArticle.value.title,
            content: newVal || '',
            path: currentArticle.value.path,
            updatedAt: Date.now(),
            isSynced: false
          });
        } else {
           // 对于远程文章，也可以考虑保存到本地草稿，这里暂且复用之前的 localStorage 逻辑作为简单备份
           // 或者也可以升级为 storage 存储
           const key = 'cms_draft_' + currentArticle.value.path
           localStorage.setItem(key, newVal || '')
        }
        autoSaveStatus.value = '已自动保存到本地'
        setTimeout(() => { autoSaveStatus.value = '' }, 2000)
      } catch (e: any) {
        autoSaveStatus.value = '自动保存失败'
        ElMessage.error(e.message || '本地存储失败');
      }
    }
  }, 1000)
})

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
 * 检查文件名是否重复
 */
const checkDuplicateName = (parentPath: string, fileName: string): boolean => {
  // 递归查找目标文件夹节点
  const findFolder = (nodes: any[]): any[] | null => {
    for (const node of nodes) {
      if (node.path === parentPath && node.type === 'folder') {
        return node.children || []
      }
      if (node.children) {
        const res = findFolder(node.children)
        if (res) return res
      }
    }
    // 特殊情况：如果是根目录 src/posts，可能直接就是 treeData
    if (parentPath === 'src/posts' || parentPath === 'src') return nodes
    return null
  }

  const siblings = findFolder(treeData.value)
  if (!siblings) return false

  return siblings.some((node: any) => node.name === fileName)
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
    // 优先处理本地文章
    // 增加 isVirtual 判断作为兜底，防止 isLocal 属性丢失
    if ((data.isLocal || data.isVirtual) && data.type === 'file') {
      let localArticle = null;
      
      // 1. 尝试通过 ID 获取
      if (data.id) {
        localArticle = await storage.getLocalArticle(data.id)
      }
      
      // 2. 如果 ID 失效或未找到，尝试通过路径匹配 (兜底策略)
      if (!localArticle) {
        const allLocal = await storage.getAllLocalArticles()
        localArticle = allLocal.find(a => a.path === data.path) || null
        
        // 如果通过路径找到了，回填 ID 到节点，方便下次使用
        if (localArticle) {
          data.id = localArticle.id
          data.isLocal = true
        }
      }

      if (localArticle) {
        currentArticle.value = {
          id: localArticle.id,
          path: localArticle.path,
          title: localArticle.title,
          content: localArticle.content,
          sha: '',
          isSynced: false,
          isLocal: true
        }
        originalContent.value = localArticle.content
        localSavedContent.value = localArticle.content
        return // 成功读取本地文章，直接返回
      }
      
      console.warn('Local article not found in storage, trying remote...', data)
    }

    // 远程文章
    const res = await articleApi.getDetail(data.path)
    // 修复：手动合并 SHA，因为后端将其放在顶层而非 data 中
    currentArticle.value = {
      ...res.data,
      sha: res.sha ?? '',
      isSynced: true, // 明确标记为同步源文章
      isLocal: false
    }
    
    // 检查是否有未保存的草稿 (localStorage)
    const draftKey = 'cms_draft_' + data.path
    const draftContent = localStorage.getItem(draftKey)
    if (draftContent && draftContent !== res.data.content) {
      try {
        await ElMessageBox.confirm('检测到本地有未保存的草稿，是否恢复？', '恢复草稿', {
          confirmButtonText: '恢复草稿',
          cancelButtonText: '丢弃',
          type: 'info'
        })
        currentArticle.value.content = draftContent
        ElMessage.success('已恢复本地草稿')
      } catch {
        // 丢弃草稿
        localStorage.removeItem(draftKey)
      }
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
 * 图片上传处理
 */
const handleUploadImg = async (files: File[], callback: (urls: string[]) => void) => {
  const res = await Promise.all(
    files.map(async (file) => {
      // 1. 前端基础校验
      if (file.size > 5 * 1024 * 1024) {
        ElMessage.warning(`文件 ${file.name} 超过 5MB，已跳过`)
        return null
      }
      
      const form = new FormData()
      form.append('file', file)

      try {
        const { data } = await articleApi.uploadImage(form)
        return data.url
      } catch (error) {
        ElMessage.error(`图片 ${file.name} 上传失败`)
        return null
      }
    })
  )

  // 过滤失败的请求
  const urls = res.filter((url): url is string => !!url)
  if (urls.length > 0) {
    callback(urls)
    ElMessage.success(`成功上传 ${urls.length} 张图片`)
  }
}


/**
 * 新建文章
 */
const handleNewArticle = async () => {
  try {
    const parentPath = resolveTargetDir(selectedNode.value);
    
    // 1. 计算自动序号
    const siblings = getChildrenByPath(treeData.value, parentPath);
    const existingNames = siblings.map((n: any) => n.name);
    const nextSeq = getNextSequence(existingNames);
    
    if (nextSeq === null) {
      ElMessage.warning('该目录下文件序号已达上限 (99)，无法自动生成');
      return;
    }

    // 2. 弹出输入框，预填序号
    const { value: name } = await ElMessageBox.prompt('请输入文章标题', '新建文章', {
      inputPattern: /\S+/,
      inputErrorMessage: '标题不能为空',
      inputValue: `${nextSeq}_`
    })

    if (name) {
      const fileName = name.endsWith('.md') ? name : `${name}.md`;
      const fullPath = `${parentPath}/${fileName}`;
      
      // 检查重名 (使用现有列表)
      if (existingNames.includes(fileName)) {
        ElMessage.error('该目录下已存在同名文件');
        return;
      }

      const newId = uuidv4(); // 生成唯一ID

      // 3. 设置编辑器为待推送状态
      currentArticle.value = {
        id: newId,
        path: fullPath,
        title: name.replace(/\.md$/, ''),
        content: `---\ntitle: ${name.replace(/\.md$/, '')}\ntags: []\ncategories: []\ndate: ${new Date().toISOString().split('T')[0]}\ndescription: \ncover: \n---\n\n开始创作...`,
        sha: "",
        isSynced: false,
        isLocal: true
      }
      originalContent.value = ""
      localSavedContent.value = ""

      // 立即保存到本地存储
      await storage.saveLocalArticle({
        id: newId,
        title: currentArticle.value.title,
        content: currentArticle.value.content,
        path: fullPath,
        updatedAt: Date.now(),
        isSynced: false
      });

      // 4. 构造虚拟节点
      const newVirtualFile = {
        id: newId,
        name: fileName,
        path: fullPath,
        type: 'file',
        isDraft: true,
        isVirtual: true,
        isLocal: true
      }

      // 5. 插入并排序
      const parentNode = findNodeByPath(treeData.value, parentPath);
      
      if (Array.isArray(parentNode)) {
         // 根目录
         parentNode.push(newVirtualFile);
         treeData.value = sortNodes(parentNode);
      } else if (parentNode) {
         // 文件夹
         if (!parentNode.children) parentNode.children = [];
         parentNode.children.push(newVirtualFile);
         parentNode.children = sortNodes(parentNode.children);
      } else {
         // 兜底：如果找不到父节点（理论上不应发生），回退到旧逻辑
         treeData.value.unshift(newVirtualFile);
      }
      
      // 展开父文件夹
      if (sidebarRef.value) {
        sidebarRef.value.expandNode(parentPath)
      }

      ElMessage.success(`草稿已在目录 [${parentPath}] 下创建`);
    }
  } catch (e) { 
    if (e !== 'cancel') console.error(e);
  }
}

/**
 * 新建文件夹
 */
const handleNewFolder = async () => {
  try {
    const { value: folderName } = await ElMessageBox.prompt('请输入文件夹名称', '新建文件夹')
    if (!folderName) return

    const parentPath = resolveTargetDir(selectedNode.value);
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
    
    // 展开父文件夹
    if (sidebarRef.value) {
      sidebarRef.value.expandNode(parentPath)
    }

    ElMessage.success('本地文件夹已就绪');
  } catch (e) { }
}

// 6. 保存/推送文章
const handleSave = async () => {
  if (!currentArticle.value || isSaving.value) return

  // 1. 数据验证
  const content = currentArticle.value.content || ''
  if (!content.trim()) {
    ElMessage.warning('文章内容不能为空')
    return
  }
  
  // 简单检查 Frontmatter (可选，根据严格程度)
  const hasFrontmatter = content.startsWith('---')
  const hasTitle = /^title:\s+.+/m.test(content)
  const hasCategory = /^categories:\s*/m.test(content)

  if (!hasFrontmatter || !hasTitle || !hasCategory) {
    const missing = []
    if (!hasFrontmatter) missing.push('Frontmatter 头部')
    if (!hasTitle) missing.push('文章标题 (title)')
    if (!hasCategory) missing.push('文章分类 (categories)')

    try {
      await ElMessageBox.confirm(
        `检测到以下关键信息缺失：${missing.join('、')}。\n这可能导致博客列表渲染异常。是否强制保存？`,
        '格式警告',
        {
          confirmButtonText: '强制保存',
          cancelButtonText: '返回修改',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }

  try {
    const { value: userInputMsg } = await ElMessageBox.prompt(
      '请输入推送备注', '确认推送至 GitHub', {
      confirmButtonText: '确定推送',
      cancelButtonText: '取消',
      inputPlaceholder: '系统将自动生成默认备注...'
    }
    )

    isSaving.value = true

    // 冲突检测与 SHA 获取 (针对本地文章)
    let finalSha = currentArticle.value.sha
    if (currentArticle.value.isLocal) {
      // 尝试获取远程文件信息，看是否已存在
      try {
        const remoteRes = await articleApi.getDetail(currentArticle.value.path, { skipErrorHandle: true })
        // 如果能获取到，说明远程已存在
        try {
           await ElMessageBox.confirm(
             `云端已存在同名文件${remoteRes.sha ? ` (SHA: ${remoteRes.sha.substring(0,7)})` : ''}，继续保存将覆盖云端内容。`,
             '版本冲突',
             {
               confirmButtonText: '覆盖保存',
               cancelButtonText: '取消',
               type: 'warning'
             }
           )
           finalSha = remoteRes.sha ?? '' // 使用远程 SHA 进行覆盖
        } catch {
           isSaving.value = false
           return // 用户取消
        }
      } catch (e) {
        // 获取失败通常说明文件不存在（404），这是正常的“新建”流程
        // 忽略错误，finalSha 保持为空即可
      }
    }

    const res = await articleApi.save({
      path: currentArticle.value.path,
      content: currentArticle.value.content,
      sha: finalSha,
      message: userInputMsg
    })

    if (res.code === 200) {
      ElMessage.success('同步成功')
      
      // 如果是本地文章，同步成功后删除本地存储
      if (currentArticle.value.isLocal && currentArticle.value.id) {
        await storage.removeLocalArticle(currentArticle.value.id)
      } else {
        // 清除旧的 localStorage 草稿
        const draftKey = 'cms_draft_' + currentArticle.value.path
        localStorage.removeItem(draftKey)
      }
      
      originalContent.value = currentArticle.value.content
      localSavedContent.value = currentArticle.value.content
      autoSaveStatus.value = ''
      
      // 关键：同步成功后重新拉取列表，消除“本地”状态
      try {
        await fetchList()
      } catch (listErr) {
        console.warn('列表刷新失败，但这不影响文章保存:', listErr);
      }
      
      // 更新 SHA 和同步状态
      currentArticle.value.sha = res.sha ?? ''
      currentArticle.value.isSynced = true
      currentArticle.value.isLocal = false
      currentArticle.value.id = undefined
    }
  } catch (err: any) {
    if (err !== 'cancel') {
      // 优化错误提示
      const errorMsg = err.response?.data?.msg || err.message || '保存失败'
      ElMessage.error(errorMsg)
    }
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
    
    // 分支处理：本地文章 vs 远程文章
    if (data.isLocal && data.id) {
      isSideLoading.value = true
      await storage.removeLocalArticle(data.id)
      ElMessage.success('草稿已删除')
    } else if (data.isVirtual) {
      // 纯虚拟节点 (例如新建的文件夹)，无需后端交互，直接移除
      ElMessage.success('已删除')
    } else {
      let userInputMsg = undefined;

      // 只有远程文件需要输入备注，文件夹不需要
      if (data.type === 'file') {
        const { value } = await ElMessageBox.prompt(
          '请输入Git提交备注', '确认删除', {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          inputPlaceholder: `Delete ${data.name}`
        })
        userInputMsg = value;
      }
      
      isSideLoading.value = true
      await articleApi.delete(data.path, data.sha, userInputMsg)
      ElMessage.success(data.type === 'folder' ? '文件夹已删除' : '文件已从 GitHub 删除')
    }
    
    // 核心修改：手动从树中移除节点，而不是重新拉取列表
    // 这样既能保持文件夹展开状态，又能避免本地草稿丢失
    removeNodeFromTree(treeData.value, { id: data.id, path: data.path });
    
    if (currentArticle.value?.path === data.path) currentArticle.value = null
    // await fetchList() // 移除此行，避免全量刷新
  } catch (e) { 
    if (e !== 'cancel') console.error(e)
  } finally {
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

        .header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .autosave-status {
            font-size: 12px;
            color: #999;
          }
        }

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
