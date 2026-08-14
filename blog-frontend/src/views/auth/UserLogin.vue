<script setup lang="ts">
/** 前台统一账户登录页。 */
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { BASE_URL } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const loading = ref(false)
const error = ref('')
const passwordFormOpen = ref(false)
const passwordVisible = ref(false)
const form = reactive({ username: '', password: '' })
const verifiedMessage = computed(() => route.query.verified === '1')

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
    <div class="ambient ambient--violet" aria-hidden="true"></div>
    <div class="ambient ambient--gold" aria-hidden="true"></div>
    <div class="grain" aria-hidden="true"></div>

    <RouterLink to="/" class="back-link">
      <span class="back-link__arrow" aria-hidden="true">←</span>
      <span>返回博客</span>
    </RouterLink>

    <section class="auth-card" aria-labelledby="login-title">
      <div class="brand-mark" aria-hidden="true">
        <span class="brand-mark__star">✦</span>
        <span class="brand-mark__line"></span>
      </div>
      <p class="kicker">STAY CURIOUS</p>
      <h1 id="login-title">欢迎回来<span class="title-dot">。</span></h1>
      <p class="subtitle">在星光下，继续你的下一段阅读。</p>
      <p v-if="verifiedMessage" class="verified-message" role="status">
        邮箱验证成功，现在可以登录了。
      </p>

      <button class="github-btn github-btn--featured" type="button" @click="loginWithGithub">
        <svg class="github-mark" viewBox="0 0 24 24" aria-hidden="true">
          <path
            fill="currentColor"
            d="M12 2C6.48 2 2 6.58 2 12.24c0 4.52 2.87 8.35 6.84 9.7.5.1.68-.22.68-.49v-1.72c-2.78.62-3.37-1.38-3.37-1.38-.46-1.2-1.12-1.52-1.12-1.52-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.58 2.35 1.12 2.92.86.09-.67.35-1.12.63-1.38-2.22-.26-4.56-1.15-4.56-5.08 0-1.12.39-2.04 1.03-2.76-.1-.26-.45-1.31.1-2.73 0 0 .84-.28 2.75 1.05A9.1 9.1 0 0 1 12 6.91c.85 0 1.7.12 2.5.36 1.91-1.33 2.75-1.05 2.75-1.05.55 1.42.2 2.47.1 2.73.64.72 1.03 1.64 1.03 2.76 0 3.94-2.35 4.81-4.58 5.07.36.32.68.94.68 1.9v2.82c0 .27.18.59.69.49A10.26 10.26 0 0 0 22 12.24C22 6.58 17.52 2 12 2Z"
          />
        </svg>
        <span>使用 GitHub 登录</span>
      </button>
      <p class="oauth-note"><span class="status-dot"></span>使用公开资料创建或恢复账户</p>

      <button
        class="password-toggle"
        type="button"
        :aria-expanded="passwordFormOpen"
        @click="passwordFormOpen = !passwordFormOpen"
      >
        <span class="password-toggle__label">
          <span class="password-toggle__icon" aria-hidden="true">⌁</span>
          使用账户密码登录
        </span>
        <span class="password-toggle__action" aria-hidden="true">
          {{ passwordFormOpen ? '收起' : '展开' }}
          <span class="chevron" :class="{ 'chevron--open': passwordFormOpen }">⌄</span>
        </span>
      </button>

      <template v-if="passwordFormOpen">
        <form class="auth-form" @submit.prevent="submit">
          <div class="field-group">
            <label for="login-identity">用户名或邮箱</label>
            <input
              id="login-identity"
              v-model="form.username"
              autocomplete="username"
              placeholder="name@example.com"
              required
            />
          </div>
          <div class="field-group">
            <label for="login-password">密码</label>
            <div class="password-field">
              <input
                id="login-password"
                v-model="form.password"
                :type="passwordVisible ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="输入你的密码"
                required
              />
              <button
                class="password-visibility"
                type="button"
                :aria-label="passwordVisible ? '隐藏密码' : '显示密码'"
                @click="passwordVisible = !passwordVisible"
              >
                {{ passwordVisible ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>
          <p v-if="error" class="error-text" role="alert">{{ error }}</p>
          <button class="primary-btn" type="submit" :disabled="loading">
            <span>{{ loading ? '正在进入...' : '进入博客' }}</span>
            <span class="button-arrow" aria-hidden="true">→</span>
          </button>
        </form>
      </template>

      <p class="switch-text">
        还没有账户？<RouterLink to="/register">创建一个新的账户</RouterLink>
      </p>
      <p class="privacy-note">登录即表示你同意以友善的方式使用这里的内容。</p>
    </section>

    <p class="page-note">A quiet corner for curious minds</p>
  </main>
</template>

<style scoped>
.auth-page {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 88px 24px 64px;
  background:
    radial-gradient(circle at 50% 0%, rgba(59, 74, 120, 0.22), transparent 38%),
    linear-gradient(145deg, #090b13 0%, #11131c 48%, #0b0b11 100%);
  color: #f4f1ea;
}

.back-link {
  position: fixed;
  z-index: 3;
  top: max(24px, env(safe-area-inset-top));
  left: max(24px, env(safe-area-inset-left));
  display: inline-flex;
  align-items: center;
  gap: 9px;
  min-height: 44px;
  padding: 8px 14px 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  background: rgba(13, 16, 27, 0.44);
  color: rgba(244, 241, 234, 0.72);
  font-size: 13px;
  backdrop-filter: blur(12px);
  transition:
    border-color 180ms ease,
    color 180ms ease,
    background 180ms ease;
}

.back-link:hover,
.back-link:focus-visible {
  border-color: rgba(218, 174, 111, 0.5);
  background: rgba(218, 174, 111, 0.12);
  color: #f4f1ea;
}

.back-link__arrow {
  color: #d8aa6b;
  font-size: 18px;
  line-height: 1;
}

.ambient {
  position: absolute;
  z-index: -1;
  width: 34vw;
  height: 34vw;
  min-width: 260px;
  min-height: 260px;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.42;
  pointer-events: none;
}

.ambient--violet {
  top: 9%;
  left: 8%;
  background: rgba(82, 91, 170, 0.38);
}

.ambient--gold {
  right: 8%;
  bottom: 6%;
  background: rgba(178, 121, 59, 0.2);
}

.grain {
  position: absolute;
  inset: 0;
  z-index: -1;
  opacity: 0.11;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.38'/%3E%3C/svg%3E");
  pointer-events: none;
}

.auth-card {
  position: relative;
  width: min(100%, 456px);
  padding: 42px 44px 34px;
  border: 1px solid rgba(255, 255, 255, 0.17);
  border-radius: 28px;
  background: linear-gradient(145deg, rgba(42, 48, 70, 0.62), rgba(17, 20, 31, 0.76));
  box-shadow:
    0 32px 90px rgba(0, 0, 0, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    inset 0 0 40px rgba(137, 151, 207, 0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  text-align: left;
  animation: card-enter 420ms ease-out both;
}

.auth-card::before {
  position: absolute;
  inset: 1px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 27px;
  content: '';
  pointer-events: none;
}

.brand-mark {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
}

.brand-mark__star {
  color: #e2b675;
  font-size: 22px;
  text-shadow: 0 0 18px rgba(226, 182, 117, 0.55);
}

.brand-mark__line {
  width: 40px;
  height: 1px;
  background: linear-gradient(90deg, rgba(226, 182, 117, 0.7), transparent);
}

.kicker {
  margin-bottom: 9px;
  color: #d8aa6b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.24em;
}

h1 {
  margin: 0;
  color: #fbf8f1;
  font:
    700 clamp(30px, 5vw, 38px) / 1.2 Georgia,
    serif;
  letter-spacing: -0.03em;
}

.title-dot {
  color: #d8aa6b;
}

.subtitle,
.switch-text {
  color: rgba(231, 227, 218, 0.64);
}

.subtitle {
  margin-top: 12px;
  font-size: 14px;
}

.verified-message {
  margin-top: 16px;
  padding: 10px 12px;
  border: 1px solid rgba(136, 194, 155, 0.3);
  border-radius: 10px;
  background: rgba(74, 132, 91, 0.16);
  color: #b8e5c5;
  font-size: 13px;
}

.auth-form {
  display: grid;
  gap: 18px;
  margin-top: 24px;
}

.github-btn--featured {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 28px;
  background: #f4f1ea;
  color: #15161c;
  box-shadow: 0 9px 24px rgba(0, 0, 0, 0.2);
}

.github-btn--featured:hover {
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.28);
}

.github-mark {
  width: 19px;
  height: 19px;
}

.oauth-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin: 11px 0 0;
  color: rgba(231, 227, 218, 0.46);
  font-size: 12px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #88c29b;
  box-shadow: 0 0 10px rgba(136, 194, 155, 0.8);
}

.password-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 48px;
  margin-top: 25px;
  padding: 14px 0 10px;
  border: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  background: transparent;
  color: rgba(244, 241, 234, 0.82);
  cursor: pointer;
  font: inherit;
  text-align: left;
  transition:
    color 180ms ease,
    border-color 180ms ease;
}

.password-toggle:hover,
.password-toggle:focus-visible {
  border-color: rgba(216, 170, 107, 0.55);
  color: #f4f1ea;
}

.password-toggle__label,
.password-toggle__action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.password-toggle__icon {
  color: #d8aa6b;
  font-size: 20px;
  transform: rotate(-25deg);
}

.password-toggle__action {
  color: #d8aa6b;
  font-size: 12px;
}

.chevron {
  display: inline-block;
  font-size: 17px;
  line-height: 0.7;
  transition: transform 180ms ease;
}

.chevron--open {
  transform: rotate(180deg);
}

.field-group {
  display: grid;
  gap: 8px;
}

.field-group label {
  color: rgba(244, 241, 234, 0.8);
  font-size: 13px;
}

input {
  width: 100%;
  min-height: 48px;
  padding: 11px 14px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  outline: 2px solid transparent;
  outline-offset: 2px;
  background: rgba(5, 7, 13, 0.38);
  color: #f4efe7;
  transition:
    border-color 180ms ease,
    background 180ms ease,
    outline-color 180ms ease;
}

input::placeholder {
  color: rgba(231, 227, 218, 0.32);
}

input:focus,
input:focus-visible {
  border-color: rgba(216, 170, 107, 0.78);
  outline-color: rgba(216, 170, 107, 0.25);
  background: rgba(5, 7, 13, 0.58);
}

.password-field {
  position: relative;
}

.password-field input {
  padding-right: 70px;
}

.password-visibility {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 58px;
  min-height: 40px;
  padding: 8px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #d8aa6b;
  cursor: pointer;
  font-size: 12px;
  transition:
    background 180ms ease,
    color 180ms ease;
}

.password-visibility:hover,
.password-visibility:focus-visible {
  background: rgba(216, 170, 107, 0.13);
  color: #f4f1ea;
}

.primary-btn,
.github-btn {
  width: 100%;
  min-height: 48px;
  padding: 12px 16px;
  border: 1px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background 180ms ease,
    opacity 180ms ease;
}

.primary-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
  background: linear-gradient(110deg, #d3a064, #e4bb7a);
  color: #20170f;
  box-shadow: 0 8px 22px rgba(185, 133, 65, 0.2);
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(185, 133, 65, 0.3);
}

.button-arrow {
  font-size: 20px;
  font-weight: 400;
}

.primary-btn:disabled {
  opacity: 0.55;
  cursor: wait;
  transform: none;
}

.github-btn {
  border-color: rgba(255, 255, 255, 0.16);
  cursor: pointer;
}

.github-btn:focus-visible,
.primary-btn:focus-visible,
.back-link:focus-visible,
.password-toggle:focus-visible,
.password-visibility:focus-visible {
  outline: 2px solid #e2b675;
  outline-offset: 3px;
}

.error-text {
  margin: -2px 0 0;
  padding: 10px 12px;
  border: 1px solid rgba(225, 124, 117, 0.35);
  border-radius: 10px;
  background: rgba(151, 55, 58, 0.18);
  color: #ffb2aa;
  font-size: 13px;
}

.switch-text {
  margin: 28px 0 0;
  text-align: center;
  font-size: 13px;
}

.switch-text a {
  color: #e3b575;
  text-decoration: underline;
  text-decoration-color: rgba(227, 181, 117, 0.4);
  text-underline-offset: 3px;
}

.privacy-note {
  margin-top: 17px;
  color: rgba(231, 227, 218, 0.34);
  font-size: 11px;
  line-height: 1.6;
  text-align: center;
}

.page-note {
  position: absolute;
  right: 24px;
  bottom: 23px;
  color: rgba(231, 227, 218, 0.28);
  font-family: Georgia, serif;
  font-size: 11px;
  font-style: italic;
  letter-spacing: 0.04em;
}

@keyframes card-enter {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

@media (max-width: 560px) {
  .auth-page {
    align-items: flex-start;
    padding: 92px 20px 72px;
  }

  .auth-card {
    padding: 32px 24px 28px;
    border-radius: 22px;
  }

  .auth-card::before {
    border-radius: 21px;
  }

  .page-note {
    right: 20px;
    bottom: 18px;
  }
}

@media (max-height: 680px) and (min-width: 561px) {
  .auth-page {
    align-items: flex-start;
    overflow-y: auto;
    padding-top: 80px;
  }
}

@media (max-width: 360px) {
  .auth-page {
    padding-right: 14px;
    padding-left: 14px;
  }

  .auth-card {
    padding-right: 20px;
    padding-left: 20px;
  }

  .oauth-note {
    font-size: 11px;
  }
}
</style>
