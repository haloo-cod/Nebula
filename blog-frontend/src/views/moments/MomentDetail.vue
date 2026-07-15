<template>
  <Teleport to="body">
    <Transition name="detail-fade">
      <div v-if="moment" class="detail-overlay" @click.self="close">
        <!-- 关闭按钮 -->
        <button class="detail-close" aria-label="关闭" @click="close">✕</button>

        <!-- 详情面板 -->
        <div class="detail-panel-wrap">
          <!-- 液态玻璃背景层(无 slot 内容) -->
          <LazyLiquidGlass
            v-if="ui.liquidGlassEnabled"
            ref="glassRef"
            class="detail-glass"
            :corner-radius="22"
            :theme="ui.theme"
            :blur-radius="ui.liquidGlassBlur"
            :allow-reveal="false"
            :ripple-trail="true"
            realtime-offset
          />

          <!-- fallback 背景层 -->
          <div v-else class="detail-fallback" />

          <!-- 内容滚动层(和液态玻璃平级,都绝对定位引用 .detail-panel-wrap 的确定高度) -->
          <div
            class="detail-content"
            @pointermove="forwardPointer"
            @pointerenter="forwardPointer"
            @pointerleave="forwardPointer"
          >
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
 * 液态玻璃背景层和内容层都用 position: absolute; inset: 0 引用同一个祖先,
 * 因此 canvas 和内容的高度天然一致,无视觉错位.
 * 涟漪效果通过 forwardPointer 将 pointer 事件转发到液态玻璃容器.
 */
import { ref, onMounted, onUnmounted } from 'vue'
import LazyLiquidGlass from '@/components/liquid-glass/LazyLiquidGlass.vue'
import { useUIStore } from '@/stores/ui'
import type { Moment } from '@/types'
import DetailInner from './MomentDetailInner.vue'

defineProps<{
  moment: Moment | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const ui = useUIStore()
const glassRef = ref<InstanceType<typeof LazyLiquidGlass> | null>(null)

function close() {
  emit('close')
}

/** 把 pointer 事件转发到液态玻璃容器根元素,使涟漪效果正常触发 */
function forwardPointer(e: PointerEvent) {
  const el = glassRef.value?.$el as HTMLElement | undefined
  if (el) {
    el.dispatchEvent(new PointerEvent(e.type, e))
  }
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
 * - 所有子层(玻璃背景、内容)都用 position: absolute; inset: 0 引用此容器
 */
.detail-panel-wrap {
  position: relative;
  width: 100%;
  max-width: 50rem;
  height: 85vh;
  border-radius: 1.3rem;
  overflow: hidden;
}

/*
 * 液态玻璃背景层:
 * 填满面板,作为玻璃效果底层.
 * LiquidGlass 内部 canvas 通过 syncCanvasSize 读取 containerRef 的
 * getBoundingClientRect() 设置尺寸.由于 .detail-glass 是
 * position: absolute; inset: 0,其高度 = 85vh(确定值),
 * syncCanvasSize 挂载时就能读到正确尺寸,无需时序 hack.
 */
.detail-glass {
  position: absolute;
  inset: 0;
  border-radius: 1.3rem;
}

/* ===== fallback 背景层 ===== */
.detail-fallback {
  position: absolute;
  inset: 0;
  border-radius: 1.3rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06),
    0 24px 80px rgba(0, 0, 0, 0.4);
}

/*
 * 内容滚动层:
 * - 和玻璃背景平级,同样 position: absolute; inset: 0 → 高度 = 85vh
 * - 和 canvas 引用同一个面板容器,天然对齐
 * - z-index: 2 在 canvas (z-index: 0) 上方
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
