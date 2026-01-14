<template>
  <div class="sidebar" :class="{ 'is-collapsed': isCollapsed }" v-loading="loading" @click="hideContextMenu">
    
    <div class="collapse-trigger" @click.stop="isCollapsed = !isCollapsed">
      <el-icon>
        <ArrowLeft v-if="!isCollapsed" />
        <ArrowRight v-else />
      </el-icon>
    </div>

    <div class="sidebar-content" v-show="!isCollapsed">
      <div class="header">
        <span class="title">文章管理</span>
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
        </div>
      </div>

      <div class="list-container">
        <el-tree 
          :data="treeData" 
          :props="{ label: 'name', children: 'children' }" 
          highlight-current 
          node-key="path"
          :indent="16" 
          @node-click="handleNodeClick" 
          @node-contextmenu="handleRightClick"
        >
          <template v-slot="{ node, data }">
            <div class="tree-node-wrapper" :class="{ 'is-virtual': data.isVirtual }">
              <template v-if="!data.isEditing">
                <span class="icon">{{ data.type === 'folder' ? '📁' : '📄' }}</span>
                <span class="label" :class="{ 'is-draft': data.isDraft }">{{ node.label }}</span>
                <span v-if="data.isModified" class="unsaved-dot"></span>
                <el-tag v-if="data.isVirtual" size="small" type="info" effect="plain" class="local-tag">本地</el-tag>
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
  ArrowLeft, ArrowRight // 新增图标
} from '@element-plus/icons-vue'

// --- 新增状态 ---
const isCollapsed = ref(false)

// 定义 Props
defineProps<{
  treeData: any[]
  loading: boolean
}>()

// 定义事件
const emit = defineEmits(['select', 'create-article', 'create-folder', 'refresh', 'rename', 'delete'])

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
  if (data.type === 'file') {
    emit('select', data)
  }
}

// 触发右键菜单
const handleRightClick = (event: MouseEvent, data: any) => {
  if (isCollapsed.value) return // 收缩状态不显示右键菜单
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
  border-right: 1px solid #e8e8e8;
  background: #ffffff; // 保持清爽白色
  display: flex;
  flex-direction: column;
  user-select: none;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1); // 平滑动画

  // 收缩状态样式
  &.is-collapsed {
    width: 0px; // 完全收起，如果想留个边可以设为 12px
    border-right: none;
    
    .sidebar-content {
      opacity: 0;
      pointer-events: none;
    }
    
    .collapse-trigger {
      right: -24px; // 按钮悬浮在侧边栏外
      border: 1px solid #e8e8e8;
      background: #fff;
    }
  }

  .sidebar-content {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 260px; // 固定宽度防止收缩时文字换行扭曲
    transition: opacity 0.2s;
  }

  // 控制按钮
  .collapse-trigger {
    position: absolute;
    right: -12px;
    top: 50%;
    transform: translateY(-50%);
    width: 24px;
    height: 24px;
    background: #f0f0f0;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 10;
    color: #909399;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: all 0.3s;

    &:hover {
      background: #42b883;
      color: #fff;
    }
  }

  /* ... 保持你原有的其他样式不变 ... */
  .header {
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f0f0f0;
    white-space: nowrap; // 防止标题换行
    
    .title {
      font-size: 13px;
      font-weight: 600;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .actions {
      display: flex;
      gap: 10px;

      .el-icon {
        font-size: 16px;
        color: #909399;
        cursor: pointer;
        transition: color 0.2s;

        &:hover {
          color: #42b883; // 悬浮变绿色
        }
      }
    }
  }

  .list-container {
    flex: 1;
    overflow-x: hidden; // 隐藏横向滚动条
    overflow-y: auto;
    padding: 8px 4px;

    :deep(.el-tree) {
      background: transparent;

      .el-tree-node__content {
        height: 32px; // 适当放宽行高，更符合网页端审美
        padding: 0 8px;
        border-radius: 4px;
        margin: 1px 4px;

        &:hover {
          background-color: #f5f7f9;
        }
      }

      .el-tree-node.is-current>.el-tree-node__content {
        background-color: #e7f6ed !important; // 选中的浅绿色
        color: #42b883;
        font-weight: 500;
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
        background: #42b883;
        border-radius: 50%;
        margin-left: 8px;
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
        color: #42b883; // 本地文件夹显示为主题绿色
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
