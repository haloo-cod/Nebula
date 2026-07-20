<script setup lang="ts">
/** 前台用户名、邮箱和密码注册页。 */
import { reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { BASE_URL } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const loading = ref(false)
const error = ref('')
const emailRegisterOpen = ref(false)
const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })

/** 使用 GitHub 创建或恢复账户。 */
function registerWithGithub() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  window.location.href = `${BASE_URL}/api/v1/auth/github?redirect=${encodeURIComponent(redirect)}`
}

/** 校验注册输入并创建账户。 */
async function submit() {
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await auth.register({ username: form.username, email: form.email, password: form.password })
    await router.replace('/')
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <RouterLink to="/" class="back-link">返回博客</RouterLink>
    <section class="auth-card">
      <p class="kicker">JOIN THE CONVERSATION</p>
      <h1>创建账户</h1>
      <p class="subtitle">使用 GitHub 创建账户，快速开始。</p>
      <button class="github-btn" type="button" @click="registerWithGithub">
        <span class="github-mark" aria-hidden="true">GH</span>
        <span>使用 GitHub 创建账户</span>
      </button>
      <p class="oauth-note">使用 GitHub 公开资料创建账户，无需单独设置密码。</p>
      <button
        class="email-register-toggle"
        type="button"
        :aria-expanded="emailRegisterOpen"
        @click="emailRegisterOpen = !emailRegisterOpen"
      >
        使用邮箱注册
        <span aria-hidden="true">{{ emailRegisterOpen ? '收起' : '展开' }}</span>
      </button>
      <template v-if="emailRegisterOpen">
        <div class="divider"><span>账户信息</span></div>
        <form class="auth-form" @submit.prevent="submit">
          <label
            >用户名<input
              v-model="form.username"
              minlength="3"
              maxlength="30"
              autocomplete="username"
              required
          /></label>
          <label
            >邮箱<input v-model="form.email" type="email" autocomplete="email" required
          /></label>
          <label
            >密码<input
              v-model="form.password"
              type="password"
              minlength="8"
              maxlength="128"
              autocomplete="new-password"
              required
          /></label>
          <label
            >确认密码<input
              v-model="form.confirmPassword"
              type="password"
              autocomplete="new-password"
              required
          /></label>
          <p v-if="error" class="error-text">{{ error }}</p>
          <button class="primary-btn" type="submit" :disabled="loading">
            {{ loading ? '创建中...' : '创建账户' }}
          </button>
        </form>
      </template>
      <p class="switch-text">已有账户？<RouterLink to="/login">直接登录</RouterLink></p>
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
  width: min(450px, 100%);
  padding: 38px 42px;
  border: 1px solid #3a352f;
  background: #191714;
  box-shadow: 18px 18px 0 #0b0a09;
}
.kicker {
  color: #b68a52;
  font-size: 11px;
  letter-spacing: 0.2em;
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
  gap: 13px;
  margin-top: 24px;
}
.github-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  margin-top: 22px;
  padding: 12px;
  border: 0;
  background: #f0ece5;
  color: #171412;
  cursor: pointer;
  font-weight: 700;
}
.github-btn:hover {
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
.email-register-toggle {
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
.email-register-toggle span {
  color: #b68a52;
  font-size: 12px;
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
label {
  display: grid;
  gap: 6px;
  color: #cfc6ba;
  font-size: 13px;
}
input {
  width: 100%;
  padding: 11px 13px;
  border: 1px solid #464039;
  background: #100f0d;
  color: #f4efe7;
  outline: none;
}
input:focus {
  border-color: #b68a52;
}
.primary-btn {
  width: 100%;
  padding: 12px;
  border: 0;
  background: #c39458;
  color: #17120d;
  cursor: pointer;
  font-weight: 700;
}
.primary-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}
.error-text {
  margin: 0;
  color: #e17c75;
  font-size: 13px;
}
.switch-text {
  margin: 20px 0 0;
  text-align: center;
  font-size: 13px;
}
.switch-text a {
  color: #d2a66c;
}
@media (max-width: 520px) {
  .auth-card {
    padding: 28px 24px;
    box-shadow: 10px 10px 0 #0b0a09;
  }
}
</style>
