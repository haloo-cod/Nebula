<script setup lang="ts">
/** 后台用户管理：账户搜索、状态管理和安全操作。 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshRight } from '@element-plus/icons-vue'
import { api, resolveUrl } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'

/** 用户列表项。 */
interface UserItem {
  id: number
  username: string
  email: string | null
  display_name: string
  avatar_url: string
  github_id: string | null
  password_hash?: string
  email_verified: boolean
  is_admin: boolean
  is_active: boolean
  last_login_at: string | null
  created_at: string
}

const showEditDialog = ref(false)
const showPasswordDialog = ref(false)
const saving = ref(false)
const resetting = ref(false)
const editingUser = ref<UserItem | null>(null)
const editForm = ref({
  email: '',
  display_name: '',
  email_verified: false,
  is_admin: false,
  is_active: true,
})
const passwordForm = ref({ password: '', confirm: '' })

const {
  loading,
  data,
  keyword,
  pagination,
  loadData,
  handleSearch,
  handlePageChange,
  handleSizeChange,
} = useAdminTable<UserItem>({
  fetchData: ({ page, pageSize, keyword: search }) => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
    if (search) params.set('keyword', search)
    return api.get<{ items: UserItem[]; total: number }>(`/api/v1/users?${params}`, true)
  },
  defaultPageSize: 15,
})

const userRows = computed(() => data.value)

/** 打开编辑弹窗。 */
function openEdit(user: UserItem) {
  editingUser.value = user
  editForm.value = {
    email: user.email || '',
    display_name: user.display_name || user.username,
    email_verified: user.email_verified,
    is_admin: user.is_admin,
    is_active: user.is_active,
  }
  showEditDialog.value = true
}

/** 保存用户资料和权限。 */
async function saveEdit() {
  if (!editingUser.value || !editForm.value.display_name.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }
  saving.value = true
  try {
    await api.put(`/api/v1/users/${editingUser.value.id}`, editForm.value, true)
    ElMessage.success('用户信息已更新')
    showEditDialog.value = false
    await loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

/** 打开重置密码弹窗。 */
function openPassword(user: UserItem) {
  editingUser.value = user
  passwordForm.value = { password: '', confirm: '' }
  showPasswordDialog.value = true
}

/** 重置密码并撤销用户旧会话。 */
async function resetPassword() {
  if (!editingUser.value) return
  if (
    passwordForm.value.password.length < 8 ||
    passwordForm.value.password !== passwordForm.value.confirm
  ) {
    ElMessage.warning('请输入至少 8 位且两次一致的新密码')
    return
  }
  resetting.value = true
  try {
    await api.post(
      `/api/v1/users/${editingUser.value.id}/reset-password`,
      { password: passwordForm.value.password },
      true,
    )
    ElMessage.success('密码已重置，旧登录会话已撤销')
    showPasswordDialog.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '重置密码失败')
  } finally {
    resetting.value = false
  }
}

/** 撤销该用户的全部登录会话。 */
async function revokeSessions(user: UserItem) {
  try {
    await ElMessageBox.confirm(`确定撤销「${user.username}」的全部登录会话吗？`, '确认操作', {
      type: 'warning',
    })
    await api.post(`/api/v1/users/${user.id}/revoke-sessions`, undefined, true)
    ElMessage.success('登录会话已撤销')
  } catch {
    // 取消操作不提示
  }
}

/** 删除用户。 */
async function deleteUser(user: UserItem) {
  try {
    await ElMessageBox.confirm(`确定删除用户「${user.username}」吗？评论内容会保留。`, '危险操作', {
      type: 'error',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await api.delete(`/api/v1/users/${user.id}`, true)
    ElMessage.success('用户已删除')
    await loadData()
  } catch {
    // 取消操作不提示
  }
}

/** GitHub 账户登录标识。 */
function loginMethod(user: UserItem): string {
  if (user.github_id) return 'GitHub'
  return '密码'
}

/** 将 Element Plus 默认表格行收窄为用户记录。 */
function asUser(row: unknown): UserItem {
  return row as UserItem
}

onMounted(() => loadData())
</script>

<template>
  <div class="user-list-page">
    <div class="page-header">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索用户名、邮箱或昵称..."
        style="width: 300px"
        @keyup.enter="handleSearch"
      />
      <el-button :icon="RefreshRight" @click="loadData">刷新</el-button>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="userRows" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="用户" min-width="190">
          <template #default="{ row }">
            <div class="user-cell">
              <img
                v-if="asUser(row).avatar_url"
                :src="resolveUrl(asUser(row).avatar_url)"
                class="avatar"
                alt=""
              />
              <span v-else class="avatar avatar--fallback">{{
                asUser(row).display_name.charAt(0)
              }}</span>
              <div>
                <strong>{{ asUser(row).display_name }}</strong
                ><small>@{{ asUser(row).username }}</small>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="190" />
        <el-table-column label="登录方式" width="120"
          ><template #default="{ row }">{{ loginMethod(asUser(row)) }}</template></el-table-column
        >
        <el-table-column label="状态" width="170">
          <template #default="{ row }">
            <el-tag :type="asUser(row).is_active ? 'success' : 'danger'" size="small">{{
              asUser(row).is_active ? '正常' : '已禁用'
            }}</el-tag>
            <el-tag v-if="asUser(row).is_admin" type="warning" size="small">管理员</el-tag>
            <el-tag v-if="asUser(row).email_verified" type="info" size="small">邮箱已验证</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="170"
          ><template #default="{ row }">{{
            asUser(row).last_login_at?.slice(0, 16).replace('T', ' ') || '从未登录'
          }}</template></el-table-column
        >
        <el-table-column label="注册时间" width="110"
          ><template #default="{ row }">{{
            asUser(row).created_at?.slice(0, 10)
          }}</template></el-table-column
        >
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEdit(asUser(row))"
              >编辑</el-button
            >
            <el-button type="warning" link size="small" @click="openPassword(asUser(row))"
              >重置密码</el-button
            >
            <el-button type="info" link size="small" @click="revokeSessions(asUser(row))"
              >撤销会话</el-button
            >
            <el-button type="danger" link size="small" @click="deleteUser(asUser(row))"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 15, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="showEditDialog" title="编辑用户" width="520px">
      <el-form v-if="editingUser" label-position="top">
        <el-form-item label="用户名"
          ><el-input :model-value="editingUser.username" disabled
        /></el-form-item>
        <el-form-item label="昵称"><el-input v-model="editForm.display_name" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="editForm.email" type="email" /></el-form-item>
        <el-checkbox v-model="editForm.email_verified">邮箱已验证</el-checkbox>
        <el-checkbox v-model="editForm.is_admin">管理员权限</el-checkbox>
        <el-checkbox v-model="editForm.is_active">账户启用</el-checkbox>
      </el-form>
      <template #footer
        ><el-button @click="showEditDialog = false">取消</el-button
        ><el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button></template
      >
    </el-dialog>

    <el-dialog v-model="showPasswordDialog" title="重置密码" width="420px">
      <el-form label-position="top"
        ><el-form-item label="新密码"
          ><el-input v-model="passwordForm.password" type="password" show-password /></el-form-item
        ><el-form-item label="确认密码"
          ><el-input v-model="passwordForm.confirm" type="password" show-password /></el-form-item
      ></el-form>
      <template #footer
        ><el-button @click="showPasswordDialog = false">取消</el-button
        ><el-button type="primary" :loading="resetting" @click="resetPassword"
          >确认重置</el-button
        ></template
      >
    </el-dialog>
  </div>
</template>

<style scoped>
.user-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-card {
  border-radius: 12px;
}
.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-cell strong,
.user-cell small {
  display: block;
}
.user-cell small {
  margin-top: 3px;
  color: var(--admin-text-secondary);
  font-size: 12px;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
}
.avatar--fallback {
  display: grid;
  place-items: center;
  background: var(--admin-menu-active-bg);
  color: var(--admin-primary-color);
  font-weight: 700;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.el-tag + .el-tag {
  margin-left: 4px;
}
</style>
