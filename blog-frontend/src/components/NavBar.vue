<template>
  <nav class="nav-bar">
    <!-- 桌面端导航 -->
    <ul ref="navListRef" class="nav-list">
      <li class="nav-indicator" :style="indicatorStyle"></li>
      <li v-for="(item, index) in navItems" :key="item.path" :ref="(el) => setItemRef(el, index)">
        <RouterLink
          :to="item.path"
          class="nav-link"
          :class="route.path === item.path ? 'nav-link-active' : 'nav-link-inactive'"
          @click="closeMenu"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </li>
    </ul>

    <!-- 移动端菜单按钮 -->
    <button
      class="mobile-toggle"
      :class="{ 'is-open': menuOpen }"
      @click="menuOpen = !menuOpen"
      aria-label="Toggle menu"
    >
      <span></span>
      <span></span>
      <span></span>
    </button>

    <!-- 移动端下拉菜单 -->
    <Transition name="menu-slide">
      <ul v-if="menuOpen" class="mobile-menu">
        <li v-for="item in navItems" :key="item.path">
          <RouterLink
            :to="item.path"
            class="mobile-link"
            :class="route.path === item.path ? 'mobile-link-active' : 'mobile-link-inactive'"
            @click="closeMenu"
          >
            <span class="nav-icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </li>
      </ul>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const navItems = [
  { label: '首页', path: '/', icon: '🏠' },
  { label: '文章', path: '/post', icon: '📄' },
  { label: '图库', path: '/gallery', icon: '🖼️' },
  { label: '其他', path: '/other', icon: '📌' },
  { label: '关于', path: '/about', icon: '👤' },
]

const route = useRoute()
const menuOpen = ref(false)
const navListRef = ref(null)
const itemRefs = ref([])
const indicatorStyle = ref({ left: '0px', width: '0px', opacity: '0' })

function setItemRef(el, index) {
  itemRefs.value[index] = el
}

function closeMenu() {
  menuOpen.value = false
}

function updateIndicator() {
  if (!navListRef.value) return
  const idx = navItems.findIndex((item) => item.path === route.path)
  if (idx === -1) {
    indicatorStyle.value = { left: '0px', width: '0px', opacity: '0' }
    return
  }
  const el = itemRefs.value[idx]
  if (!el) return
  const listRect = navListRef.value.getBoundingClientRect()
  const itemRect = el.getBoundingClientRect()
  indicatorStyle.value = {
    left: `${itemRect.left - listRect.left}px`,
    width: `${itemRect.width}px`,
    opacity: '1',
  }
}

let observer = null

onMounted(() => {
  nextTick(updateIndicator)
  observer = new ResizeObserver(updateIndicator)
  if (navListRef.value) observer.observe(navListRef.value)
  window.addEventListener('resize', updateIndicator)
})

watch(
  () => route.path,
  () => nextTick(updateIndicator),
)

onUnmounted(() => {
  observer?.disconnect()
  window.removeEventListener('resize', updateIndicator)
})
</script>

<style scoped>
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  justify-content: center;
  padding-top: 2rem;
  padding-left: 1rem;
  padding-right: 1rem;
}

/* 桌面导航列表 */
.nav-list {
  display: none;
}

@media (min-width: 768px) {
  .nav-list {
    position: relative;
    display: flex;
    align-items: center;
    gap: 3rem;
    padding: 1rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
}

.nav-indicator {
  position: absolute;
  top: 16px;
  height: calc(100% - 32px);
  border-radius: 9999px;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(16px);
  box-shadow:
    0 2px 24px rgba(255, 255, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transition:
    left 0.5s cubic-bezier(0.34, 1.56, 0.64, 1),
    width 0.5s cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 0.3s ease;
}

.nav-link {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 14px 32px;
  font-size: 29px;
  font-weight: 600;
  border-radius: 9999px;
  transition: color 0.3s ease;
}

.nav-link-inactive {
  color: rgba(255, 255, 255, 0.55);
}

.nav-link-inactive:hover {
  color: rgba(255, 255, 255, 0.85);
}

.nav-link-active {
  color: #1a1a2e;
}

.nav-icon {
  font-size: 20px;
  line-height: 1;
}

/* 移动端按钮 */
.mobile-toggle {
  position: absolute;
  top: 2rem;
  right: 1.5rem;
  z-index: 60;
  width: 44px;
  height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  cursor: pointer;
  transition: background 0.3s ease;
}

@media (min-width: 768px) {
  .mobile-toggle {
    display: none;
  }
}

.mobile-toggle:hover {
  background: rgba(255, 255, 255, 0.15);
}

.mobile-toggle span {
  display: block;
  width: 20px;
  height: 2px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 2px;
  transition: all 0.3s ease;
  transform-origin: center;
}

.mobile-toggle.is-open span:nth-child(1) {
  transform: translateY(8px) rotate(45deg);
}

.mobile-toggle.is-open span:nth-child(2) {
  opacity: 0;
  transform: scaleX(0);
}

.mobile-toggle.is-open span:nth-child(3) {
  transform: translateY(-8px) rotate(-45deg);
}

/* 移动端菜单 */
.mobile-menu {
  position: fixed;
  top: 6rem;
  left: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 1.5rem;
  background: rgba(30, 30, 50, 0.85);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
}

@media (min-width: 768px) {
  .mobile-menu {
    display: none;
  }
}

.mobile-link {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 16px 24px;
  font-size: 20px;
  font-weight: 600;
  border-radius: 1rem;
  transition: all 0.3s ease;
}

.mobile-link-inactive {
  color: rgba(255, 255, 255, 0.65);
}

.mobile-link-inactive:hover {
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.06);
}

.mobile-link-active {
  color: #1a1a2e;
  background: rgba(255, 255, 255, 0.5);
}

/* 菜单动画 */
.menu-slide-enter-active {
  transition: all 0.3s ease;
}

.menu-slide-leave-active {
  transition: all 0.2s ease;
}

.menu-slide-enter-from {
  opacity: 0;
  transform: translateY(-12px);
}

.menu-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
