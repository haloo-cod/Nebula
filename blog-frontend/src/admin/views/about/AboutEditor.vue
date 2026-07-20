<script setup lang="ts">
/**
 * 关于页 Markdown 编辑器
 * 内容保存到后端 content/about.md，前台继续通过公开接口读取并渲染。
 */
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import { api, BASE_URL, getToken, resolveUrl } from '@/api/client'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'

/** 关于页内容接口响应 */
interface AboutContent {
  content_md: string
  cover_url: string
}

const editorRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const saving = ref(false)
const editorReady = ref(false)
const error = ref('')
const coverUrl = ref('')
const showImagePicker = ref(false)
let vditor: Vditor | null = null

/** 初始化支持三种编辑模式、预览和图床上传的 Markdown 编辑器。 */
function initVditor(content: string) {
  if (!editorRef.value) return
  editorReady.value = false
  vditor?.destroy()
  const isDark = document.documentElement.classList.contains('dark')
  vditor = new Vditor(editorRef.value, {
    height: 620,
    mode: 'ir',
    theme: isDark ? 'dark' : 'classic',
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
    placeholder: '在这里编写关于页内容...',
    cache: { enable: false },
    value: content,
    upload: {
      url: `${BASE_URL}/api/v1/images/upload`,
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      fieldName: 'file',
      max: 10 * 1024 * 1024,
      accept: 'image/*',
      format(_files: File[], responseText: string): string {
        try {
          const response = JSON.parse(responseText) as { original_name: string; url: string }
          return JSON.stringify({
            msg: '',
            code: 0,
            data: {
              errFiles: [],
              succMap: { [response.original_name]: resolveUrl(response.url) },
            },
          })
        } catch {
          return JSON.stringify({ msg: '上传失败', code: 1, data: { errFiles: [], succMap: {} } })
        }
      },
    },
    preview: {
      actions: [],
      theme: { current: isDark ? 'dark' : 'ant-design' },
    },
    after: () => {
      if (!vditor) return
      vditor.setValue(content)
      editorReady.value = true
    },
  })
}

/** 从后端读取 Markdown，并在成功后创建编辑器。 */
async function loadContent() {
  loading.value = true
  editorReady.value = false
  error.value = ''
  vditor?.destroy()
  vditor = null
  try {
    const content = await api.get<AboutContent>('/api/v1/about/content', true)
    loading.value = false
    await nextTick()
    coverUrl.value = content.cover_url || ''
    initVditor(content.content_md)
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : '加载关于页内容失败'
  } finally {
    loading.value = false
  }
}

/** 保存当前 Markdown 内容。 */
async function saveContent() {
  if (!vditor || !editorReady.value) {
    ElMessage.warning('编辑器尚未加载完成')
    return
  }
  saving.value = true
  try {
    await api.put<AboutContent>(
      '/api/v1/about/content',
      { content_md: vditor.getValue(), cover_url: coverUrl.value },
      true,
    )
    ElMessage.success('关于页已保存')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/** 选择关于页独立封面图。 */
function handleCoverSelected(image: PickerImage) {
  coverUrl.value = image.url
}

/** 后台主题切换时同步编辑区和预览区。 */
function handleAdminThemeChange(event: Event) {
  const customEvent = event as CustomEvent<{ isDark: boolean }>
  const isDark = customEvent.detail.isDark
  vditor?.setTheme(isDark ? 'dark' : 'classic', isDark ? 'dark' : 'ant-design')
}

onMounted(() => {
  window.addEventListener('admin-theme-change', handleAdminThemeChange)
  void loadContent()
})

onBeforeUnmount(() => {
  window.removeEventListener('admin-theme-change', handleAdminThemeChange)
  vditor?.destroy()
  vditor = null
})
</script>

<template>
  <div class="about-editor-page">
    <div class="page-header">
      <div>
        <h2>关于页内容</h2>
        <p>使用 Markdown 编辑前台“关于 / 自我介绍”正文。</p>
      </div>
      <el-button
        type="primary"
        :loading="saving"
        :disabled="loading || !editorReady || !!error"
        @click="saveContent"
      >
        保存内容
      </el-button>
    </div>

    <el-card shadow="never" class="cover-card">
      <template #header>关于页封面图</template>
      <div class="cover-editor">
        <img v-if="coverUrl" :src="resolveUrl(coverUrl)" alt="关于页封面预览" class="cover-preview" />
        <div v-else class="cover-empty">未设置封面图</div>
        <div class="cover-actions">
          <el-button type="primary" @click="showImagePicker = true">从媒体库选择</el-button>
          <el-button v-if="coverUrl" @click="coverUrl = ''">清空封面</el-button>
          <el-input v-model="coverUrl" placeholder="也可手动填写图片 URL" />
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="editor-card" v-loading="loading">
      <el-result v-if="error" icon="error" title="内容加载失败" :sub-title="error">
        <template #extra>
          <el-button type="primary" :icon="RefreshRight" @click="loadContent">重新加载</el-button>
        </template>
      </el-result>
      <div v-show="!error" ref="editorRef" class="vditor-container"></div>
    </el-card>
    <ImagePickerDialog v-model="showImagePicker" title="选择关于页封面" @select="handleCoverSelected" />
  </div>
</template>

<style scoped>
.about-editor-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.page-header h2 {
  margin: 0;
  color: var(--admin-text-color);
  font-size: 20px;
}
.page-header p {
  margin: 4px 0 0;
  color: var(--admin-text-secondary);
  font-size: 13px;
}
.editor-card {
  min-height: 664px;
  border-radius: 12px;
  overflow: visible !important;
}
.cover-card {
  border-radius: 12px;
}
.cover-editor {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.cover-preview,
.cover-empty {
  width: 220px;
  height: 120px;
  border-radius: 8px;
  object-fit: cover;
}
.cover-empty {
  display: grid;
  place-items: center;
  color: var(--admin-text-secondary);
  background: var(--admin-hover-bg);
}
.cover-actions {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.cover-actions .el-input {
  flex-basis: 100%;
}
.editor-card :deep(.el-card__body) {
  overflow: visible !important;
}
.vditor-container {
  min-height: 620px;
}
@media (max-width: 640px) {
  .page-header {
    align-items: flex-start;
  }
  .cover-editor {
    flex-direction: column;
  }
  .cover-preview,
  .cover-empty {
    width: 100%;
  }
}
</style>
