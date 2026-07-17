# epub.js 滚动模式（scrolled-doc）连续阅读问题修复记录

## 问题描述

在使用 **epub.js 0.3.93** 的 `scrolled-doc` 阅读模式时，遇到两类典型问题：

1. **章节之间无法自动衔接**：滚动到当前章节底部后，无法继续滚动进入下一章，必须点击"下一页"按钮才能加载后续内容。
2. **首次打开图书时内容未完全加载**：部分图书（例如《86-不存在的战区 05》）首次进入时停留在封面，必须手动点击一次"上一页"或"下一页"按钮，后续章节内容才会渲染出来。

> 注意：这个问题在 epub.js 的 `paginated`（翻页）模式下通常不会出现，仅在 `scrolled-doc` 模式下表现明显。

---

## 根本原因

epub.js 的 `scrolled-doc` 模式**默认只渲染当前一个 spine item（章节）**，并不会自动把整本书的所有章节拼接成连续可滚动的长文档。每个章节被渲染在一个独立的 iframe 中，章节之间需要主动调用 `rendition.next()` / `rendition.prev()` 进行切换。

因此：

- 当用户滚动到章节末尾时，没有下一章的 DOM 内容，滚动自然停止。
- 某些 EPUB 的封面章节本身很短（通常只有一张封面图），甚至不会触发滚动事件，导致用户必须手动触发一次导航才能"唤醒"后续章节的渲染。

这是 epub.js 的设计限制，不是 EPUB 文件本身的错误。

---

## 修复方案

修复分两部分：CSS 防止滚动锚定回弹，以及 JS 实现滚动到底自动加载下一章 + 首次加载预热。

### 1. 关闭滚动锚定（overflow-anchor）

epub.js 在章节边界处可能出现滚动位置异常回弹（GitHub issue 中常见的"Page is bouncing back"问题）。在滚动模式的外层容器上关闭滚动锚定：

```css
.reader-page--scrolled .reader-viewer {
  overflow: hidden;
  /* 防止 epub.js 滚动模式下章节边界处的滚动锚定回弹 */
  overflow-anchor: none;
}
```

### 2. 滚动到底自动加载下一章

监听 `.epub-container` 的滚动事件，当接近底部时自动调用 `nextPage()`：

```ts
let scrollAutoLoadUnlisten: (() => void) | null = null

/** 滚动模式：监听 epub-container 滚动，到底时自动加载下一章 */
function setupScrollAutoLoad() {
  cleanupScrollAutoLoad()
  if (readingMode.value !== 'scrolled') return
  const container = viewerRef.value?.querySelector('.epub-container') as HTMLElement | null
  if (!container) return

  let isLoadingNext = false
  const onScroll = () => {
    if (isLoadingNext || !rendition.value) return
    const { scrollTop, scrollHeight, clientHeight } = container
    if (scrollTop + clientHeight >= scrollHeight - 40) {
      isLoadingNext = true
      nextPage()
      // 加载完成后重置标志
      window.setTimeout(() => {
        isLoadingNext = false
      }, 400)
    }
  }
  container.addEventListener('scroll', onScroll, { passive: true })
  scrollAutoLoadUnlisten = () => container.removeEventListener('scroll', onScroll)
}

function cleanupScrollAutoLoad() {
  scrollAutoLoadUnlisten?.()
  scrollAutoLoadUnlisten = null
}
```

在 `loadReader()` 成功后调用：

```ts
await displayReaderAnchor(anchor)
// ...
await nextTick()
setupScrollAutoLoad()
```

在切换阅读模式或销毁阅读器时清理监听：

```ts
function cleanupReader() {
  cleanupScrollAutoLoad()
  // ...
}
```

### 3. 首次加载预热下一章

滚动模式下首次打开图书时，主动调用一次 `nextPage()` 再 `prevPage()` 回来，让 epub.js 把下一章也加载进渲染管线：

```ts
await displayReaderAnchor(anchor)

// 滚动模式下设置自动加载下一章监听
await nextTick()
setupScrollAutoLoad()

// 滚动模式下首次加载封面后预热下一章，避免必须点一次按钮才出现内容
if (readingMode.value === 'scrolled') {
  await nextPage()
  await prevPage()
}
```

这一步没有明显闪烁，但能解决部分 EPUB 打开后只显示封面、后续内容不出来的问题。

---

## 效果

修复后：

- 用户在 `scrolled-doc` 模式下可以连续滚动阅读整本书，章节自动衔接。
- 首次打开图书时，封面正常显示，后续章节已经预热，滚动到底即可自动进入下一章。
- 不再需要依赖"上一页"/"下一页"按钮来激活内容渲染。

---

## 局限性

- 这是基于 epub.js 现有架构的 workaround，不是真正的"无限滚动"实现。
- 章节切换时仍由 epub.js 内部重新渲染，理论上可能有轻微的位置重置，但实际测试中几乎无感知。
- 如果 EPUB 的某个章节高度很小（例如只有几行文字），自动触发阈值可能需要调整。

---

## 相关链接

- [epub.js GitHub](https://github.com/futurepress/epub.js)
- [epub.js scrolled-doc 模式文档](http://epubjs.org/documentation/0.3/#rendition)
- [GitHub Issue #1303 - Page is bouncing back when scrolling up](https://github.com/futurepress/epub.js/issues/1303)

---

*记录时间：2026-07-18*

*项目：Starlit Blog 图书阅读器*
