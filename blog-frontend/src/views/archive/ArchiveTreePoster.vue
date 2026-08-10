<template>
    <div class="archive-tree-page">
      <div class="archive-tree-stage" :style="{ height: `${stageHeight}px` }">
        <svg
          class="archive-tree-svg"
          :viewBox="`0 0 ${stageWidth} ${stageHeight}`"
          preserveAspectRatio="none"
        >
          <defs>
            <filter id="treeSketchGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <g class="tree-sketch" filter="url(#treeSketchGlow)">
            <path v-for="root in rootPaths" :key="root" :d="root" class="tree-root-line" />

            <path :d="trunkLeftPath" class="tree-trunk-outline" />
            <path :d="trunkRightPath" class="tree-trunk-outline" />

            <path v-for="line in barkLines" :key="line" :d="line" class="tree-bark-line" />

            <path
              v-for="branch in branches"
              :key="branch.id"
              :d="branch.path"
              class="tree-branch-line"
            />
            <path v-for="twig in crownTwigs" :key="twig" :d="twig" class="tree-crown-line" />
          </g>
        </svg>

        <div class="archive-tree-layer">
          <div
            v-for="marker in yearMarkers"
            :key="marker.year"
            class="year-marker"
            :style="{ left: `${marker.x}px`, top: `${marker.y}px` }"
          >
            <span class="year-marker-line"></span>
            <span class="year-marker-text">{{ marker.year }}</span>
          </div>

          <div
            v-for="branch in branches"
            :key="`month-${branch.id}`"
            class="month-marker"
            :class="branch.side === 'left' ? 'month-marker--left' : 'month-marker--right'"
            :style="{ left: `${branch.monthX}px`, top: `${branch.monthY}px` }"
          >
            {{ branch.month }} 月
          </div>

          <RouterLink
            v-for="card in cards"
            :key="card.slug"
            :to="`/archive/post/${card.slug}`"
            class="archive-leaf-card"
            :class="card.side === 'left' ? 'archive-leaf-card--left' : 'archive-leaf-card--right'"
            :style="{
              left: `${card.x}px`,
              top: `${card.y}px`,
              transform: `rotate(${card.rotate}deg)`,
            }"
          >
            <span class="archive-leaf-card-pin"></span>
            <span class="archive-leaf-card-string"></span>
            <div class="archive-leaf-card-head">
              <span class="archive-leaf-card-date"
                >{{ card.monthLabel }} / {{ card.dayLabel }}</span
              >
              <span v-if="card.category" class="archive-leaf-card-category">{{
                card.category
              }}</span>
            </div>
            <h3 class="archive-leaf-card-title">{{ card.title }}</h3>
            <p v-if="card.description" class="archive-leaf-card-desc">{{ card.description }}</p>
            <div class="archive-leaf-card-tags">
              <span
                v-for="tag in card.tags.slice(0, 2)"
                :key="`${card.slug}-${tag}`"
                class="archive-leaf-card-tag"
              >
                #{{ tag }}
              </span>
            </div>
          </RouterLink>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { getPosts } from '@/data/posts'
import type { Post } from '@/types'

interface MonthGroup {
  year: string
  month: number
  posts: Post[]
}

interface BranchView {
  id: string
  year: string
  month: number
  side: 'left' | 'right'
  level: 1 | 2 | 3 | 4
  attachX: number
  attachY: number
  endX: number
  endY: number
  monthX: number
  monthY: number
  path: string
}

interface CardView {
  slug: string
  title: string
  description: string
  category: string
  tags: string[]
  side: 'left' | 'right'
  x: number
  y: number
  rotate: number
  monthLabel: string
  dayLabel: string
}

interface YearMarker {
  year: string
  x: number
  y: number
}

const stageWidth = 1320
const stageCenterX = 660
const topPadding = 120
const bottomPadding = 210
const monthGap = 150
const cardWidth = 246
const rootBaseYInset = 42

const posts = getPosts().filter((post) => !post.draft && post.date)

const monthGroups = computed<MonthGroup[]>(() => {
  const grouped = new Map<string, MonthGroup>()

  for (const post of posts) {
    const date = new Date(post.date)
    if (Number.isNaN(date.getTime())) continue
    const year = String(date.getFullYear())
    const month = date.getMonth() + 1
    const key = `${year}-${String(month).padStart(2, '0')}`

    if (!grouped.has(key)) {
      grouped.set(key, { year, month, posts: [] })
    }
    grouped.get(key)!.posts.push(post)
  }

  return [...grouped.values()].sort((a, b) => {
    const yearDiff = Number(a.year) - Number(b.year)
    if (yearDiff !== 0) return yearDiff
    return a.month - b.month
  })
})

const stageHeight = computed(() => {
  const count = Math.max(monthGroups.value.length, 1)
  return topPadding + bottomPadding + count * monthGap
})

const trunkBottomY = computed(() => stageHeight.value - rootBaseYInset)
const trunkTopY = computed(() => topPadding)

function trunkOffset(progress: number) {
  return Math.sin(progress * Math.PI * 1.1) * 32 + Math.sin(progress * Math.PI * 2.3) * 12
}

function trunkHalfWidth(progress: number) {
  return 58 - progress * 34 + Math.sin(progress * Math.PI * 1.6) * 4
}

const trunkLeftPath = computed(() => {
  const bottomY = trunkBottomY.value
  const topY = trunkTopY.value
  const step = 10
  let path = ''
  for (let index = 0; index <= step; index += 1) {
    const progress = index / step
    const y = bottomY - (bottomY - topY) * progress
    const x = stageCenterX + trunkOffset(progress) - trunkHalfWidth(progress)
    path += `${index === 0 ? 'M' : ' L'} ${x} ${y}`
  }
  return path
})

const trunkRightPath = computed(() => {
  const bottomY = trunkBottomY.value
  const topY = trunkTopY.value
  const step = 10
  let path = ''
  for (let index = 0; index <= step; index += 1) {
    const progress = index / step
    const y = bottomY - (bottomY - topY) * progress
    const x = stageCenterX + trunkOffset(progress) + trunkHalfWidth(progress)
    path += `${index === 0 ? 'M' : ' L'} ${x} ${y}`
  }
  return path
})

const barkLines = computed(() => {
  const lines: string[] = []
  const offsets = [-18, -6, 10, 22]

  offsets.forEach((baseOffset, lineIndex) => {
    const step = 8
    let path = ''
    for (let index = 0; index <= step; index += 1) {
      const progress = index / step
      const y = trunkBottomY.value - 36 - (trunkBottomY.value - trunkTopY.value - 68) * progress
      const wobble = Math.sin(progress * Math.PI * 2 + lineIndex) * 6
      const x = stageCenterX + trunkOffset(progress) * 0.48 + baseOffset + wobble
      path += `${index === 0 ? 'M' : ' L'} ${x} ${y}`
    }
    lines.push(path)
  })

  return lines
})

const rootPaths = computed(() => {
  const y = trunkBottomY.value
  return [
    `M ${stageCenterX - 44} ${y} C ${stageCenterX - 98} ${y + 18}, ${stageCenterX - 156} ${y + 44}, ${stageCenterX - 228} ${y + 104}`,
    `M ${stageCenterX - 14} ${y} C ${stageCenterX - 56} ${y + 24}, ${stageCenterX - 96} ${y + 64}, ${stageCenterX - 138} ${y + 126}`,
    `M ${stageCenterX + 6} ${y} C ${stageCenterX + 8} ${y + 26}, ${stageCenterX + 2} ${y + 64}, ${stageCenterX + 12} ${y + 112}`,
    `M ${stageCenterX + 24} ${y} C ${stageCenterX + 72} ${y + 18}, ${stageCenterX + 118} ${y + 52}, ${stageCenterX + 186} ${y + 112}`,
    `M ${stageCenterX + 50} ${y} C ${stageCenterX + 108} ${y + 20}, ${stageCenterX + 176} ${y + 48}, ${stageCenterX + 248} ${y + 118}`,
  ]
})

function trunkAnchor(progress: number) {
  const y = trunkBottomY.value - (trunkBottomY.value - trunkTopY.value) * progress
  const x = stageCenterX + trunkOffset(progress)
  return { x, y }
}

const branches = computed<BranchView[]>(() => {
  const total = Math.max(monthGroups.value.length - 1, 1)

  return monthGroups.value.map((group, index) => {
    const progress = index / total
    const side: 'left' | 'right' = index % 2 === 0 ? 'left' : 'right'
    const direction = side === 'left' ? -1 : 1
    const { x: attachX, y: attachY } = trunkAnchor(0.16 + progress * 0.72)

    let level: 1 | 2 | 3 | 4 = 2
    if (progress < 0.28) level = 1
    else if (progress < 0.58) level = 2
    else if (progress < 0.82) level = 3
    else level = 4

    let path = ''
    let endX = attachX
    let endY = attachY

    if (level === 1 && side === 'left') {
      endX = attachX - 238
      endY = attachY + 24
      path = `M ${attachX} ${attachY} C ${attachX - 48} ${attachY + 14}, ${attachX - 132} ${attachY + 32}, ${endX} ${endY} M ${attachX - 166} ${attachY + 26} L ${attachX - 206} ${attachY - 18} M ${attachX - 166} ${attachY + 26} L ${attachX - 218} ${attachY + 4}`
    } else if (level === 1 && side === 'right') {
      endX = attachX + 250
      endY = attachY + 10
      path = `M ${attachX} ${attachY} C ${attachX + 56} ${attachY + 10}, ${attachX + 150} ${attachY + 14}, ${endX} ${endY} M ${attachX + 180} ${attachY + 12} L ${attachX + 220} ${attachY - 24} M ${attachX + 180} ${attachY + 12} L ${attachX + 146} ${attachY - 12}`
    } else if (level === 2 && side === 'left') {
      endX = attachX - 230
      endY = attachY - 78
      path = `M ${attachX} ${attachY} C ${attachX - 46} ${attachY - 8}, ${attachX - 138} ${attachY - 46}, ${endX} ${endY} M ${attachX - 184} ${attachY - 58} L ${attachX - 220} ${attachY - 108} M ${attachX - 184} ${attachY - 58} L ${attachX - 194} ${attachY - 120}`
    } else if (level === 2 && side === 'right') {
      endX = attachX + 236
      endY = attachY - 86
      path = `M ${attachX} ${attachY} C ${attachX + 56} ${attachY - 2}, ${attachX + 164} ${attachY - 32}, ${endX} ${endY} M ${attachX + 192} ${attachY - 74} L ${attachX + 212} ${attachY - 136} M ${attachX + 192} ${attachY - 74} L ${attachX + 244} ${attachY - 118}`
    } else if (level === 3 && side === 'left') {
      endX = attachX - 154
      endY = attachY - 56
      path = `M ${attachX} ${attachY} C ${attachX - 34} ${attachY - 6}, ${attachX - 92} ${attachY - 32}, ${endX} ${endY} M ${attachX - 116} ${attachY - 42} L ${attachX - 148} ${attachY - 84} M ${attachX - 116} ${attachY - 42} L ${attachX - 134} ${attachY - 4}`
    } else if (level === 3 && side === 'right') {
      endX = attachX + 160
      endY = attachY - 62
      path = `M ${attachX} ${attachY} C ${attachX + 34} ${attachY - 6}, ${attachX + 92} ${attachY - 30}, ${endX} ${endY} M ${attachX + 116} ${attachY - 42} L ${attachX + 146} ${attachY - 88} M ${attachX + 116} ${attachY - 42} L ${attachX + 136} ${attachY - 2}`
    } else if (side === 'left') {
      endX = attachX - 112
      endY = attachY - 82
      path = `M ${attachX} ${attachY} C ${attachX - 24} ${attachY - 10}, ${attachX - 70} ${attachY - 44}, ${endX} ${endY} M ${attachX - 88} ${attachY - 62} L ${attachX - 112} ${attachY - 106}`
    } else {
      endX = attachX + 114
      endY = attachY - 86
      path = `M ${attachX} ${attachY} C ${attachX + 24} ${attachY - 10}, ${attachX + 72} ${attachY - 46}, ${endX} ${endY} M ${attachX + 92} ${attachY - 66} L ${attachX + 120} ${attachY - 112}`
    }

    return {
      id: `${group.year}-${group.month}`,
      year: group.year,
      month: group.month,
      side,
      level,
      attachX,
      attachY,
      endX,
      endY,
      monthX: endX + direction * 22,
      monthY: endY - 18,
      path,
    }
  })
})

const crownTwigs = computed(() => {
  const x = stageCenterX + trunkOffset(1)
  const y = trunkTopY.value
  return [
    `M ${x} ${y} L ${x - 10} ${y - 56}`,
    `M ${x} ${y} L ${x + 4} ${y - 64}`,
    `M ${x} ${y} L ${x + 20} ${y - 52}`,
    `M ${x - 18} ${y - 12} L ${x - 42} ${y - 42} M ${x - 42} ${y - 42} L ${x - 54} ${y - 66} M ${x - 42} ${y - 42} L ${x - 24} ${y - 68}`,
    `M ${x + 18} ${y - 14} L ${x + 46} ${y - 44} M ${x + 46} ${y - 44} L ${x + 64} ${y - 68} M ${x + 46} ${y - 44} L ${x + 32} ${y - 72}`,
  ]
})

const yearMarkers = computed<YearMarker[]>(() => {
  const grouped = new Map<string, BranchView[]>()
  branches.value.forEach((branch) => {
    if (!grouped.has(branch.year)) grouped.set(branch.year, [])
    grouped.get(branch.year)!.push(branch)
  })

  return [...grouped.entries()].map(([year, entries], index) => {
    const averageY = entries.reduce((sum, entry) => sum + entry.attachY, 0) / entries.length
    const averageX = entries.reduce((sum, entry) => sum + entry.attachX, 0) / entries.length
    const side = index % 2 === 0 ? -1 : 1
    return {
      year,
      x: averageX + side * 132,
      y: averageY,
    }
  })
})

const cards = computed<CardView[]>(() => {
  const branchMap = new Map(branches.value.map((branch) => [branch.id, branch]))

  return monthGroups.value.flatMap((group, groupIndex) => {
    const branch = branchMap.get(`${group.year}-${group.month}`)
    if (!branch) return []

    const direction = branch.side === 'left' ? -1 : 1
    return group.posts.map((post, postIndex) => {
      const date = new Date(post.date)
      const dayLabel = Number.isNaN(date.getTime()) ? '--' : String(date.getDate()).padStart(2, '0')
      const offsetY =
        group.posts.length === 1 ? 0 : (postIndex - (group.posts.length - 1) / 2) * 112
      const x = branch.endX + direction * 56 - (direction === -1 ? cardWidth : 0)
      const y = branch.endY - 42 + offsetY

      return {
        slug: post.slug,
        title: post.title,
        description: post.description,
        category: post.category,
        tags: post.tags,
        side: branch.side,
        x,
        y,
        rotate: direction * (-3.6 + (groupIndex % 4) * 0.7) + postIndex * 0.35,
        monthLabel: `${String(group.month).padStart(2, '0')}月`,
        dayLabel,
      }
    })
  })
})
</script>

<style scoped>
.archive-tree-page {
  position: relative;
  z-index: 10;
  width: min(100%, 108rem);
  margin: 0 auto;
  padding: 6rem 1rem 4rem;
}

.archive-tree-stage {
  position: relative;
  width: 100%;
  min-height: 100vh;
}

.archive-tree-svg,
.archive-tree-layer {
  position: absolute;
  inset: 0;
}

.archive-tree-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.archive-tree-layer {
  pointer-events: none;
}

.tree-sketch {
  stroke-linecap: round;
  stroke-linejoin: round;
}

.tree-root-line,
.tree-trunk-outline,
.tree-branch-line,
.tree-crown-line {
  fill: none;
  stroke: rgba(164, 231, 255, 0.84);
}

.tree-root-line,
.tree-trunk-outline {
  stroke-width: 4.4;
}

.tree-branch-line {
  stroke-width: 3.2;
}

.tree-crown-line {
  stroke-width: 2.1;
}

.tree-bark-line {
  fill: none;
  stroke: rgba(125, 214, 255, 0.58);
  stroke-width: 1.4;
}

.year-marker,
.month-marker {
  position: absolute;
  pointer-events: none;
}

.year-marker {
  display: flex;
  align-items: center;
  gap: 10px;
  transform: translate(-50%, -50%);
}

.year-marker-line {
  width: 44px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(125, 220, 255, 0.9));
  box-shadow: 0 0 12px rgba(70, 195, 255, 0.4);
}

.year-marker-text {
  color: rgba(225, 247, 255, 0.96);
  font-size: 1.05rem;
  letter-spacing: 0.18em;
  text-shadow: 0 0 14px rgba(77, 196, 255, 0.36);
}

.month-marker {
  color: rgba(178, 235, 255, 0.82);
  font-size: 0.76rem;
  letter-spacing: 0.16em;
  text-shadow: 0 0 12px rgba(83, 198, 255, 0.34);
}

.month-marker--left {
  transform: translate(-100%, -50%);
}

.month-marker--right {
  transform: translate(0, -50%);
}

.archive-leaf-card {
  position: absolute;
  width: 246px;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  padding: 1rem 1rem 0.9rem;
  border-radius: 16px;
  text-decoration: none;
  pointer-events: auto;
  overflow: hidden;
  background: rgba(10, 22, 37, 0.82);
  border: 1px solid rgba(128, 221, 255, 0.24);
  box-shadow:
    0 18px 42px rgba(0, 0, 0, 0.26),
    0 0 28px rgba(77, 198, 255, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transition:
    transform 0.24s ease,
    border-color 0.24s ease,
    box-shadow 0.24s ease,
    background 0.24s ease;
}

.archive-leaf-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 16%, rgba(120, 214, 255, 0.14), transparent 30%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), transparent 34%);
  pointer-events: none;
}

.archive-leaf-card:hover {
  border-color: rgba(170, 236, 255, 0.4);
  background: rgba(12, 25, 42, 0.9);
  box-shadow:
    0 24px 50px rgba(0, 0, 0, 0.32),
    0 0 32px rgba(88, 204, 255, 0.22),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.archive-leaf-card--left:hover {
  transform: rotate(0deg) translate(-6px, -6px);
}

.archive-leaf-card--right:hover {
  transform: rotate(0deg) translate(6px, -6px);
}

.archive-leaf-card-pin {
  position: absolute;
  top: 12px;
  left: 50%;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(225, 246, 255, 0.96);
  box-shadow: 0 0 10px rgba(92, 207, 255, 0.42);
  transform: translateX(-50%);
}

.archive-leaf-card-string {
  position: absolute;
  top: -26px;
  left: 50%;
  width: 1px;
  height: 26px;
  background: linear-gradient(180deg, rgba(152, 233, 255, 0.9), rgba(152, 233, 255, 0.16));
  box-shadow: 0 0 10px rgba(78, 196, 255, 0.36);
  transform: translateX(-50%);
}

.archive-leaf-card-head,
.archive-leaf-card-tags {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.archive-leaf-card-date,
.archive-leaf-card-category,
.archive-leaf-card-tag {
  font-size: 0.72rem;
}

.archive-leaf-card-date {
  color: rgba(180, 236, 255, 0.84);
  letter-spacing: 0.12em;
}

.archive-leaf-card-category {
  color: rgba(229, 246, 255, 0.86);
  background: rgba(102, 204, 255, 0.15);
  padding: 0.16rem 0.46rem;
  border-radius: 999px;
}

.archive-leaf-card-title,
.archive-leaf-card-desc {
  position: relative;
  z-index: 1;
  margin: 0;
}

.archive-leaf-card-title {
  color: rgba(240, 249, 255, 0.96);
  font-size: 1rem;
  line-height: 1.45;
}

.archive-leaf-card-desc {
  color: rgba(194, 223, 239, 0.68);
  font-size: 0.8rem;
  line-height: 1.58;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.archive-leaf-card-tags {
  gap: 0.4rem;
  justify-content: flex-start;
  flex-wrap: wrap;
  margin-top: auto;
}

.archive-leaf-card-tag {
  position: relative;
  z-index: 1;
  color: rgba(164, 213, 235, 0.74);
  background: rgba(255, 255, 255, 0.04);
  padding: 0.16rem 0.46rem;
  border-radius: 999px;
}

@media (max-width: 1023px) {
  .archive-tree-page {
    width: min(100%, 96rem);
    padding: 5.5rem 0.8rem 3rem;
  }

  .archive-leaf-card {
    width: 220px;
  }
}

@media (max-width: 767px) {
  .archive-tree-page {
    padding-top: 5rem;
  }

  .archive-leaf-card {
    width: min(70vw, 220px);
  }

  .year-marker-text {
    font-size: 0.94rem;
  }
}
</style>
