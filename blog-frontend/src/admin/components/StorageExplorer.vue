<script setup lang="ts">
/** 目录浏览：合并展示本地文件、R2 记录与本地副本，管理操作仍使用业务页面。 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type LoadFunction, type TreeInstance } from 'element-plus'
import { Document, FolderOpened, Refresh, ArrowUp } from '@element-plus/icons-vue'
import {
  browseStorage,
  type StorageBrowseResponse,
  type StorageDirectory,
  type StorageEntry,
  type StorageRoot,
} from '@/api/storage'
import { resolveUrl } from '@/api/client'
import '@/assets/styles/storage-explorer.css'

/** 左侧目录树节点，根目录与相对路径共同确定身份。 */
interface FolderNode {
  key: string
  name: string
  root: StorageRoot
  path: string
}

/** 复用组件库的懒加载节点类型。 */
type LazyFolderNode = Parameters<LoadFunction>[0]

/** 旧文件库支持的三个管理标签。 */
type LibraryTab = 'files' | 'images' | 'archives'

const emit = defineEmits<{ library: [tab: LibraryTab] }>()
/** 文件库操作后返回目录时，保留位置并刷新文件状态。 */
const props = defineProps<{ visible: boolean }>()
const router = useRouter()
const tree = ref<TreeInstance>()
const roots: FolderNode[] = [
  { key: 'uploads/', name: 'uploads · 上传资源', root: 'uploads', path: '' },
  { key: 'content/', name: 'content · 内容原文件', root: 'content', path: '' },
]
const current = ref<FolderNode>(roots[0]!)
const listing = ref<StorageBrowseResponse | null>(null)
const page = ref(1)
const pageSize = 50
const loading = ref(false)
const error = ref('')
let requestId = 0
let active = true

const breadcrumbs = computed(() => {
  const parts = current.value.path.split('/').filter(Boolean)
  return [
    { name: current.value.root, path: '' },
    ...parts.map((name, index) => ({ name, path: parts.slice(0, index + 1).join('/') })),
  ]
})

/** 创建稳定的树节点，不把服务器绝对路径暴露给前台。 */
function folderNode(root: StorageRoot, folder: StorageDirectory): FolderNode {
  return { ...folder, root, key: `${root}/${folder.path}` }
}

/** 按展开层级加载目录，失败时允许再次展开重试。 */
async function loadTree(
  node: LazyFolderNode,
  resolve: (nodes: FolderNode[]) => void,
  reject: () => void,
) {
  if (node.level === 0) return resolve(roots)
  // 树的数据仅由本组件的 roots 和 folderNode 生成，在组件库边界恢复节点类型。
  const folder = node.data as FolderNode
  try {
    const response = await browseStorage(folder.root, folder.path, 1, 1)
    if (!active) return
    resolve(response.directories.map((directory) => folderNode(folder.root, directory)))
  } catch (err: unknown) {
    if (!active) return
    reject()
    ElMessage.error(err instanceof Error ? err.message : '加载子目录失败')
  }
}

/** 后发请求优先，避免快速切目录时较早响应覆盖当前位置。 */
async function loadDirectory() {
  const request = ++requestId
  const { root, path } = current.value
  loading.value = true
  error.value = ''
  listing.value = null
  try {
    const result = await browseStorage(root, path, page.value, pageSize)
    if (!active || request !== requestId) return
    listing.value = result
    const node = tree.value?.getNode(`${root}/${path}`)
    if (node?.loaded) {
      // 仅增删变化的目录，保留其他节点的展开状态及已加载的子目录。
      const keys = new Set(result.directories.map((folder) => `${root}/${folder.path}`))
      for (const child of [...node.childNodes]) {
        if (!keys.has(String(child.key))) tree.value?.remove(child)
      }
      for (const folder of result.directories) {
        const child = folderNode(root, folder)
        if (!tree.value?.getNode(child.key)) tree.value?.append(child, node)
      }
    }
  } catch (err: unknown) {
    if (active && request === requestId)
      error.value = err instanceof Error ? err.message : '加载目录失败'
  } finally {
    if (active && request === requestId) loading.value = false
  }
}

/** 目录按钮、左树和面包屑使用同一导航逻辑。 */
function openDirectory(node: FolderNode) {
  current.value = node
  page.value = 1
  tree.value?.setCurrentKey(node.key)
  tree.value?.getNode(node.key)?.expand()
  void loadDirectory()
}

/** 在当前业务根目录下进入相对路径。 */
function openPath(path: string) {
  openDirectory(
    folderNode(current.value.root, { name: path.split('/').pop() || current.value.root, path }),
  )
}

/** 文件行来自后端固定响应结构，收窄组件库默认的宽松行类型。 */
function entry(row: unknown): StorageEntry {
  // 表格 data 只绑定 StorageEntry[]，因此在插槽边界恢复该类型。
  return row as StorageEntry
}

function formatSize(size: number | null): string {
  if (size === null) return '未知'
  if (size < 1024) return `${size} B`
  if (size < 1024 ** 2) return `${(size / 1024).toFixed(1)} KB`
  if (size < 1024 ** 3) return `${(size / 1024 ** 2).toFixed(1)} MB`
  return `${(size / 1024 ** 3).toFixed(1)} GB`
}

function formatTime(value: string | null): string {
  if (!value) return '—'
  const date = new Date(/[zZ]|[+\-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

/** 管理入口复用原文件库及各业务页面，文件身份和引用关系不变。 */
function manageFile(file: StorageEntry) {
  const tabs: Record<string, LibraryTab> = {
    file: 'files',
    image: 'images',
    book_archive: 'archives',
  }
  const tab = file.record_kind ? tabs[file.record_kind] : undefined
  if (tab) emit('library', tab)
  else if (file.manage_url) void router.push(file.manage_url)
}

async function copyPath(value: string) {
  try {
    await navigator.clipboard.writeText(value)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败，请手动选择文本复制')
  }
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) void loadDirectory()
    else {
      requestId++
      loading.value = false
    }
  },
)
onMounted(() => {
  if (props.visible) void loadDirectory()
})
onBeforeUnmount(() => {
  active = false
  requestId++
})
</script>

<template>
  <section class="storage-explorer" aria-label="文件目录浏览">
    <aside class="storage-directory-pane" aria-label="目录树">
      <h3>目录</h3>
      <el-tree
        ref="tree"
        node-key="key"
        :props="{ label: 'name' }"
        :load="loadTree"
        lazy
        highlight-current
        :expand-on-click-node="false"
        :current-node-key="current.key"
        :default-expanded-keys="['uploads/']"
        @node-click="openDirectory"
      >
        <template #default="{ data }">
          <span class="storage-tree-label" :title="data.name">
            <el-icon><FolderOpened /></el-icon>
            <span>{{ data.name }}</span>
          </span>
        </template>
      </el-tree>
    </aside>

    <div class="storage-file-pane">
      <div class="storage-directory-toolbar">
        <el-breadcrumb separator="/" aria-label="当前目录">
          <el-breadcrumb-item v-for="crumb in breadcrumbs" :key="crumb.path">
            <button type="button" @click="openPath(crumb.path)">{{ crumb.name }}</button>
          </el-breadcrumb-item>
        </el-breadcrumb>
        <div class="storage-directory-actions">
          <el-button
            :icon="ArrowUp"
            :disabled="!current.path"
            @click="openPath(current.path.split('/').slice(0, -1).join('/'))"
            >上一级</el-button
          >
          <el-button :icon="Refresh" :loading="loading" @click="loadDirectory">刷新</el-button>
        </div>
      </div>
      <p class="storage-directory-note">
        本地文件与已登记的 R2 对象合并展示；R2 记录不代表服务器没有本地副本。
      </p>
      <el-alert
        v-if="listing && !listing.r2_enabled"
        type="info"
        :closable="false"
        title="当前环境未启用 R2，仍可查看数据库中已有的 R2 记录。"
      />
      <el-alert v-if="error" :title="error" type="error" :closable="false">
        <el-button link type="primary" @click="loadDirectory">重试</el-button>
      </el-alert>

      <div v-loading="loading" class="storage-directory-content">
        <div v-if="listing?.directories.length" class="storage-subdirectories" aria-label="子目录">
          <el-button
            v-for="folder in listing.directories"
            :key="folder.path"
            :icon="FolderOpened"
            @click="openPath(folder.path)"
          >
            {{ folder.name }}
          </el-button>
        </div>
        <el-table
          v-if="listing?.items.length"
          :data="listing.items"
          row-key="path"
          class="storage-file-table"
        >
          <el-table-column type="expand" width="42">
            <template #default="{ row }">
              <dl class="storage-file-details">
                <dt>相对路径</dt>
                <dd>{{ current.root }}/{{ entry(row).path }}</dd>
                <dt>关联记录</dt>
                <dd>
                  {{
                    entry(row).record_kind
                      ? `${entry(row).record_kind} #${entry(row).record_id}`
                      : '无关联记录'
                  }}
                </dd>
                <dt>R2 对象键</dt>
                <dd>{{ entry(row).r2_key || '—' }}</dd>
                <dt>R2 地址</dt>
                <dd>{{ entry(row).r2_url || '—' }}</dd>
                <dt>站内地址</dt>
                <dd>{{ entry(row).url ? resolveUrl(entry(row).url!) : '—' }}</dd>
              </dl>
            </template>
          </el-table-column>
          <el-table-column label="文件" min-width="260">
            <template #default="{ row }">
              <div class="storage-file-name">
                <el-icon><Document /></el-icon><span>{{ entry(row).name }}</span>
              </div>
              <span
                v-if="entry(row).title && entry(row).title !== entry(row).name"
                class="storage-file-title"
                >{{ entry(row).title }}</span
              >
            </template>
          </el-table-column>
          <el-table-column label="存储位置" width="140">
            <template #default="{ row }">
              <el-tag v-if="entry(row).storage_backend === 'r2'" type="primary">R2</el-tag>
              <el-tag v-else-if="entry(row).local_exists" type="info">本地</el-tag>
              <el-tag v-else type="danger">本地缺失</el-tag>
              <span v-if="!entry(row).record_kind" class="storage-file-title">无关联记录</span>
            </template>
          </el-table-column>
          <el-table-column label="本地副本" width="110">
            <template #default="{ row }">{{ entry(row).local_exists ? '存在' : '无' }}</template>
          </el-table-column>
          <el-table-column label="大小" width="110">
            <template #default="{ row }">{{ formatSize(entry(row).file_size) }}</template>
          </el-table-column>
          <el-table-column label="修改 / 登记时间" min-width="180">
            <template #default="{ row }">{{ formatTime(entry(row).modified_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button link @click="copyPath(`${current.root}/${entry(row).path}`)"
                >复制路径</el-button
              >
              <el-button
                v-if="entry(row).manage_url"
                link
                type="primary"
                @click="manageFile(entry(row))"
                >管理</el-button
              >
            </template>
          </el-table-column>
        </el-table>
        <el-empty
          v-if="listing && !listing.items.length && !listing.directories.length"
          description="此目录为空"
        />
      </div>
      <div v-if="listing" class="storage-directory-footer">
        <span>{{ listing.directories.length }} 个文件夹 · {{ listing.total }} 个文件</span>
        <el-pagination
          v-if="listing.total > pageSize"
          v-model:current-page="page"
          :page-size="pageSize"
          :total="listing.total"
          layout="prev, pager, next"
          @current-change="loadDirectory"
        />
      </div>
    </div>
  </section>
</template>
