<template>
  <div class="sidebar">
    <div class="header">
      <h3>文章管理</h3>
      <button @click="$emit('create')" class="add-btn">+</button>
    </div>
    
    <div class="list-container">
      <div 
        v-for="item in articles" 
        :key="item.path"
        :class="['article-item', { active: currentPath === item.path }]"
        @click="$emit('select', item)"
      >
        <span :class="['type-tag', item.type]">{{ item.type === 'draft' ? '草' : '文' }}</span>
        <span class="name">{{ item.name.replace('.md', '') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 自动导入插件会处理 ref, onMounted
import axios from 'axios'

defineProps<{
  currentPath?: string
  articles: any[]
}>()

defineEmits(['select', 'create'])
</script>

<style lang="scss" scoped>
.sidebar {
  width: 260px;
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
    
    .add-btn {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: none;
      background: #42b883;
      color: white;
      cursor: pointer;
      &:hover { background: #33a06f; }
    }
  }

  .list-container {
    flex: 1;
    overflow-y: auto;
    padding: 10px;

    .article-item {
      padding: 12px 15px;
      margin-bottom: 5px;
      border-radius: 6px;
      cursor: pointer;
      display: flex;
      align-items: center;
      transition: all 0.2s;
      font-size: 14px;

      &:hover { background: #f0f0f0; }
      &.active {
        background: #e7f6ed;
        color: #42b883;
        font-weight: bold;
      }

      .type-tag {
        font-size: 10px;
        padding: 2px 4px;
        border-radius: 3px;
        margin-right: 10px;
        color: white;
        &.post { background: #42b883; }
        &.draft { background: #fb7299; }
      }

      .name {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}
</style>
