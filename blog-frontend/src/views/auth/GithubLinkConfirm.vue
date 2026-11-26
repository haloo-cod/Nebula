<script setup lang="ts">
/** GitHub 邮箱命中已有密码账户时，先验证账户密码再绑定。 */
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { confirmGithubLink } from '@/api/auth'
import { ApiError, BASE_URL, setToken } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const password = ref('')
const loading = ref(false)
const error = ref('')
const linkToken = computed(() => typeof route.query.token === 'string' ? route.query.token : '')
const redirect = computed(() => {
  const value = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  return value.startsWith('/') && !value.startsWith('//') ? value : '/'
})
const githubLoginUrl = computed(() => `${BASE_URL}/api/v1/auth/github?redirect=${encodeURIComponent(redirect.value)}`)

/** 验证密码、恢复统一登录态并返回站内目标页。 */
async function submit() {
  if (!linkToken.value || !password.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await confirmGithubLink({ link_token: linkToken.value, password: password.value })
    setToken(res.access_token)
    await auth.init(true)
    if (!auth.isLoggedIn) throw new Error('未能恢复登录会话，请重新使用 GitHub 登录')
    await router.replace(redirect.value)
  } catch (err: unknown) {
    error.value = err instanceof ApiError || err instanceof Error ? err.message : 'GitHub 绑定失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="link-page">
    <section class="link-card" aria-labelledby="link-title">
      <h1 id="link-title">确认绑定 GitHub</h1>
      <template v-if="linkToken">
        <p>该邮箱已有账户，请输入现有账户密码以确认绑定。</p>
        <form @submit.prevent="submit">
          <label for="link-password">现有账户密码</label>
          <el-input id="link-password" v-model="password" type="password" autocomplete="current-password"
            show-password :disabled="loading" placeholder="请输入账户密码" />
          <el-button native-type="submit" type="primary" :loading="loading" :disabled="!password || loading">
            确认绑定并登录
          </el-button>
        </form>
        <p v-if="error" role="alert">{{ error }}</p>
        <a :href="githubLoginUrl">重新使用 GitHub 登录</a>
      </template>
      <template v-else>
        <p role="alert">缺少绑定令牌，请重新登录。</p>
        <RouterLink to="/login">返回登录</RouterLink>
      </template>
    </section>
  </main>
</template>

<style scoped>
.link-page { min-height: 100vh; display: grid; place-items: center; padding: 24px; background: #11100e; color: #ede8df; }
.link-card { width: min(100%, 400px); padding: 28px; border: 1px solid #514a40; border-radius: 12px; }
.link-card h1 { margin-top: 0; font-size: 24px; }
.link-card p { margin: 16px 0; line-height: 1.6; }
.link-card form { display: grid; gap: 12px; margin: 24px 0; }
.link-card a { color: #d2a66c; }
.link-card [role='alert'] { color: #f5a4a4; }
</style>
