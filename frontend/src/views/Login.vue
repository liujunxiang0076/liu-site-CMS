<template>
  <div class="login-container">
    <!-- 动态背景装饰 -->
    <div class="bg-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-icon">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="36" height="36" rx="10" fill="url(#logoGrad)"/>
            <path d="M10 18L16 24L26 12" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="logoGrad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                <stop stop-color="#667eea"/>
                <stop offset="1" stop-color="#764ba2"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="title">内容管理系统</h1>
        <p class="subtitle">Content Management System</p>
      </div>

      <!-- 登录表单 -->
      <el-form :model="loginForm" @submit.prevent="handleLogin" class="login-form">
        <el-form-item class="form-item">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入管理密码"
            show-password
            size="large"
            class="password-input"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon class="input-icon"><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item class="form-item submit-item">
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            class="login-btn"
            size="large"
          >
            <span v-if="!loading" class="btn-text">
              <el-icon class="btn-icon"><Right /></el-icon>
              登&nbsp;&nbsp;录
            </span>
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 底部 -->
      <div class="footer">
        <div class="security-badge">
          <el-icon><CircleCheckFilled /></el-icon>
          <span>安全加密连接</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, Right, CircleCheckFilled } from '@element-plus/icons-vue'
import apiClient from '../api/client'

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
    const res = await apiClient.post<any, any>('/login', { password: loginForm.value.password })

    if (res.data?.access_token) {
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('token_expire', (Date.now() + 12 * 60 * 60 * 1000).toString())
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error('登录失败')
    }
  } catch (err: any) {
    const msg = err?.message || '登录服务异常'
    if (msg.includes('密码错误') || msg.includes('Unauthorized')) {
      ElMessage.error('密码错误')
    } else {
      ElMessage.error(msg)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* 动态光晕背景 */
.bg-orbs {
  position: absolute;
  inset: 0;
  pointer-events: none;

  .orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.5;
    animation: float 8s ease-in-out infinite;
  }

  .orb-1 {
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, #667eea 0%, transparent 70%);
    top: -100px;
    left: -100px;
    animation-delay: 0s;
  }

  .orb-2 {
    width: 350px;
    height: 350px;
    background: radial-gradient(circle, #764ba2 0%, transparent 70%);
    bottom: -80px;
    right: -80px;
    animation-delay: -3s;
  }

  .orb-3 {
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, #f093fb 0%, transparent 70%);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation-delay: -6s;
    opacity: 0.2;
  }
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-30px) scale(1.05); }
}

/* 登录卡片 */
.login-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: 48px 40px 36px;
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 1px 0 rgba(255, 255, 255, 0.1) inset;
  animation: slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Logo 区域 */
.logo-area {
  text-align: center;
  margin-bottom: 36px;

  .logo-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(102, 126, 234, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 32px rgba(102, 126, 234, 0.5);
    }
  }

  .title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 6px;
    letter-spacing: 0.5px;
  }

  .subtitle {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.45);
    margin: 0;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
}

/* 表单 */
.login-form {
  .form-item {
    margin-bottom: 16px;

    :deep(.el-form-item__content) {
      line-height: normal;
    }
  }

  .submit-item {
    margin-top: 24px;
    margin-bottom: 0;
  }
}

/* 输入框样式覆盖 */
.password-input {
  :deep(.el-input__wrapper) {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    box-shadow: none !important;
    padding: 0 16px;
    transition: all 0.3s ease;

    &:hover {
      border-color: rgba(255, 255, 255, 0.25);
      background: rgba(255, 255, 255, 0.09);
    }

    &.is-focus {
      border-color: #667eea;
      background: rgba(102, 126, 234, 0.08);
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
    }
  }

  :deep(.el-input__inner) {
    color: #ffffff;
    font-size: 15px;
    height: 48px;

    &::placeholder {
      color: rgba(255, 255, 255, 0.3);
    }
  }

  :deep(.el-input__prefix) {
    color: rgba(255, 255, 255, 0.4);
  }

  :deep(.el-input__suffix) {
    color: rgba(255, 255, 255, 0.4);
    cursor: pointer;

    &:hover {
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

.input-icon {
  font-size: 16px;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 50px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #7f94f0 0%, #8f5db0 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  &:hover::before {
    opacity: 1;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(102, 126, 234, 0.6);
  }

  &:active {
    transform: translateY(0);
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  }

  .btn-text {
    position: relative;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .btn-icon {
    font-size: 16px;
  }
}

/* 底部 */
.footer {
  margin-top: 28px;
  text-align: center;

  .security-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    color: rgba(255, 255, 255, 0.35);
    font-size: 12px;

    .el-icon {
      font-size: 13px;
      color: rgba(102, 234, 141, 0.7);
    }
  }
}

/* 移动端适配 */
@media screen and (max-width: 480px) {
  .login-card {
    padding: 36px 24px 28px;
    border-radius: 20px;
  }

  .logo-area {
    margin-bottom: 28px;

    .logo-icon {
      width: 56px;
      height: 56px;
    }

    .title {
      font-size: 20px;
    }
  }
}
</style>
