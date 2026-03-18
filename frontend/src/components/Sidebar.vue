<template>
  <div class="sidebar" :class="{ 'is-collapsed': isCollapsed }" v-loading="loading" @click="hideContextMenu">
    
    <div class="collapse-trigger" @click.stop="isCollapsed = !isCollapsed">
      <el-icon>
        <ArrowLeft v-if="!isCollapsed" />
        <ArrowRight v-else />
      </el-icon>
    </div>

    <div class="sidebar-content" v-show="!isCollapsed" @click="handleBackgroundClick">
      <div class="header">
        <span class="title">
          文章管理
          <el-tooltip content="数据来自本地缓存" placement="top" v-if="isFromCache">
             <span class="cache-dot"></span>
          </el-tooltip>
        </span>
        <div class="actions">
          <el-icon @click="emit('create-article')" title="新建文章">
            <DocumentAdd />
          </el-icon>
          <el-icon @click="emit('create-folder')" title="新建文件夹">
            <FolderAdd />
          </el-icon>
          <el-icon @click="emit('refresh')" title="刷新列表">
            <Refresh />
          </el-icon>
          <el-icon @click="emit('settings')" title="设置">
            <Setting />
          </el-icon>
          <el-icon @click="emit('logout')" title="退出登录" class="logout-icon">
            <SwitchButton />
          </el-icon>
        </div>
      </div>

      <div class="list-container">
        <el-tree 
          ref="treeRef"
          :data="treeData" 
          :props="{ label: 'name', children: 'children' }" 
          highlight-current 
          node-key="path"
          :indent="16" 
          @node-click="handleNodeClick" 
          @node-contextmenu="handleRightClick"
        >
          <template v-slot="{ node, data }">
            <div class="tree-node-wrapper" :class="{ 'is-virtual': data.isVirtual, 'is-group': data.group }">
              <template v-if="!data.isEditing">
                <span class="icon">{{ data.type === 'folder' ? '📁' : '📄' }}</span>
                <span class="label" :class="{ 'is-draft': data.isDraft }">{{ node.label }}</span>
                <span v-if="data.isModified" class="unsaved-dot"></span>
                <el-tag v-if="data.isVirtual" size="small" type="info" effect="plain" class="local-tag">本地</el-tag>
                <el-tag
                  v-else-if="data.type === 'file'"
                  size="small"
                  :type="data.isDraft ? 'warning' : 'success'"
                  effect="plain"
                  class="status-tag"
                >
                  {{ data.isDraft ? '草稿' : '已发布' }}
                </el-tag>
              </template>

              <template v-else>
                <span class="icon">{{ data.type === 'folder' ? '📁' : '📄' }}</span>
                <el-input 
                  v-model="data.tempName" 
                  size="small" 
                  class="inline-input" 
                  @blur="handleNameConfirm(data)"
                  @keyup.enter="handleNameConfirm(data)" 
                  v-focus 
                />
              </template>
            </div>
          </template>
        </el-tree>
      </div>
    </div>

    <div v-if="menu.visible" :style="{ top: menu.y + 'px', left: menu.x + 'px' }" class="context-menu">
      <div class="menu-item" @click="handleMenuAction('rename')">
        <el-icon><Edit /></el-icon> 重命名
      </div>
      <div class="menu-item delete" @click="handleMenuAction('delete')">
        <el-icon><Delete /></el-icon> 删除
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { 
  DocumentAdd, FolderAdd, Refresh, Edit, Delete, 
  ArrowLeft, ArrowRight, Setting, SwitchButton // 新增图标
} from '@element-plus/icons-vue'

// --- 新增状态 ---
const isCollapsed = ref(false)

// 定义 Props
defineProps<{
  treeData: any[]
  loading: boolean
  isFromCache?: boolean
}>()

// 定义事件
const emit = defineEmits(['select', 'create-article', 'create-folder', 'refresh', 'rename', 'delete', 'clear-selection', 'settings', 'logout'])

const treeRef = ref()
defineExpose({
  expandNode: (key: string) => {
    if (treeRef.value) {
      const node = treeRef.value.getNode(key)
      if (node) {
        node.expanded = true
      }
    }
  },
  // 新增：取消选中方法
  setCurrentKey: (key: string | null) => {
    if (treeRef.value) {
      treeRef.value.setCurrentKey(key)
    }
  }
})

// 右键菜单状态
const menu = reactive({
  visible: false,
  x: 0,
  y: 0,
  data: null as any
})

// 自定义指令：自动聚焦
const vFocus = {
  mounted: (el: HTMLElement) => {
    const input = el.querySelector('input')
    if (input) input.focus()
  }
}

// 处理节点点击
const handleNodeClick = (data: any) => {
  menu.visible = false
  // 无论是文件还是文件夹，都触发 select 事件，以便父组件知道当前选中项
  emit('select', data)
}

// 处理背景点击（空白处）
const handleBackgroundClick = (event: MouseEvent) => {
  // 确保点击的不是树节点本身（通过事件冒泡机制，如果点击的是树节点，el-tree 会先处理）
  // 检查点击的目标是否是树节点的内部元素
  const target = event.target as HTMLElement
  if (target.closest('.el-tree-node__content')) return
  
  // 如果点击的是 header 区域（例如操作按钮），也不要清除选中状态
  if (target.closest('.header')) return

  if (treeRef.value) {
    treeRef.value.setCurrentKey(null) // 清除高亮
  }
  emit('clear-selection') // 通知父组件清除选中状态
}

// 触发右键菜单
const handleRightClick = (event: MouseEvent, data: any) => {
  if (isCollapsed.value) return // 收缩状态不显示右键菜单
  if (data?.group) return // 分组节点不允许重命名/删除
  event.preventDefault()
  menu.visible = true
  menu.x = event.clientX
  menu.y = event.clientY
  menu.data = data
}

const hideContextMenu = () => {
  menu.visible = false
}

// 处理菜单动作
const handleMenuAction = (action: 'rename' | 'delete') => {
  if (menu.data?.group) {
    menu.visible = false
    return
  }
  if (action === 'rename') {
    menu.data.isEditing = true
    menu.data.tempName = menu.data.name
  } else {
    emit('delete', menu.data)
  }
  menu.visible = false
}

// 确认命名 (回车或失焦)
const handleNameConfirm = (data: any) => {
  if (!data.isEditing) return
  data.isEditing = false
  if (data.tempName && data.tempName !== data.name) {
    emit('rename', { data, newName: data.tempName })
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  position: relative;
  width: 260px;
  height: 100vh;
  border-right: 1px solid #e4e8ee;
  background: #f7f8fc;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  .sidebar-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  // 收缩状态样式
  &.is-collapsed {
    width: 0px; // 完全收起，如果想留个边可以设为 12px
    border-right: none;
    
    .sidebar-content {
      opacity: 0;
      pointer-events: none;
    }
    
    .collapse-trigger {
      /* 自动贴边：向左收回一半多，只露个边 */
      right: -14px; 
      opacity: 0.3; // 贴边时保持高透明
      background: #f7f8fc;
      border: 1px solid #dcdfe6;
      color: #909399;

      &:hover {
        opacity: 1;
        right: -12px; // 鼠标移入稍微弹出来一点
        background: #42b883;
        color: #fff;
        border-color: #42b883;
        /* 增加延迟防抖：移入立即显示，移出延迟消失 */
        transition: all 0.2s ease, opacity 0.2s ease;
      }
    }
  }

  // --- 通用触发器样式 ---
  .collapse-trigger {
    position: absolute;
    top: 50%;
    right: -12px; // 展开态默认居中边框
    transform: translateY(-50%);
    width: 24px;
    height: 24px;
    background: #f0f0f0;
    border-radius: 50%; // 保持圆形
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 100;
    color: #909399;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    /* 核心：消失时增加 0.4s 延迟，防止鼠标滑过边缘时的“抖动” */
    transition: all 0.2s ease, opacity 0.3s ease 0.4s; 

    // 扩大交互热区：防止鼠标精准度要求过高导致的抖动
    &::before {
      content: '';
      position: absolute;
      width: 40px; // 热区比按钮大
      height: 60px;
      left: -10px;
      top: -18px;
      background: transparent;
    }

    &:hover {
      background: #42b883;
      color: #fff;
    }
  }

  .header {
    padding: 14px 16px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #e8ecf2;
    white-space: nowrap;
    background: linear-gradient(180deg, #ffffff 0%, #f7f8fc 100%);
    
    .title {
      font-size: 12px;
      font-weight: 700;
      color: #8a94a6;
      text-transform: uppercase;
      letter-spacing: 1px;
      display: flex;
      align-items: center;
      gap: 6px;

      .cache-dot {
        width: 6px;
        height: 6px;
        background-color: #e6a23c;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2);
      }
    }

    .actions {
      display: flex;
      gap: 2px;

      .el-icon {
        font-size: 15px;
        color: #b0bac9;
        cursor: pointer;
        padding: 5px;
        border-radius: 6px;
        transition: all 0.2s;

        &:hover {
          color: #4a7ee5;
          background: rgba(74, 126, 229, 0.08);
        }
      }

      .logout-icon:hover {
        color: #f56c6c;
        background: rgba(245, 108, 108, 0.08);
      }
    }
  }

  .list-container {
    flex: 1;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 8px 6px;

    &::-webkit-scrollbar {
      width: 4px;
    }
    &::-webkit-scrollbar-thumb {
      background: #dce0ea;
      border-radius: 4px;
    }

    :deep(.el-tree) {
      background: transparent;

      .el-tree-node__content {
        height: 34px;
        padding: 0 8px;
        border-radius: 6px;
        margin: 1px 2px;

        &:hover {
          background-color: #eef1f8;
        }
      }

      .el-tree-node.is-current>.el-tree-node__content {
        background: linear-gradient(135deg, #eef4ff 0%, #e8f0fe 100%) !important;
        color: #4a7ee5;
        font-weight: 600;
        box-shadow: 0 1px 4px rgba(74, 126, 229, 0.12);
      }
    }

    .tree-node-wrapper {
      display: flex;
      align-items: center;
      width: 100%;
      font-size: 14px;

      .icon {
        margin-right: 8px;
        font-size: 14px;
      }

      .label {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;

        &.is-draft {
          color: #909399;
          font-style: italic;
        }
      }

      .unsaved-dot {
        width: 6px;
        height: 6px;
        background: #f5a623;
        border-radius: 50%;
        margin-left: 8px;
        box-shadow: 0 0 0 2px rgba(245, 166, 35, 0.2);
      }

      .inline-input {
        flex: 1;

        :deep(.el-input__inner) {
          height: 22px;
          line-height: 22px;
          padding: 0 4px;
          font-size: 13px;
          border-radius: 2px;
        }
      }

      &.is-virtual {
        color: #4a7ee5; // 本地文件夹显示为主题绿色
        font-style: italic; // 斜体表示“未持久化”

        .label {
          opacity: 0.8;
        }
      }

      .local-tag {
        margin-left: 8px;
        height: 16px;
        line-height: 14px;
        padding: 0 4px;
        font-size: 10px;
        transform: scale(0.8);
      }

      .status-tag {
        margin-left: 8px;
        height: 16px;
        line-height: 14px;
        padding: 0 4px;
        font-size: 10px;
        transform: scale(0.8);
      }

      &.is-group {
        .label {
          font-weight: 700;
          color: #4a7ee5;
        }
      }
    }
  }

  /* 右键菜单：Element Plus 简洁风格 */
  .context-menu {
    position: fixed;
    z-index: 2000;
    background: #fff;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 5px 0;
    min-width: 120px;

    .menu-item {
      padding: 8px 16px;
      font-size: 13px;
      color: #606266;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;

      &:hover {
        background-color: #f5f7fa;
        color: #42b883;
      }

      &.delete {
        color: #f56c6c;

        &:hover {
          background-color: #fef0f0;
        }
      }
    }
  }
}
</style>
