<script setup lang="ts">
/**
 * 友链管理 — 列表页
 * 表格展示所有友链，支持新建、编辑、删除
 */
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, ApiError } from '@/api/client'
import {
  resolveFriendRssUrl,
  syncFriendsJson,
  type ApiFriendItem,
  type FriendExchangeInfo,
} from '@/api/friends'
import FriendApplicationsPanel from './FriendApplicationsPanel.vue'

const loading = ref(false)
const friends = ref<ApiFriendItem[]>([])
const showDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const editingId = ref(0)
const form = ref({ name: '', bio: '', avatar: '', url: '', rss_url: '', sort_order: 0 })
const exchangeInfo = ref<FriendExchangeInfo>({
  name: '',
  url: '',
  avatar: '',
  bio: '',
  requirements: [],
  contact: '',
  rss_url: '',
})
const effectiveRssUrl = computed(() => resolveFriendRssUrl(exchangeInfo.value.rss_url))
const exchangeLoading = ref(false)
const exchangeSaving = ref(false)
const requirementsText = ref('')
const activeTab = ref('friends')
const friendsError = ref('')
const syncFailed = ref(false)
const syncing = ref(false)
const deleting = ref(new Set<number>())
let friendsRequest = 0

/** 加载友链列表 */
async function loadFriends() {
  const request = ++friendsRequest
  loading.value = true
  friendsError.value = ''
  try {
    const res = await api.get<{ items: ApiFriendItem[]; total: number }>('/api/v1/friends', true)
    if (request === friendsRequest) friends.value = res.items
  } catch (error: unknown) {
    if (request === friendsRequest)
      friendsError.value = error instanceof Error ? error.message : '加载友链失败'
  } finally {
    if (request === friendsRequest) loading.value = false
  }
}

/** 已保存的写操作失败后只重建副本。 */
async function handleSync() {
  if (syncing.value) return
  syncing.value = true
  try {
    await syncFriendsJson()
    syncFailed.value = false
    ElMessage.success('JSON 已同步')
  } catch (error: unknown) {
    syncFailed.value = true
    ElMessage.error(error instanceof Error ? error.message : 'JSON 同步失败')
  } finally {
    syncing.value = false
  }
}

/** 加载交换友链展示信息。 */
async function loadExchangeInfo() {
  exchangeLoading.value = true
  try {
    exchangeInfo.value = await api.get<FriendExchangeInfo>('/api/v1/friends/exchange-info', true)
    requirementsText.value = exchangeInfo.value.requirements.join('\n')
  } catch {
    ElMessage.error('加载交换友链信息失败')
  } finally {
    exchangeLoading.value = false
  }
}

/** 保存交换友链展示信息。 */
async function saveExchangeInfo() {
  exchangeSaving.value = true
  try {
    exchangeInfo.value = await api.put<FriendExchangeInfo>(
      '/api/v1/friends/exchange-info',
      {
        ...exchangeInfo.value,
        requirements: requirementsText.value
          .split('\n')
          .map((item) => item.trim())
          .filter(Boolean),
      },
      true,
    )
    requirementsText.value = exchangeInfo.value.requirements.join('\n')
    ElMessage.success('交换友链信息已保存')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    exchangeSaving.value = false
  }
}

/** 打开新建弹窗 */
function openCreate() {
  isEdit.value = false
  form.value = { name: '', bio: '', avatar: '', url: '', rss_url: '', sort_order: 0 }
  showDialog.value = true
}

/** 打开编辑弹窗 */
function openEdit(item: ApiFriendItem) {
  isEdit.value = true
  editingId.value = item.id
  form.value = {
    name: item.name,
    bio: item.bio,
    avatar: item.avatar,
    url: item.url,
    rss_url: item.rss_url,
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

/** 保存 */
async function handleSave() {
  if (saving.value) return
  if (!form.value.name.trim() || !form.value.url.trim()) {
    ElMessage.warning('站名和 URL 不能为空')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await api.put(`/api/v1/friends/${editingId.value}`, form.value, true)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/friends', form.value, true)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    syncFailed.value = false
    await loadFriends()
  } catch (err: unknown) {
    if (err instanceof ApiError && err.status === 503 && err.detail === 'FRIEND_JSON_SYNC_FAILED') {
      showDialog.value = false
      syncFailed.value = true
      await loadFriends()
      ElMessage.warning('数据已保存，JSON 同步失败')
    } else {
      ElMessage.error(err instanceof Error ? err.message : '保存失败')
    }
  } finally {
    saving.value = false
  }
}

/** 删除 */
async function handleDelete(item: ApiFriendItem) {
  if (deleting.value.has(item.id)) return
  deleting.value.add(item.id)
  try {
    await ElMessageBox.confirm(
      `确定删除友链「${item.name}」？如有关联申请，将同时删除该申请及全部讨论。`,
      '确认删除',
      { type: 'warning' },
    )
    await api.delete(`/api/v1/friends/${item.id}`)
    syncFailed.value = false
    ElMessage.success('删除成功')
    await loadFriends()
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') return
    if (
      error instanceof ApiError &&
      error.status === 503 &&
      error.detail === 'FRIEND_JSON_SYNC_FAILED'
    ) {
      syncFailed.value = true
      await loadFriends()
      ElMessage.warning('数据已保存，JSON 同步失败')
    } else {
      ElMessage.error(error instanceof Error ? error.message : '删除失败')
    }
  } finally {
    deleting.value.delete(item.id)
  }
}

onMounted(() => {
  loadFriends()
  loadExchangeInfo()
})

onUnmounted(() => {
  ++friendsRequest
})
</script>

<template>
  <div class="friend-list-page">
    <el-alert
      v-if="syncFailed"
      title="数据已保存，JSON 同步失败"
      type="warning"
      :closable="false"
      show-icon
    />
    <el-tabs v-model="activeTab">
      <el-tab-pane label="友链管理" name="friends">
        <div class="friend-list-page">
          <el-alert
            v-if="friendsError"
            :title="friendsError"
            type="error"
            :closable="false"
            show-icon
          >
            <el-button link @click="loadFriends">重新加载</el-button>
          </el-alert>
          <div class="page-header">
            <span class="page-title">共 {{ friends.length }} 条友链</span>
            <el-space>
              <el-button :loading="syncing" @click="handleSync">重新同步 JSON</el-button>
              <el-button type="primary" @click="openCreate">
                <el-icon><Plus /></el-icon>新增友链
              </el-button>
            </el-space>
          </div>

          <el-card shadow="never" class="table-card">
            <el-table
              :data="friends"
              v-loading="loading"
              stripe
              style="width: 100%"
              empty-text="暂无友链"
            >
              <el-table-column prop="name" label="站名" width="140" />
              <el-table-column prop="bio" label="简介" min-width="200" />
              <!-- @vue-generic {ApiFriendItem} -->
              <el-table-column prop="avatar" label="头像" width="70">
                <template #default="{ row }: { row: ApiFriendItem }">
                  <img v-if="row.avatar" :src="row.avatar" class="avatar-img" alt="" />
                  <span v-else>—</span>
                </template>
              </el-table-column>
              <!-- @vue-generic {ApiFriendItem} -->
              <el-table-column prop="url" label="链接" min-width="200">
                <template #default="{ row }: { row: ApiFriendItem }">
                  <a :href="row.url" target="_blank" rel="noopener noreferrer" class="link-text">{{
                    row.url
                  }}</a>
                </template>
              </el-table-column>
              <!-- @vue-generic {ApiFriendItem} -->
              <el-table-column prop="rss_url" label="RSS" min-width="180">
                <template #default="{ row }: { row: ApiFriendItem }">
                  <a
                    v-if="row.rss_url"
                    :href="row.rss_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="link-text"
                    >{{ row.rss_url }}</a
                  >
                  <span v-else>—</span>
                </template>
              </el-table-column>
              <el-table-column prop="sort_order" label="排序" width="70" />
              <!-- @vue-generic {ApiFriendItem} -->
              <el-table-column label="操作" width="140" fixed="right">
                <template #default="{ row }: { row: ApiFriendItem }">
                  <el-button type="primary" link size="small" @click="openEdit(row)"
                    >编辑</el-button
                  >
                  <el-button
                    type="danger"
                    link
                    size="small"
                    :loading="deleting.has(row.id)"
                    @click="handleDelete(row)"
                    >删除</el-button
                  >
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <el-card shadow="never" class="table-card" v-loading="exchangeLoading">
            <template #header>
              <span>交换友链</span>
            </template>
            <el-form label-position="top">
              <div class="form-grid">
                <el-form-item label="站点名称">
                  <el-input
                    v-model="exchangeInfo.name"
                    placeholder="展示在交换友链区域的站点名称"
                  />
                </el-form-item>
                <el-form-item label="站点 URL">
                  <el-input v-model="exchangeInfo.url" placeholder="https://..." />
                </el-form-item>
                <el-form-item label="头像 URL">
                  <el-input v-model="exchangeInfo.avatar" placeholder="https://..." />
                </el-form-item>
                <el-form-item label="联系方式">
                  <el-input v-model="exchangeInfo.contact" placeholder="邮箱或其他联系方式" />
                </el-form-item>
                <el-form-item label="RSS 订阅地址">
                  <el-input
                    v-model="exchangeInfo.rss_url"
                    placeholder="留空自动使用本站 RSS"
                    maxlength="2048"
                  />
                  <div class="rss-address-hint">
                    当前有效地址：<a
                      :href="effectiveRssUrl"
                      target="_blank"
                      rel="noopener noreferrer"
                      >{{ effectiveRssUrl }}</a
                    >
                  </div>
                </el-form-item>
              </div>
              <el-form-item label="站点简介">
                <el-input v-model="exchangeInfo.bio" type="textarea" :rows="2" />
              </el-form-item>
              <el-form-item label="申请要求（每行一条）">
                <el-input
                  v-model="requirementsText"
                  type="textarea"
                  :rows="4"
                  placeholder="原创内容优先&#10;站点稳定可访问"
                />
              </el-form-item>
              <div class="exchange-form-actions">
                <el-button type="primary" :loading="exchangeSaving" @click="saveExchangeInfo">
                  保存设置
                </el-button>
              </div>
            </el-form>
          </el-card>

          <!-- 新建/编辑弹窗 -->
          <el-dialog v-model="showDialog" :title="isEdit ? '编辑友链' : '新增友链'" width="460px">
            <el-form label-position="top" :disabled="saving">
              <el-form-item label="站名">
                <el-input v-model="form.name" placeholder="友链站点名称" />
              </el-form-item>
              <el-form-item label="简介">
                <el-input v-model="form.bio" placeholder="一句话介绍" />
              </el-form-item>
              <el-form-item label="头像 URL">
                <el-input v-model="form.avatar" placeholder="https://..." />
              </el-form-item>
              <el-form-item label="站点 URL">
                <el-input v-model="form.url" placeholder="https://..." />
              </el-form-item>
              <el-form-item label="RSS 地址（选填）">
                <el-input
                  v-model="form.rss_url"
                  maxlength="2048"
                  placeholder="https://.../rss.xml，留空不显示订阅"
                />
              </el-form-item>
              <el-form-item label="排序权重（越小越靠前）">
                <el-input-number v-model="form.sort_order" :min="0" />
              </el-form-item>
            </el-form>
            <template #footer>
              <el-button @click="showDialog = false">取消</el-button>
              <el-button type="primary" :loading="saving" @click="handleSave">{{
                isEdit ? '更新' : '创建'
              }}</el-button>
            </template>
          </el-dialog>
        </div>
      </el-tab-pane>
      <el-tab-pane label="申请审核" name="applications" lazy>
        <FriendApplicationsPanel @changed="loadFriends" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.rss-address-hint {
  margin-top: 6px;
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.friend-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  font-size: 14px;
  color: var(--admin-text-secondary, #909399);
}
.table-card {
  border-radius: 12px;
}
.exchange-form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}
.avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}
.link-text {
  color: #409eff;
  text-decoration: none;
  font-size: 13px;
}
.link-text:hover {
  text-decoration: underline;
}
</style>
