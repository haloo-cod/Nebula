<script setup lang="ts">
/**
 * 管理后台登录页
 * 采用方案 A 纸墨刊物极简居中卡片，支持读取已保存的后台亮/暗主题偏好。
 */
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock, ArrowLeft } from '@element-plus/icons-vue'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@/assets/admin.css'

const router = useRouter()
const authStore = useAuthStore()

const isDark = ref(
  typeof localStorage !== 'undefined' && localStorage.getItem('admin_dark_mode') === 'true',
)

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const errorMsg = ref('')

onMounted(() => {
  document.documentElement.classList.add('admin-theme')
  document.documentElement.classList.toggle('dark', isDark.value)
})

onBeforeUnmount(() => {
  document.documentElement.classList.remove('dark', 'admin-theme')
})

/** 提交管理员登录 */
async function handleLogin() {
  if (!form.username || !form.password) {
    errorMsg.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    await authStore.login({
      username: form.username,
      password: form.password,
    })
    if (!authStore.isAdmin) {
      await authStore.logout()
      errorMsg.value = '该账户没有管理员权限'
      return
    }
    await router.push('/admin/dashboard')
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="admin-login-root" :class="{ 'admin-dark': isDark }">
    <div class="login-card">
      <div class="login-brand">
        <span class="brand-mark" aria-hidden="true">S</span>
        <span class="brand-name">Starlit</span>
      </div>

      <div class="login-header">
        <span class="login-eyebrow">ADMIN STUDIO</span>
        <h1 class="login-title">登录内容工作台</h1>
        <p class="login-subtitle">输入管理员账户信息以管理博客内容与配置</p>
      </div>

      <el-form :model="form" label-position="top" class="login-form" @submit.prevent="handleLogin">
        <el-form-item label="用户名">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            autocomplete="username"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            size="large"
            :prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-alert
          v-if="errorMsg"
          :title="errorMsg"
          type="error"
          :closable="false"
          show-icon
          class="login-error"
        />

        <el-form-item class="login-submit-item">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            登录工作台
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <router-link to="/" class="back-home-link">
          <el-icon><ArrowLeft /></el-icon>返回博客首页
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-root {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  padding: 24px;
  background: var(--admin-content-bg);
  color: var(--admin-text-color);
  font-family: var(--admin-font-sans);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 34px 32px 26px;
  border: 1px solid var(--admin-border-color);
  border-radius: 14px;
  background: var(--admin-panel-bg);
  box-shadow: var(--admin-shadow-hover);
}

.login-brand {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 24px;
}

.brand-mark {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid var(--admin-border-strong);
  border-radius: 7px;
  background: var(--admin-panel-subtle);
  color: var(--admin-text-color);
  font-family: var(--admin-font-serif);
  font-size: 15px;
  font-weight: 700;
}

.brand-name {
  font-family: var(--admin-font-serif);
  font-size: 17px;
  font-weight: 700;
}

.login-header {
  margin-bottom: 24px;
}

.login-eyebrow {
  display: block;
  margin-bottom: 6px;
  color: var(--admin-primary-color);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.login-title {
  margin: 0 0 6px;
  color: var(--admin-text-color);
  font-size: 23px;
  font-weight: 700;
  letter-spacing: -0.025em;
}

.login-subtitle {
  margin: 0;
  color: var(--admin-text-secondary);
  font-size: 13px;
}

.login-error {
  margin-bottom: 16px;
}

.login-submit-item {
  margin-top: 8px;
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  height: 42px;
  font-size: 14px;
}

.login-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--admin-border-color);
  text-align: center;
}

.back-home-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--admin-text-secondary);
  font-size: 12.5px;
  text-decoration: none;
}

.back-home-link:hover {
  color: var(--admin-primary-color);
}

@media (max-width: 480px) {
  .admin-login-root {
    padding: 16px;
  }

  .login-card {
    padding: 26px 20px 22px;
  }
}
</style>
