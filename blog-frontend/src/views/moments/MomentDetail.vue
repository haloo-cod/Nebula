<template>
  <Teleport to="body">
    <Transition name="detail-fade">
      <div v-if="moment" class="detail-overlay" @click.self="close">
        <!-- 关闭按钮 -->
        <button class="detail-close" aria-label="关闭" @click="close">✕</button>

        <!-- 详情面板 -->
        <div class="detail-panel-wrap">
          <!-- 毛玻璃背景层 -->
          <PanelFallbackGlass class="detail-fallback" />

          <!-- 内容滚动层 -->
          <div class="detail-content">
            <DetailInner :moment="moment" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * 说说详情 overlay 面板
 * 点击卡片后弹出,展示完整内容(图片、标签、评论)
 *
 * 布局策略:
 * .detail-panel-wrap (position: relative, height: 85vh) 作为唯一确定高度的 positioned ancestor.
 * 毛玻璃背景层和内容层都用 position: absolute; inset: 0 引用同一个祖先,
 * 因此背景和内容的高度天然一致,无视觉错位.
 */
import { onMounted, onUnmounted } from 'vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import type { Moment } from '@/types'
import DetailInner from './MomentDetailInner.vue'

defineProps<{
  moment: Moment | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

function close() {
  emit('close')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* ===== 遮罩层 ===== */
.detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 8000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

/* ===== 关闭按钮 ===== */
.detail-close {
  position: fixed;
  top: 1.2rem;
  right: 1.2rem;
  z-index: 8001;
  width: 2.4rem;
  height: 2.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.detail-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/*
 * 面板容器:
 * - position: relative + height: 85vh → 唯一确定高度的 positioned ancestor
 * - 所有子层(毛玻璃背景、内容)都用 position: absolute; inset: 0 引用此容器
 */
.detail-panel-wrap {
  position: relative;
  width: 100%;
  max-width: 50rem;
  height: 85vh;
  border-radius: 1.3rem;
  overflow: hidden;
}

/* ===== 毛玻璃背景层 ===== */
.detail-fallback {
  position: absolute;
  inset: 0;
  border-radius: 1.3rem;
}

/*
 * 内容滚动层:
 * - 和毛玻璃背景平级,同样 position: absolute; inset: 0 → 高度 = 85vh
 * - z-index: 2 在背景层上方
 * - 内容超过 85vh 时 overflow-y: auto 触发滚动
 */
.detail-content {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1.8rem 1.6rem;
}

/* 自定义滚动条 */
.detail-content::-webkit-scrollbar {
  width: 4px;
}

.detail-content::-webkit-scrollbar-track {
  background: transparent;
}

.detail-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
}

/* ===== 过渡动画 ===== */
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.detail-fade-enter-active .detail-panel-wrap,
.detail-fade-leave-active .detail-panel-wrap {
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
}

.detail-fade-enter-from .detail-panel-wrap {
  transform: scale(0.92) translateY(20px);
}

.detail-fade-leave-to .detail-panel-wrap {
  transform: scale(0.95) translateY(10px);
}
</style>

<style>
/* ============================================
   light 模式详情面板适配
   通过 .detail-overlay 前缀限定作用范围,不影响其他组件
   ============================================ */

/* 遮罩层:柔和的浅灰半透明,避免纯白刺眼 */
[data-theme='light'] .detail-overlay {
  background: rgba(240, 240, 245, 0.45);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

/* 关闭按钮:深色系,在白色遮罩上可见 */
[data-theme='light'] .detail-overlay .detail-close {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.6);
}

[data-theme='light'] .detail-overlay .detail-close:hover {
  background: rgba(0, 0, 0, 0.12);
}

/* 面板背景:带微灰调的半透明白底,柔和且保证文字可读 */
[data-theme='light'] .detail-overlay .panel-fallback-glass {
  background: rgba(248, 248, 250, 0.72);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.7),
    0 8px 32px rgba(0, 0, 0, 0.08);
}

/* 滚动条 thumb:深色,在白底面板上可见 */
[data-theme='light'] .detail-overlay .detail-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
}
</style>
