<script setup lang="ts">
/**
 * 管理后台登录页
 * 全屏布局,不使用 AdminLayout,视觉参考 art-design-pro 的登录页风格
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

/** 表单数据 */
const form = reactive({
  username: '',
  password: '',
})

/** 加载状态 */
const loading = ref(false)
/** 错误信息 */
const errorMsg = ref('')

/** 提交登录 */
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
    // 登录成功,跳转到管理后台首页
    router.push('/admin/dashboard')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '登录失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- 标题 -->
      <div class="login-header">
        <h1 class="login-title">博客管理后台</h1>
        <p class="login-subtitle">请登录以继续</p>
      </div>

      <!-- 表单 -->
      <el-form :model="form" class="login-form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.username"
            label="用户名"
            placeholder="请输入用户名"
            autocomplete="username"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="form.password"
            label="密码"
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

        <!-- 错误提示 -->
        <el-alert
          v-if="errorMsg"
          :title="errorMsg"
          type="error"
          :closable="false"
          show-icon
          class="login-error"
        />

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100dvh;
  padding: 24px;
  background: #f1f4f2;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 32px;
  border: 1px solid #e4e4e7;
  border-radius: 18px;
  background: radial-gradient(circle at 100% 0%, rgba(31, 122, 104, 0.1), transparent 38%), #ffffff;
  box-shadow:
    0 1px 2px rgba(24, 24, 27, 0.04),
    0 18px 48px rgba(24, 24, 27, 0.08);
}

.login-header {
  margin-bottom: 32px;
  text-align: center;
}

.login-title {
  margin: 0 0 8px;
  color: #18181b;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.login-subtitle {
  margin: 0;
  color: #71717a;
  font-size: 14px;
}

.login-form {
  width: 100%;
}

.login-error {
  margin-bottom: 16px;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 16px;
}

@media (max-width: 480px) {
  .login-page {
    padding: 16px;
  }

  .login-card {
    padding: 24px 18px;
  }
}
</style>
