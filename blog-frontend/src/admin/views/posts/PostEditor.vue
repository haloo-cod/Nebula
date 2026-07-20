<script setup lang="ts">
/**
 * 文章编辑页 — 新建 / 编辑文章
 * 集成 Vditor Markdown 编辑器（支持 sv/ir/wysiwyg 三种模式切换）
 * 图片粘贴/拖拽自动上传到后端图床
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import { api, getToken, resolveUrl, BASE_URL } from '@/api/client'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'

/** 后端文章详情（与 PostDetail schema 对应） */
interface PostDetail {
  id: number
  slug: string
  title: string
  description: string
  date: string
  cover_url: string
  category: string
  tags: string[]
  is_draft: boolean
  is_pinned: boolean
  content_md: string
  content_html: string
  created_at: string
  updated_at: string
}

const route = useRoute()
const router = useRouter()

/** 是否为编辑模式（路由参数有 slug 且不为 'new'） */
const isEdit = ref(false)
const saving = ref(false)
const showCoverPicker = ref(false)

/** 表单数据 */
const form = ref({
  slug: '',
  title: '',
  description: '',
  date: '',
  cover_url: '',
  category: '',
  tags: [] as string[],
  is_draft: false,
  is_pinned: false,
  content_md: '',
})

/** 标签输入 */
const tagInput = ref('')

/** Vditor 实例 */
let vditor: Vditor | null = null
const editorRef = ref<HTMLDivElement | null>(null)

/** 初始化 Vditor 编辑器 */
function initVditor(content = '') {
  if (!editorRef.value) return
  const isDark = document.documentElement.classList.contains('dark')

  vditor = new Vditor(editorRef.value, {
    height: 500,
    mode: 'ir',
    theme: isDark ? 'dark' : 'classic',
    // 三种模式都可用
    toolbar: [
      'emoji',
      'headings',
      'bold',
      'italic',
      'strike',
      '|',
      'line',
      'quote',
      'list',
      'ordered-list',
      'check',
      '|',
      'code',
      'inline-code',
      'link',
      'upload',
      'table',
      '|',
      'undo',
      'redo',
      '|',
      'edit-mode',
      'fullscreen',
      'outline',
      'preview',
    ],
    placeholder: '开始写作...',
    cache: { enable: false },
    value: content,
    upload: {
      // 图片上传配置：直接对接后端图床 API（需要完整 URL，Vditor 不走前端 proxy）
      url: `${BASE_URL}/api/v1/images/upload`,
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      fieldName: 'file',
      max: 10 * 1024 * 1024, // 10MB
      accept: 'image/*',
      // 自定义上传处理：解析后端响应，返回 Vditor 要求的格式
      format(_files: File[], responseText: string): string {
        try {
          const res = JSON.parse(responseText)
          const url = resolveUrl(res.url)
          return JSON.stringify({
            msg: '',
            code: 0,
            data: { errFiles: [], succMap: { [res.original_name]: url } },
          })
        } catch {
          return JSON.stringify({ msg: '上传失败', code: 1, data: { errFiles: [], succMap: {} } })
        }
      },
    },
    preview: {
      // 移除预览区的 Desktop/Tablet/Mobile/公众号/知乎 按钮
      actions: [],
      theme: {
        current: isDark ? 'dark' : 'ant-design',
      },
    },
    after: () => {
      // 编辑器就绪后设置内容
      if (content && vditor) {
        vditor.setValue(content)
      }
    },
  })
}

/** 后台主题切换时同步 Vditor 编辑区和预览区。 */
function handleAdminThemeChange(event: Event) {
  const customEvent = event as CustomEvent<{ isDark: boolean }>
  const isDark = customEvent.detail.isDark
  vditor?.setTheme(isDark ? 'dark' : 'classic', isDark ? 'dark' : 'ant-design')
}

/** 获取编辑器当前内容 */
function getEditorContent(): string {
  return vditor?.getValue() ?? ''
}

/** 保存文章（新建 or 更新） */
async function handleSave() {
  const content_md = getEditorContent()
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写文章标题')
    return
  }
  if (!form.value.slug.trim()) {
    ElMessage.warning('请填写文章 Slug')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form.value,
      content_md,
    }

    if (isEdit.value) {
      await api.put(`/api/v1/posts/${form.value.slug}`, payload, true)
      ElMessage.success('文章已更新')
    } else {
      await api.post('/api/v1/posts', payload, true)
      ElMessage.success('文章已创建')
      router.push('/admin/posts')
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '保存失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

/** 添加标签 */
function addTag() {
  const tag = tagInput.value.trim()
  if (tag && !form.value.tags.includes(tag)) {
    form.value.tags.push(tag)
  }
  tagInput.value = ''
}

/** 移除标签 */
function removeTag(tag: string) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

/** 从已上传图片中选择文章封面。 */
function handleCoverSelected(image: PickerImage) {
  form.value.cover_url = image.url
}

/** 返回列表 */
function goBack() {
  router.push('/admin/posts')
}

onMounted(() => {
  window.addEventListener('admin-theme-change', handleAdminThemeChange)
  const slug = route.params.id as string
  if (slug && slug !== 'new') {
    isEdit.value = true
    // 先加载文章内容，再初始化编辑器
    api
      .get<PostDetail>(`/api/v1/posts/${slug}`, true)
      .then((detail) => {
        form.value = {
          slug: detail.slug,
          title: detail.title,
          description: detail.description,
          date: detail.date,
          cover_url: detail.cover_url,
          category: detail.category,
          tags: detail.tags,
          is_draft: detail.is_draft,
          is_pinned: detail.is_pinned,
          content_md: detail.content_md,
        }
        initVditor(detail.content_md)
      })
      .catch(() => {
        ElMessage.error('加载文章失败')
        initVditor('')
      })
  } else {
    isEdit.value = false
    initVditor('')
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('admin-theme-change', handleAdminThemeChange)
  vditor?.destroy()
  vditor = null
})
</script>

<template>
  <div class="post-editor-page">
    <!-- 顶部操作栏 -->
    <div class="editor-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>返回列表
      </el-button>
      <div class="header-actions">
        <el-switch v-model="form.is_draft" active-text="草稿" inactive-text="发布" />
        <el-switch v-model="form.is_pinned" active-text="置顶" />
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ isEdit ? '更新文章' : '创建文章' }}
        </el-button>
      </div>
    </div>

    <!-- 元数据表单 -->
    <el-card shadow="never" class="meta-card">
      <div class="meta-grid">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="文章标题" />
        </el-form-item>
        <el-form-item label="Slug">
          <el-input v-model="form.slug" placeholder="url-friendly-slug" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="如：技术、生活" />
        </el-form-item>
        <el-form-item label="日期">
          <el-input v-model="form.date" placeholder="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="摘要">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="文章摘要" />
        </el-form-item>
        <el-form-item label="封面图">
          <div class="cover-field">
            <img
              v-if="form.cover_url"
              :src="resolveUrl(form.cover_url)"
              alt="文章封面预览"
              class="cover-preview"
            />
            <div v-else class="cover-empty">未设置封面</div>
            <div class="cover-actions">
              <div>
                <el-button type="primary" plain @click="showCoverPicker = true">
                  从已上传图片选择
                </el-button>
                <el-button v-if="form.cover_url" @click="form.cover_url = ''">清空</el-button>
              </div>
              <el-input v-model="form.cover_url" placeholder="也可手动填写封面图 URL" />
            </div>
          </div>
        </el-form-item>
        <el-form-item label="标签">
          <div class="tags-input">
            <el-tag
              v-for="tag in form.tags"
              :key="tag"
              closable
              @close="removeTag(tag)"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-model="tagInput"
              size="small"
              placeholder="输入标签后回车"
              style="width: 140px"
              @keyup.enter="addTag"
            />
          </div>
        </el-form-item>
      </div>
    </el-card>

    <!-- Markdown 编辑器 -->
    <el-card shadow="never" class="editor-card">
      <div ref="editorRef" class="vditor-container"></div>
    </el-card>
    <ImagePickerDialog
      v-model="showCoverPicker"
      title="选择文章封面"
      @select="handleCoverSelected"
    />
  </div>
</template>

<style scoped>
.post-editor-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.meta-card {
  border-radius: 12px;
}

.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
}

.meta-grid .el-form-item:nth-child(5),
.meta-grid .el-form-item:nth-child(6),
.meta-grid .el-form-item:nth-child(7) {
  grid-column: 1 / -1;
}

.tags-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.cover-field {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.cover-preview,
.cover-empty {
  width: 180px;
  height: 100px;
  flex-shrink: 0;
  border-radius: 6px;
  object-fit: cover;
}

.cover-empty {
  display: grid;
  place-items: center;
  color: var(--admin-text-secondary);
  background: var(--admin-fill-bg, #f5f7fa);
  font-size: 12px;
}

.cover-actions {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
}

.tag-item {
  margin: 0;
}

.editor-card {
  border-radius: 12px;
  overflow: visible !important;
}

.editor-card :deep(.el-card__body) {
  overflow: visible !important;
}

.vditor-container {
  min-height: 500px;
}

@media (max-width: 640px) {
  .cover-field {
    flex-direction: column;
  }

  .cover-preview,
  .cover-empty {
    width: 100%;
  }
}
</style>
