<template>
  <div class="login-container">
    <div class="login-box">
      <div class="logo-area">
        <h1>CMS Login</h1>
      </div>
      <el-form :model="loginForm" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码" 
            show-password
            size="large"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="login-btn" size="large">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="footer">
        <p>Secure System</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const loginForm = ref({
  password: ''
})

const handleLogin = async () => {
  if (!loginForm.value.password) {
    ElMessage.warning('请输入密码')
    return
  }

  loading.value = true
  try {
    // Assuming axios is configured with base URL in a global file, 
    // but here I'll use direct path or import the client if available.
    // Better to use the configured client but for now I'll use relative path which proxies to backend
    // Checking client.ts might be better.
    const res = await axios.post('/api/login', { password: loginForm.value.password })
    
    if (res.data.access_token) {
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('token_expire', (Date.now() + 12 * 60 * 60 * 1000).toString()) // Client side check
      ElMessage.success('登录成功')
      router.push('/')
    } else {
       ElMessage.error('登录失败')
    }
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      ElMessage.error('密码错误')
    } else {
      ElMessage.error('登录服务异常')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
  
  .login-box {
    width: 100%;
    max-width: 400px;
    padding: 40px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    
    .logo-area {
      text-align: center;
      margin-bottom: 30px;
      h1 {
        font-size: 24px;
        color: #333;
        font-weight: 600;
      }
    }
    
    .login-btn {
      width: 100%;
    }
    
    .footer {
      margin-top: 20px;
      text-align: center;
      color: #999;
      font-size: 12px;
    }
  }
}

@media screen and (max-width: 768px) {
  .login-box {
    width: 90%;
    padding: 20px;
  }
}
</style>
