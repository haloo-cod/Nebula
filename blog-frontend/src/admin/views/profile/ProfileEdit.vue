<script setup lang="ts">
/**
 * 个人资料编辑页
 * 编辑站点 profile（昵称/简介/头像/封面）+ 社交链接管理
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '@/api/client'

/** 个人资料（匹配后端 ProfileResponse） */
interface ProfileData {
  name: string
  bio: string
  avatar_url: string
  cover_url: string
  social_links: SocialLink[]
}

/** 社交链接 */
interface SocialLink {
  id: number
  label: string
  icon: string
  url: string
  sort_order: number
}

const loading = ref(false)
const saving = ref(false)
const profile = ref<ProfileData>({ name: '', bio: '', avatar_url: '', cover_url: '', social_links: [] })

// 社交链接弹窗
const showLinkDialog = ref(false)
const savingLink = ref(false)
const linkForm = ref({ label: '', icon: '', url: '', sort_order: 0 })

/** 加载个人资料 */
async function loadProfile() {
  loading.value = true
  try {
    profile.value = await api.get<ProfileData>('/api/v1/profile', true)
  } catch {
    ElMessage.error('加载个人资料失败')
  } finally {
    loading.value = false
  }
}

/** 保存个人资料 */
async function saveProfile() {
  saving.value = true
  try {
    await api.put('/api/v1/profile', {
      name: profile.value.name,
      bio: profile.value.bio,
      avatar_url: profile.value.avatar_url,
      cover_url: profile.value.cover_url,
    }, true)
    ElMessage.success('保存成功')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/** 打开添加社交链接弹窗 */
function openAddLink() {
  linkForm.value = { label: '', icon: '', url: '', sort_order: 0 }
  showLinkDialog.value = true
}

/** 添加社交链接 */
async function saveLink() {
  if (!linkForm.value.label.trim() || !linkForm.value.url.trim()) {
    ElMessage.warning('平台名称和 URL 不能为空')
    return
  }
  savingLink.value = true
  try {
    await api.post('/api/v1/profile/social-links', linkForm.value, true)
    ElMessage.success('添加成功')
    showLinkDialog.value = false
    loadProfile()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '添加失败')
  } finally {
    savingLink.value = false
  }
}

/** 删除社交链接 */
async function deleteLink(link: SocialLink) {
  try {
    await ElMessageBox.confirm(`确定删除「${link.label}」？`, '确认', { type: 'warning' })
    await api.delete(`/api/v1/profile/social-links/${link.id}`)
    ElMessage.success('删除成功')
    loadProfile()
  } catch { /* 取消 */ }
}

onMounted(() => loadProfile())
</script>

<template>
  <div class="profile-edit-page" v-loading="loading">
    <!-- 基本信息 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="昵称">
            <el-input v-model="profile.name" placeholder="站点昵称" />
          </el-form-item>
          <el-form-item label="头像 URL">
            <el-input v-model="profile.avatar_url" placeholder="头像图片地址" />
          </el-form-item>
        </div>
        <el-form-item label="简介">
          <el-input v-model="profile.bio" type="textarea" :rows="3" placeholder="个人简介 / 站点描述" />
        </el-form-item>
        <el-form-item label="封面图 URL">
          <el-input v-model="profile.cover_url" placeholder="个人资料页封面图" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 社交链接 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header-row">
          <span>社交链接</span>
          <el-button type="primary" size="small" @click="openAddLink">
            <el-icon><Plus /></el-icon>添加
          </el-button>
        </div>
      </template>
      <el-table :data="(profile.social_links as any)" stripe style="width: 100%">
        <el-table-column prop="icon" label="图标" width="60" />
        <el-table-column prop="label" label="平台" width="120" />
        <el-table-column prop="url" label="链接" min-width="250">
          <template #default="{ row }: { row: any }">
            <a :href="row.url" target="_blank" class="link-text">{{ row.url }}</a>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="60" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }: { row: any }">
            <el-button type="danger" link size="small" @click="deleteLink(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加社交链接弹窗 -->
    <el-dialog v-model="showLinkDialog" title="添加社交链接" width="420px">
      <el-form label-position="top">
        <el-form-item label="平台名称">
          <el-input v-model="linkForm.label" placeholder="如 GitHub、Bilibili" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="linkForm.icon" placeholder="图标标识（如 github）" />
        </el-form-item>
        <el-form-item label="链接 URL">
          <el-input v-model="linkForm.url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number v-model="linkForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showLinkDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingLink" @click="saveLink">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.profile-edit-page { display: flex; flex-direction: column; gap: 20px; }
.section-card { border-radius: 12px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; }
.link-text { color: #409eff; text-decoration: none; font-size: 13px; }
.link-text:hover { text-decoration: underline; }
</style>
