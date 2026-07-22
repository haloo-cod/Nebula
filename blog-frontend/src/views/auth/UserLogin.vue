<script setup lang="ts">
/** 前台统一账户登录页。 */
import { reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { BASE_URL } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref('')
const passwordFormOpen = ref(false)
const form = reactive({ username: '', password: '' })

/** 使用用户名或邮箱登录。 */
async function submit() {
  if (!form.username.trim() || !form.password) {
    error.value = '请输入用户名或邮箱和密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.login(form)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    loading.value = false
  }
}

/** 由后端发起 GitHub OAuth，回调后通过 Refresh Cookie 恢复会话。 */
function loginWithGithub() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  window.location.href = `${BASE_URL}/api/v1/auth/github?redirect=${encodeURIComponent(redirect)}`
}
</script>

<template>
  <main class="auth-page">
    <RouterLink to="/" class="back-link">返回博客</RouterLink>
    <section class="auth-card">
      <p class="kicker">STAY CURIOUS</p>
      <h1>欢迎回来</h1>
      <p class="subtitle">使用 GitHub 登录，快速进入博客。</p>
      <button class="github-btn github-btn--featured" type="button" @click="loginWithGithub">
        <span class="github-mark" aria-hidden="true">GH</span>
        <span>使用 GitHub 登录</span>
      </button>
      <p class="oauth-note">使用 GitHub 公开资料创建或恢复账户。</p>
      <button
        class="password-toggle"
        type="button"
        :aria-expanded="passwordFormOpen"
        @click="passwordFormOpen = !passwordFormOpen"
      >
        使用账户密码登录
        <span aria-hidden="true">{{ passwordFormOpen ? '收起' : '展开' }}</span>
      </button>
      <template v-if="passwordFormOpen">
        <div class="divider"><span>账户密码</span></div>
        <form class="auth-form" @submit.prevent="submit">
          <label>用户名或邮箱<input v-model="form.username" autocomplete="username" /></label>
          <label
            >密码<input v-model="form.password" type="password" autocomplete="current-password"
          /></label>
          <p v-if="error" class="error-text">{{ error }}</p>
          <button class="primary-btn" type="submit" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
      </template>
      <p class="switch-text">还没有账户？<RouterLink to="/register">创建账户</RouterLink></p>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 20px;
  background: #11100e;
  color: #ede8df;
}
.back-link {
  position: fixed;
  top: 24px;
  left: 28px;
  color: #b9ad9c;
}
.auth-card {
  width: min(430px, 100%);
  padding: 42px;
  border: 1px solid #3a352f;
  background: #191714;
  box-shadow: 18px 18px 0 #0b0a09;
}
.kicker {
  color: #b68a52;
  font-size: 11px;
  letter-spacing: 0.22em;
}
h1 {
  margin: 8px 0;
  font:
    700 34px/1.2 Georgia,
    serif;
}
.subtitle,
.switch-text {
  color: #a99f92;
}
.auth-form {
  display: grid;
  gap: 16px;
  margin-top: 28px;
}
.github-btn--featured {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 24px;
  background: #f0ece5;
  color: #171412;
}
.github-btn--featured:hover {
  background: #ffffff;
}
.github-mark {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
}
.oauth-note {
  margin: 9px 0 0;
  color: #84796e;
  font-size: 12px;
  text-align: center;
}
.password-toggle {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 22px;
  padding: 12px 0;
  border: 0;
  border-top: 1px solid #37322d;
  background: transparent;
  color: #cfc6ba;
  cursor: pointer;
  font: inherit;
  text-align: left;
}
.password-toggle span {
  color: #b68a52;
  font-size: 12px;
}
label {
  display: grid;
  gap: 7px;
  color: #cfc6ba;
  font-size: 13px;
}
input {
  width: 100%;
  padding: 12px 13px;
  border: 1px solid #464039;
  background: #100f0d;
  color: #f4efe7;
  outline: none;
}
input:focus {
  border-color: #b68a52;
}
.primary-btn,
.github-btn {
  width: 100%;
  padding: 12px;
  border: 0;
  cursor: pointer;
  font-weight: 700;
}
.primary-btn {
  background: #c39458;
  color: #17120d;
}
.primary-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}
.github-btn {
  border: 1px solid #4c463f;
  background: transparent;
  color: #ede8df;
}
.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 22px 0;
  color: #766f66;
  font-size: 12px;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #37322d;
}
.error-text {
  margin: 0;
  color: #e17c75;
  font-size: 13px;
}
.switch-text {
  margin: 22px 0 0;
  text-align: center;
  font-size: 13px;
}
.switch-text a {
  color: #d2a66c;
}
@media (max-width: 520px) {
  .auth-card {
    padding: 30px 24px;
    box-shadow: 10px 10px 0 #0b0a09;
  }
}
</style>
