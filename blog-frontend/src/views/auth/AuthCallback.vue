<script setup lang="ts">
/** GitHub OAuth 回调落地页，通过 HttpOnly Refresh Cookie 恢复账户。 */
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const error = ref('')

onMounted(async () => {
  try {
    await auth.init(true)
    if (!auth.isLoggedIn) throw new Error('未能恢复 GitHub 登录会话')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/')
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'GitHub 登录失败'
  }
})
</script>

<template>
  <main class="callback-page">
    <p v-if="!error">正在完成 GitHub 登录...</p>
    <div v-else>
      <p>{{ error }}</p>
      <RouterLink to="/login">返回登录</RouterLink>
    </div>
  </main>
</template>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #11100e;
  color: #ede8df;
}
.callback-page div {
  text-align: center;
}
.callback-page a {
  color: #d2a66c;
}
</style>
