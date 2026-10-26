<template>
  <section
    id="friend-application"
    ref="rootRef"
    class="friend-applications"
    aria-labelledby="friend-application-title"
  >
    <!-- 整套申请与讨论共用一层玻璃，避免每张卡片重复创建 WebGL 实例。 -->
    <component
      :is="ui.liquidGlassEnabled ? LiquidGlass : PanelFallbackGlass"
      v-bind="glassProps"
      class="friend-applications__glass"
    >
      <div class="friend-applications__panel">
        <header class="friend-applications__header">
          <h2 id="friend-application-title" class="friend-applications__title">交换友链</h2>
        </header>

        <!-- 登录态尚未恢复时不闪出表单，也不提前显示登录提示。 -->
        <div v-if="!auth.initialized" class="friend-applications__state" role="status">
          正在加载登录状态…
        </div>

        <div v-else-if="!auth.isLoggedIn" class="friend-applications__login">
          <p>登录后即可提交友链申请，并查看自己的审核进度。</p>
          <RouterLink
            class="friend-applications__button friend-applications__button--primary"
            :to="{ path: '/login', query: { redirect: '/friends#friend-application' } }"
          >
            去登录
          </RouterLink>
        </div>

        <template v-else>
          <form class="friend-applications__form" novalidate @submit.prevent="submitApplication">
            <fieldset class="friend-applications__fieldset" :disabled="submitting">
              <div class="friend-applications__fields">
                <div
                  class="friend-applications__field"
                  :class="{ 'is-invalid': Boolean(fieldErrors.name) }"
                >
                  <label class="friend-applications__label" for="friend-application-name">
                    名称
                    <span class="friend-applications__required" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="friend-application-name"
                    v-model="form.name"
                    class="friend-applications__input"
                    type="text"
                    required
                    maxlength="100"
                    autocomplete="organization"
                    placeholder="例如：星尘小站"
                    :aria-invalid="fieldErrors.name ? 'true' : 'false'"
                    :aria-describedby="
                      fieldErrors.name ? 'friend-application-name-error' : undefined
                    "
                    @input="clearFieldError('name')"
                  />
                  <p
                    v-if="fieldErrors.name"
                    id="friend-application-name-error"
                    class="friend-applications__field-error"
                  >
                    {{ fieldErrors.name }}
                  </p>
                </div>

                <div
                  class="friend-applications__field"
                  :class="{ 'is-invalid': Boolean(fieldErrors.url) }"
                >
                  <label class="friend-applications__label" for="friend-application-url">
                    站点地址
                    <span class="friend-applications__required" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="friend-application-url"
                    v-model="form.url"
                    class="friend-applications__input"
                    type="url"
                    required
                    maxlength="500"
                    autocomplete="url"
                    placeholder="https://example.com"
                    :aria-invalid="fieldErrors.url ? 'true' : 'false'"
                    :aria-describedby="fieldErrors.url ? 'friend-application-url-error' : undefined"
                    @input="clearFieldError('url')"
                  />
                  <p
                    v-if="fieldErrors.url"
                    id="friend-application-url-error"
                    class="friend-applications__field-error"
                  >
                    {{ fieldErrors.url }}
                  </p>
                </div>

                <div
                  class="friend-applications__field"
                  :class="{ 'is-invalid': Boolean(fieldErrors.avatar) }"
                >
                  <label class="friend-applications__label" for="friend-application-avatar">
                    头像地址
                    <span class="friend-applications__required" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="friend-application-avatar"
                    v-model="form.avatar"
                    class="friend-applications__input"
                    type="url"
                    required
                    maxlength="500"
                    autocomplete="off"
                    placeholder="https://example.com/avatar.png"
                    :aria-invalid="fieldErrors.avatar ? 'true' : 'false'"
                    :aria-describedby="
                      fieldErrors.avatar ? 'friend-application-avatar-error' : undefined
                    "
                    @input="clearFieldError('avatar')"
                  />
                  <p
                    v-if="fieldErrors.avatar"
                    id="friend-application-avatar-error"
                    class="friend-applications__field-error"
                  >
                    {{ fieldErrors.avatar }}
                  </p>
                </div>

                <div
                  class="friend-applications__field"
                  :class="{ 'is-invalid': Boolean(fieldErrors.email) }"
                >
                  <label class="friend-applications__label" for="friend-application-email">
                    邮箱
                    <span class="friend-applications__required" aria-hidden="true">*</span>
                  </label>
                  <input
                    id="friend-application-email"
                    ref="emailInputRef"
                    v-model="form.email"
                    class="friend-applications__input"
                    type="email"
                    required
                    maxlength="320"
                    autocomplete="email"
                    placeholder="your-email@example.com"
                    :aria-invalid="fieldErrors.email ? 'true' : 'false'"
                    :aria-describedby="
                      fieldErrors.email ? 'friend-application-email-error' : undefined
                    "
                    @input="handleEmailInput"
                  />
                  <p
                    v-if="fieldErrors.email"
                    id="friend-application-email-error"
                    class="friend-applications__field-error"
                  >
                    {{ fieldErrors.email }}
                  </p>
                </div>

                <div
                  class="friend-applications__field friend-applications__field--wide"
                  :class="{ 'is-invalid': Boolean(fieldErrors.rss_url) }"
                >
                  <label class="friend-applications__label" for="friend-application-rss">
                    RSS 地址（选填）
                  </label>
                  <input
                    id="friend-application-rss"
                    v-model="form.rss_url"
                    class="friend-applications__input"
                    type="url"
                    maxlength="2048"
                    autocomplete="off"
                    placeholder="https://example.com/rss.xml"
                    :aria-invalid="fieldErrors.rss_url ? 'true' : 'false'"
                    :aria-describedby="
                      fieldErrors.rss_url ? 'friend-application-rss-error' : undefined
                    "
                    @input="clearFieldError('rss_url')"
                  />
                  <p
                    v-if="fieldErrors.rss_url"
                    id="friend-application-rss-error"
                    class="friend-applications__field-error"
                  >
                    {{ fieldErrors.rss_url }}
                  </p>
                </div>
              </div>

              <p
                v-if="formError"
                class="friend-applications__alert friend-applications__form-error"
                role="alert"
              >
                <span>{{ formError }}</span>
              </p>

              <div class="friend-applications__actions">
                <button
                  class="friend-applications__button friend-applications__button--primary"
                  type="submit"
                  :disabled="submitting"
                >
                  {{ submitting ? '正在提交…' : '提交申请' }}
                </button>
                <p v-if="successMessage" class="friend-applications__success" role="status">
                  {{ successMessage }}
                </p>
              </div>
            </fieldset>
          </form>

          <section
            v-if="myLoading || myError || myItems.length > 0"
            class="friend-applications__block"
            aria-labelledby="my-applications-title"
            :aria-busy="myLoading"
          >
            <div class="friend-applications__block-head">
              <h3 id="my-applications-title" class="friend-applications__block-title">我的申请</h3>
            </div>

            <p
              v-if="myLoading && myItems.length === 0"
              class="friend-applications__state"
              role="status"
            >
              正在加载我的申请…
            </p>

            <div v-if="myError" class="friend-applications__alert" role="alert">
              <span>{{ myError }}</span>
              <button
                class="friend-applications__button friend-applications__button--ghost"
                type="button"
                :disabled="myLoading"
                @click="loadMyApplications(myPage)"
              >
                重试
              </button>
            </div>

            <ul v-if="myItems.length > 0" class="friend-applications__my-list">
              <li v-for="item in myItems" :key="item.id" class="friend-applications__my-item">
                <div class="friend-applications__my-main">
                  <span class="friend-applications__my-name">{{ item.name }}</span>
                  <span
                    class="friend-applications__status"
                    :class="`friend-applications__status--${item.status}`"
                  >
                    {{ STATUS_LABELS[item.status] }}
                  </span>
                </div>
                <p class="friend-applications__meta">
                  提交于 {{ formatDateTime(item.created_at) }}
                </p>
                <p
                  v-if="item.status === 'rejected' && item.review_note"
                  class="friend-applications__reason"
                >
                  拒绝原因：{{ item.review_note }}
                </p>
              </li>
            </ul>

            <nav
              v-if="myTotal > MINE_PAGE_SIZE"
              class="friend-applications__pagination"
              aria-label="我的申请分页"
            >
              <button
                class="friend-applications__button friend-applications__button--ghost"
                type="button"
                :disabled="myLoading || myPage <= 1"
                @click="goToMyPage(myPage - 1)"
              >
                上一页
              </button>
              <span>第 {{ myPage }} / {{ myTotalPages }} 页</span>
              <button
                class="friend-applications__button friend-applications__button--ghost"
                type="button"
                :disabled="myLoading || myPage >= myTotalPages"
                @click="goToMyPage(myPage + 1)"
              >
                下一页
              </button>
            </nav>
          </section>
        </template>

        <section
          class="friend-applications__block friend-applications__block--public"
          aria-labelledby="public-applications-title"
          :aria-busy="publicLoading"
        >
          <div class="friend-applications__block-head">
            <h3 id="public-applications-title" class="friend-applications__block-title">
              交换记录
            </h3>
          </div>

          <p
            v-if="publicLoading && publicItems.length === 0"
            class="friend-applications__state"
            role="status"
          >
            正在加载交换记录…
          </p>

          <div v-if="publicError" class="friend-applications__alert" role="alert">
            <span>{{ publicError }}</span>
            <button
              class="friend-applications__button friend-applications__button--ghost"
              type="button"
              :disabled="publicLoading"
              @click="loadPublicApplications(publicPage)"
            >
              重试
            </button>
          </div>
          <p
            v-else-if="!publicLoading && publicItems.length === 0"
            class="friend-applications__state"
          >
            暂无交换记录
          </p>

          <div v-if="publicItems.length > 0" class="friend-applications__cards">
            <article
              v-for="application in publicItems"
              :key="application.id"
              class="friend-application-card"
            >
              <div class="friend-application-card__head">
                <img
                  v-if="!failedAvatars[application.id]"
                  :src="resolveUrl(application.avatar)"
                  class="friend-application-card__avatar"
                  alt=""
                  loading="lazy"
                  @error="failedAvatars[application.id] = true"
                />
                <span
                  v-else
                  class="friend-application-card__avatar friend-application-card__avatar--fallback"
                  aria-hidden="true"
                >
                  {{ application.name.charAt(0) }}
                </span>
                <div class="friend-application-card__info">
                  <a
                    class="friend-application-card__name"
                    :href="externalUrl(application.url) || undefined"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {{ application.name }}
                  </a>
                  <a
                    class="friend-application-card__url"
                    :href="externalUrl(application.url) || undefined"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {{ application.url }}
                  </a>
                  <a
                    v-if="application.rss_url"
                    class="friend-application-card__rss"
                    :href="externalUrl(application.rss_url) || undefined"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    RSS 订阅
                  </a>
                </div>
              </div>

              <p class="friend-applications__meta">
                审核通过：{{ formatDate(application.reviewed_at) }}
              </p>

              <button
                class="friend-applications__button friend-applications__button--ghost friend-application-card__toggle"
                type="button"
                :aria-expanded="isDiscussionExpanded(application.id)"
                :aria-controls="`friend-application-discussion-${application.id}`"
                @click="toggleDiscussion(application.id)"
              >
                {{ isDiscussionExpanded(application.id) ? '收起讨论' : '展开讨论' }}
              </button>

              <!-- 折叠时卸载，避免首次进入页面就请求所有申请的全部评论。 -->
              <div
                v-if="isDiscussionExpanded(application.id)"
                :id="`friend-application-discussion-${application.id}`"
                class="friend-application-card__discussion"
              >
                <AboutComments
                  :key="application.id"
                  :page-key="`friend-application:${application.id}`"
                />
              </div>
            </article>
          </div>

          <nav
            v-if="publicTotal > PUBLIC_PAGE_SIZE"
            class="friend-applications__pagination"
            aria-label="交换记录分页"
          >
            <button
              class="friend-applications__button friend-applications__button--ghost"
              type="button"
              :disabled="publicLoading || publicPage <= 1"
              @click="goToPublicPage(publicPage - 1)"
            >
              上一页
            </button>
            <span>第 {{ publicPage }} / {{ publicTotalPages }} 页</span>
            <button
              class="friend-applications__button friend-applications__button--ghost"
              type="button"
              :disabled="publicLoading || publicPage >= publicTotalPages"
              @click="goToPublicPage(publicPage + 1)"
            >
              下一页
            </button>
          </nav>
        </section>
      </div>
    </component>
  </section>
</template>

<script setup lang="ts">
/**
 * 友链申请区：登录用户提交/查看自己的申请，所有访客查看已通过申请并展开讨论。
 * 正式友链由父页面独立加载；本组件只负责申请、公开列表和本人的私有记录。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import AboutComments from '@/views/about/AboutComments.vue'
import { ApiError, resolveUrl } from '@/api/client'
import {
  fetchFriendApplications,
  fetchMyFriendApplications,
  submitFriendApplication,
  type FriendApplicationCreate,
  type FriendApplicationPrivate,
  type FriendApplicationPublic,
  type FriendApplicationStatus,
} from '@/api/friends'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const PUBLIC_PAGE_SIZE = 10
const MINE_PAGE_SIZE = 10

/** 申请表单字段，用于统一清空校验错误。 */
type ApplicationField = 'name' | 'url' | 'avatar' | 'email' | 'rss_url'

/** 申请表单的本地状态；提交前统一 trim。 */
type ApplicationForm = Required<FriendApplicationCreate>

/** 后端 422 返回的校验项。 */
interface ApiValidationIssue {
  loc?: unknown[]
  msg?: string
  type?: string
}

const APPLICATION_FIELDS: readonly ApplicationField[] = [
  'name',
  'url',
  'avatar',
  'email',
  'rss_url',
]

/** 状态文案只在这里维护，公开卡片不显示申请状态。 */
const STATUS_LABELS: Record<FriendApplicationStatus, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '未通过',
}

const route = useRoute()
const auth = useAuthStore()
const ui = useUIStore()

const rootRef = ref<HTMLElement | null>(null)
const emailInputRef = ref<HTMLInputElement | null>(null)

const form = reactive<ApplicationForm>(createEmptyForm())
const fieldErrors = reactive<Record<ApplicationField, string>>({
  name: '',
  url: '',
  avatar: '',
  email: '',
  rss_url: '',
})
const formError = ref('')
const successMessage = ref('')
const submitting = ref(false)
const emailTouched = ref(false)

const myItems = ref<FriendApplicationPrivate[]>([])
const myTotal = ref(0)
const myPage = ref(1)
const myLoading = ref(false)
const myError = ref('')

const publicItems = ref<FriendApplicationPublic[]>([])
const publicTotal = ref(0)
const publicPage = ref(1)
const publicLoading = ref(false)
const publicError = ref('')

const failedAvatars = ref<Record<number, boolean>>({})
const expandedDiscussions = ref<Set<number>>(new Set())

/** 每次登录身份变化都会递增，用来丢弃旧账号的提交/加载响应。 */
let identityVersion = 0
let myRequest = 0
let publicRequest = 0

const glassProps = computed(() =>
  ui.liquidGlassEnabled
    ? {
        theme: ui.theme,
        cornerRadius: 16,
        blurRadius: ui.liquidGlassBlur,
        rippleTrail: true,
      }
    : { staticBlur: true },
)

const myTotalPages = computed(() => Math.max(1, Math.ceil(myTotal.value / MINE_PAGE_SIZE)))
const publicTotalPages = computed(() =>
  Math.max(1, Math.ceil(publicTotal.value / PUBLIC_PAGE_SIZE)),
)

/** 表单初始值，退出登录或首次登录时整份重置。 */
function createEmptyForm(): ApplicationForm {
  return { name: '', url: '', avatar: '', email: '', rss_url: '' }
}

/** 提交前统一去除首尾空白。 */
function trimmedForm(): ApplicationForm {
  return {
    name: form.name.trim(),
    url: form.url.trim(),
    avatar: form.avatar.trim(),
    email: form.email.trim(),
    rss_url: form.rss_url.trim(),
  }
}

/** 输入时立即清除该字段的旧错误，但不掩盖站点冲突等表单级错误。 */
function clearFieldError(field: ApplicationField) {
  fieldErrors[field] = ''
  successMessage.value = ''
}

function handleEmailInput() {
  emailTouched.value = true
  clearFieldError('email')
}

/** 仅接受无空白、无凭据的完整 HTTP(S) 地址。 */
function validateHttpUrl(value: string): string {
  if (!/^https?:\/\//i.test(value)) return '请输入完整的 HTTP(S) 地址'
  if (/\s/.test(value)) return '地址不能包含空白字符'
  let parsed: URL
  try {
    parsed = new URL(value)
  } catch {
    return '请输入完整的 HTTP(S) 地址'
  }
  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    return '仅支持 HTTP(S) 地址'
  }
  if (parsed.username || parsed.password) {
    return '地址不能包含用户名或密码'
  }
  return ''
}

function isEmailValid(value: string): boolean {
  if (value.length > 320) return false
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
}

/** 前端校验与后端规则保持一致，后端 422 仍然会映射回字段。 */
function validateForm(): boolean {
  for (const field of APPLICATION_FIELDS) fieldErrors[field] = ''
  formError.value = ''
  successMessage.value = ''

  const values = trimmedForm()
  let valid = true

  if (!values.name) {
    fieldErrors.name = '请输入站点名称'
    valid = false
  } else if ([...values.name].length > 100) {
    fieldErrors.name = '名称不能超过 100 个字符'
    valid = false
  }

  if (!values.url) {
    fieldErrors.url = '请输入站点地址'
    valid = false
  } else if (values.url.length > 500) {
    fieldErrors.url = '站点地址不能超过 500 个字符'
    valid = false
  } else {
    const message = validateHttpUrl(values.url)
    if (message) {
      fieldErrors.url = message
      valid = false
    }
  }

  if (!values.avatar) {
    fieldErrors.avatar = '请输入头像地址'
    valid = false
  } else if (values.avatar.length > 500) {
    fieldErrors.avatar = '头像地址不能超过 500 个字符'
    valid = false
  } else {
    const message = validateHttpUrl(values.avatar)
    if (message) {
      fieldErrors.avatar = message
      valid = false
    }
  }

  if (!values.email) {
    fieldErrors.email = '请输入邮箱'
    valid = false
  } else if (!isEmailValid(values.email)) {
    fieldErrors.email = '请输入有效的邮箱地址'
    valid = false
  }

  if (values.rss_url) {
    if (values.rss_url.length > 2048) {
      fieldErrors.rss_url = 'RSS 地址不能超过 2048 个字符'
      valid = false
    } else {
      const message = validateHttpUrl(values.rss_url)
      if (message) {
        fieldErrors.rss_url = message
        valid = false
      }
    }
  }

  // 原生 email 输入框再补一层浏览器校验；带首尾空白时交给 trim 后的规则判断。
  if (
    !fieldErrors.email &&
    form.email === form.email.trim() &&
    emailInputRef.value?.validity.typeMismatch
  ) {
    fieldErrors.email = '请输入有效的邮箱地址'
    valid = false
  }

  return valid
}

/** 将 FastAPI 的 422 loc 映射回对应字段。 */
function isApplicationField(value: string): value is ApplicationField {
  return (APPLICATION_FIELDS as readonly string[]).includes(value)
}

function issueField(issue: ApiValidationIssue): ApplicationField | null {
  const loc = Array.isArray(issue.loc) ? issue.loc : []
  for (let index = loc.length - 1; index >= 0; index -= 1) {
    const part = loc[index]
    if (typeof part === 'string' && isApplicationField(part)) return part
  }
  return null
}

function friendlyIssueMessage(field: ApplicationField, issue: ApiValidationIssue): string {
  const type = typeof issue.type === 'string' ? issue.type : ''
  if (type.includes('missing') || issue.msg?.toLowerCase().includes('field required')) {
    return '该字段为必填项'
  }
  if (field === 'email') return '请输入有效的邮箱地址'
  if (field === 'name') {
    return type.includes('too_long') ? '名称不能超过 100 个字符' : '请输入有效的站点名称'
  }
  if (field === 'rss_url') return '请输入有效的 HTTP(S) RSS 地址'
  return '请输入有效的 HTTP(S) 地址'
}

function parseValidationIssues(detail: string): ApiValidationIssue[] {
  try {
    const parsed: unknown = JSON.parse(detail)
    return Array.isArray(parsed) ? (parsed as ApiValidationIssue[]) : []
  } catch {
    return []
  }
}

function applySubmitError(error: unknown) {
  if (!(error instanceof ApiError)) {
    formError.value = '网络异常，请检查网络后重试'
    return
  }

  if (error.status === 422) {
    const issues = parseValidationIssues(error.detail)
    let mapped = false
    for (const issue of issues) {
      const field = issueField(issue)
      if (!field) continue
      fieldErrors[field] = friendlyIssueMessage(field, issue)
      mapped = true
    }
    if (!mapped) formError.value = '提交内容未通过校验，请检查后重试'
    return
  }

  formError.value =
    error.detail ||
    (error.status === 409 ? '该站点已有待审核或已通过的申请' : '提交失败，请稍后重试')
}

/** 登录后才预填账号邮箱，用户编辑过邮箱后不再覆盖。 */
function prefillEmail() {
  const email = auth.user?.email
  if (!auth.isLoggedIn || !email || emailTouched.value || form.email) return
  form.email = email
}

/** 清空私有数据与整份表单；旧请求随后返回也不会重新填入。 */
function resetPrivateState() {
  identityVersion += 1
  myRequest += 1
  myItems.value = []
  myTotal.value = 0
  myPage.value = 1
  myLoading.value = false
  myError.value = ''
  Object.assign(form, createEmptyForm())
  for (const field of APPLICATION_FIELDS) fieldErrors[field] = ''
  formError.value = ''
  successMessage.value = ''
  emailTouched.value = false
  submitting.value = false
}

/** 响应是否仍属于当前登录用户与当前请求。 */
function isCurrentMyRequest(sequence: number, userId: number | null): boolean {
  return sequence === myRequest && auth.isLoggedIn && (auth.user?.id ?? null) === userId
}

async function loadMyApplications(page = myPage.value): Promise<void> {
  if (!auth.initialized || !auth.isLoggedIn) return
  const userId = auth.user?.id ?? null
  const sequence = ++myRequest
  myLoading.value = true
  myError.value = ''

  try {
    const response = await fetchMyFriendApplications(page, MINE_PAGE_SIZE)
    if (!isCurrentMyRequest(sequence, userId)) return

    const maxPage = Math.max(1, Math.ceil(response.total / MINE_PAGE_SIZE))
    if (page > maxPage) {
      void loadMyApplications(maxPage)
      return
    }

    myItems.value = response.items
    myTotal.value = response.total
    myPage.value = page
  } catch (error) {
    if (!isCurrentMyRequest(sequence, userId)) return
    myError.value = describeError(error, '我的申请加载失败，请稍后重试')
  } finally {
    if (sequence === myRequest) myLoading.value = false
  }
}

async function loadPublicApplications(page = publicPage.value): Promise<void> {
  const target = Math.max(1, page)
  const sequence = ++publicRequest
  publicLoading.value = true
  publicError.value = ''

  try {
    const response = await fetchFriendApplications(target, PUBLIC_PAGE_SIZE)
    if (sequence !== publicRequest) return

    const maxPage = Math.max(1, Math.ceil(response.total / PUBLIC_PAGE_SIZE))
    if (target > maxPage) {
      void loadPublicApplications(maxPage)
      return
    }

    publicItems.value = response.items
    publicTotal.value = response.total
    publicPage.value = target
    failedAvatars.value = {}

    // 被删除或移出公开列表的申请不应继续占着展开状态。
    const visibleIds = new Set(response.items.map((item) => item.id))
    expandedDiscussions.value = new Set(
      [...expandedDiscussions.value].filter((id) => visibleIds.has(id)),
    )
  } catch (error) {
    // 刷新失败时保留旧卡片，不用空列表覆盖已有内容。
    if (sequence !== publicRequest) return
    publicError.value = describeError(error, '已通过的申请加载失败，请稍后重试')
  } finally {
    if (sequence === publicRequest) publicLoading.value = false
  }
}

function describeError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return '登录状态已失效，请重新登录'
    return error.detail || fallback
  }
  return fallback
}

async function submitApplication() {
  if (submitting.value) return
  if (!auth.isLoggedIn) {
    formError.value = '登录状态已失效，请重新登录'
    return
  }
  if (!validateForm()) return

  const payload = trimmedForm()
  Object.assign(form, payload)
  const data: FriendApplicationCreate = {
    name: payload.name,
    url: payload.url,
    avatar: payload.avatar,
    email: payload.email,
    rss_url: payload.rss_url,
  }
  const version = identityVersion
  submitting.value = true

  try {
    await submitFriendApplication(data)
    if (version !== identityVersion) return

    successMessage.value = '申请已提交，等待审核'
    // 只清空站点相关字段，邮箱保留，方便继续补充申请。
    form.name = ''
    form.url = ''
    form.avatar = ''
    form.rss_url = ''
    myPage.value = 1
    await loadMyApplications(1)
  } catch (error) {
    if (version !== identityVersion) return
    applySubmitError(error)
  } finally {
    if (version === identityVersion) submitting.value = false
  }
}

/** 后端时间通常为 UTC，缺少时区时补 Z 再交给浏览器本地化。 */
function parseBackendDate(value: string): Date | null {
  if (!value) return null
  const normalized = /(?:[zZ]|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

function formatDateTime(value: string): string {
  const date = parseBackendDate(value)
  return date ? date.toLocaleString() : value.replace('T', ' ').slice(0, 19)
}

function formatDate(value: string | null): string {
  if (!value) return ''
  const date = parseBackendDate(value)
  return date ? date.toLocaleDateString() : value.replace('T', ' ').slice(0, 10)
}

/** 即使旧数据异常，也不会把 javascript: 等地址放进外链。 */
function externalUrl(value: string): string {
  if (!value) return ''
  try {
    const parsed = new URL(value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? value : ''
  } catch {
    return ''
  }
}

function isDiscussionExpanded(id: number): boolean {
  return expandedDiscussions.value.has(id)
}

function toggleDiscussion(id: number) {
  const next = new Set(expandedDiscussions.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedDiscussions.value = next
}

function goToMyPage(page: number) {
  if (myLoading.value || page < 1 || page > myTotalPages.value) return
  void loadMyApplications(page)
}

function goToPublicPage(page: number) {
  if (publicLoading.value || page < 1 || page > publicTotalPages.value) return
  void loadPublicApplications(page)
}

/** 窗口重新获得焦点时刷新公开列表和本人记录，不做轮询。 */
function handleWindowFocus() {
  void loadPublicApplications(publicPage.value)
  if (auth.initialized && auth.isLoggedIn) {
    void loadMyApplications(myPage.value)
  }
}

watch(
  () => [auth.initialized, auth.isLoggedIn, auth.user?.id] as const,
  ([initialized, loggedIn, userId], previous) => {
    const previousInitialized = previous?.[0] ?? false
    const previousLoggedIn = previous?.[1] ?? false
    const previousUserId = previous?.[2] ?? null

    if (!loggedIn) {
      // 退出登录或会话失效时立即清空私有记录与表单。
      if (previousLoggedIn || previousInitialized) resetPrivateState()
      return
    }
    if (!initialized) return

    if (!previousLoggedIn || previousUserId !== userId) {
      resetPrivateState()
      prefillEmail()
    }
    void loadMyApplications(1)
  },
  { immediate: true },
)

watch(
  () => auth.user?.email,
  () => {
    if (auth.isLoggedIn) prefillEmail()
  },
  { immediate: true },
)

onMounted(() => {
  void loadPublicApplications(1)
  window.addEventListener('focus', handleWindowFocus)

  // 登录重定向回到 /friends#friend-application 时滚动到申请区。
  nextTick(() => {
    if (route.hash === '#friend-application') {
      rootRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
})

onBeforeUnmount(() => {
  identityVersion += 1
  myRequest += 1
  publicRequest += 1
  window.removeEventListener('focus', handleWindowFocus)
})
</script>

<style scoped src="@/assets/styles/friend-applications.css"></style>
