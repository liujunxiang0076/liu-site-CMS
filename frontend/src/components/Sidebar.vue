<template>
  <div class="sidebar" v-loading="loading">
    <div class="header">
      <h3>文章管理</h3>
      <el-dropdown trigger="click" @command="handleCommand">
        <button class="add-btn">
          <el-icon>
            <Plus />
          </el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="article">📄 新建文章 (.md)</el-dropdown-item>
            <el-dropdown-item command="folder">📁 新建文件夹</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="list-container">
      <el-tree :data="treeData" :props="{ label: 'name', children: 'children' }" highlight-current node-key="path"
        @node-click="handleNodeClick">
        <template v-slot="{ node, data }">
          <div class="tree-node-wrapper">
            <span class="icon">{{ data.type === 'folder' ? '📁' : '📄' }}</span>
            <span class="label">{{ node.label }}</span>
            <span v-if="data.type === 'file'" class="type-tag" :class="data.isDraft ? 'draft' : 'post'">
              {{ data.isDraft ? '草稿' : '发布' }}
            </span>
          </div>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue' // 确保安装了 @element-plus/icons-vue

defineProps<{
  treeData: any[]
  loading: boolean
}>()

// 新增指令：通知父组件是想建文件还是文件夹
const emit = defineEmits(['select', 'create-article', 'create-folder'])

const handleCommand = (command: string) => {
  if (command === 'article') {
    emit('create-article')
  } else if (command === 'folder') {
    emit('create-folder')
  }
}

const handleNodeClick = (data: any) => {
  if (data.type === 'file') {
    emit('select', data)
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  width: 280px; // 稍微加宽一点，给树形缩进留空间
  height: 100vh;
  border-right: 1px solid #eee;
  background: #fafafa;
  display: flex;
  flex-direction: column;

  .header {
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #eee;

    h3 {
      margin: 0;
      font-size: 18px;
      color: #333;
    }

    .add-btn {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: none;
      background: #42b883;
      color: white;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      transition: background 0.3s;

      &:hover {
        background: #33a06f;
      }
    }
  }

  .list-container {
    flex: 1;
    overflow-y: auto;
    padding: 10px 5px;

    // 深度覆盖 Element Plus 样式，使其匹配你的 UI
    :deep(.el-tree) {
      background: transparent;

      .el-tree-node__content {
        height: auto; // 允许内容撑开高度
        padding: 4px 0;
        border-radius: 6px;
        margin-bottom: 2px;

        &:hover {
          background-color: #f0f0f0;
        }
      }

      .el-tree-node.is-current>.el-tree-node__content {
        background-color: #e7f6ed !important;
        color: #42b883;
      }
    }

    .tree-node-wrapper {
      display: flex;
      align-items: center;
      font-size: 14px;
      width: 100%;
      overflow: hidden;

      .icon {
        margin-right: 8px;
        font-size: 14px;
      }

      .label {
        flex: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .type-tag {
        font-size: 10px;
        padding: 1px 4px;
        border-radius: 3px;
        margin-left: 8px;
        margin-right: 10px;
        color: white;
        transform: scale(0.9);

        &.post {
          background: #42b883;
        }

        &.draft {
          background: #fb7299;
        }
      }
    }
  }
}
</style>
