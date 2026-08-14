<script setup lang="ts">
/** 邮箱验证结果页。 */
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  try {
    if (!token) throw new Error('邮箱验证链接不完整')
    await api.get(`/api/v1/auth/email-verification/confirm?token=${encodeURIComponent(token)}`)
    await router.replace('/login?verified=1')
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : '邮箱验证失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="verify-page">
    <section>
      <p v-if="loading">正在验证邮箱...</p>
      <template v-else-if="error"
        ><h1>验证失败</h1>
        <p>{{ error }}</p></template
      >
      <template v-else
        ><h1>邮箱验证成功</h1>
        <p>现在可以使用完整的账户功能。</p></template
      >
      <RouterLink :to="error ? '/' : '/login'">{{ error ? '返回博客' : '前往登录' }}</RouterLink>
    </section>
  </main>
</template>

<style scoped>
.verify-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #11100e;
  color: #ede8df;
}
section {
  max-width: 520px;
  text-align: center;
}
h1 {
  font-family: Georgia, serif;
}
a {
  color: #d2a66c;
}
</style>
