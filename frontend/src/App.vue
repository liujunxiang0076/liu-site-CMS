<template>
  <div class="cms-layout">
    <Sidebar :articles="articles" :currentPath="currentArticle?.path" @select="loadArticle"
      @create="createNewArticle" />

    <div class="main-content">
      <Editor v-if="currentArticle" :articleData="currentArticle" @refresh="fetchList" />
      <div v-else class="empty-state">
        <p>请选择或创建一篇文章开始编辑</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'

const currentArticle = ref<any>(null)

const articles = ref([]) // 确保初始化是一个空数组
const isLoading = ref(false)

const fetchList = async () => {
  isLoading.value = true // 开始加载
  try {
    const res = await axios.get('/api/articles')
    articles.value = res.data
  } catch (error) {
    console.error('获取列表失败', error)
  } finally {
    isLoading.value = false // 结束加载
  }
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
    path: '', // 路径为空代表新文章
    sha: '',  // 新文章没有 sha
    metadata: {
      title: '未命名文章',
      tags: [],
      categories: ['技术分享'],
      date: new Date().toISOString().split('T')[0], // 自动生成今天日期
      description: ''
    },
    content: ''
  }
}

// frontend/src/App.vue



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

      span.name {
        display: none;
      }

      // 隐藏文字只留图标
    }
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #fff;

    #vditor {
      border: none !important; // 去掉 Vditor 默认边框
      max-width: 900px; // 限制宽度，写作更舒适
      margin: 0 auto;
      width: 100%;
    }
  }
}
</style>
