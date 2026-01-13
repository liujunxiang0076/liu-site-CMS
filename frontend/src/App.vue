<template>
  <div class="cms-layout">
    <Sidebar 
      :articles="articles" 
      :currentPath="currentArticle?.path"
      @select="loadArticle"
      @create="createNewArticle"
    />
    
    <div class="main-content">
      <Editor 
        v-if="currentArticle" 
        :articleData="currentArticle" 
        @refresh="fetchList"
      />
      <div v-else class="empty-state">
        <p>请选择或创建一篇文章开始编辑</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'

const articles = ref([])
const currentArticle = ref<any>(null)

const fetchList = async () => {
  const res = await axios.get('/api/articles')
  articles.value = res.data
}

const loadArticle = async (item: any) => {
  // 获取详情
  const res = await axios.get(`/api/article/detail?path=${item.path}`)
  currentArticle.value = {
    path: item.path,
    sha: res.data.sha,
    metadata: res.data.metadata,
    content: res.data.content
  }
}

const createNewArticle = () => {
  currentArticle.value = {
    path: '',
    metadata: { title: '未命名文章', date: new Date().toISOString().split('T')[0] },
    content: ''
  }
}

onMounted(fetchList)
</script>

<style lang="scss">
// frontend/src/App.vue
.cms-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #f0f2f5;

  // 侧边栏基础样式
  .sidebar-wrap {
    flex-shrink: 0; // 防止被挤压
    transition: width 0.3s ease;
    
    @media (max-width: 768px) {
      width: 60px; // 手机端自动变窄
      span.name { display: none; } // 隐藏文字只留图标
    }
  }

  .main-content {
    flex: 1;
    min-width: 0; // 解决 Flex 子元素溢出问题
    background: #fff;
    box-shadow: -2px 0 8px rgba(0,0,0,0.05);
  }
}
</style>
