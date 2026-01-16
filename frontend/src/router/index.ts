import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Login from '@/views/Login.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const tokenExpire = localStorage.getItem('token_expire')
  
  if (to.meta.requiresAuth) {
    if (!token) {
      next('/login')
    } else {
      // Check expiry
      if (tokenExpire && Date.now() > parseInt(tokenExpire)) {
        localStorage.removeItem('token')
        localStorage.removeItem('token_expire')
        next('/login')
      } else {
        next()
      }
    }
  } else {
    if (to.path === '/login' && token) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
