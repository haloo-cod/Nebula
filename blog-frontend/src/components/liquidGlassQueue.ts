interface TextureUploadTask {
  execute: () => void
}

const textureUploadQueue: TextureUploadTask[] = []
const idleResolvers = new Set<() => void>()
const firstSettledResolvers = new Set<() => void>()
let textureUploadFrame = 0
let textureUploadGeneration = 0
let settledInGeneration = 0

function waitForSettledGeneration(predicate: () => boolean, timeoutMs: number): Promise<void> {
  if (predicate()) return Promise.resolve()

  return new Promise((resolve) => {
    const startedAt = performance.now()
    let frame = 0
    const finish = () => {
      if (frame) cancelAnimationFrame(frame)
      resolve()
    }
    const check = () => {
      if (predicate() || (timeoutMs > 0 && performance.now() - startedAt >= timeoutMs)) {
        finish()
        return
      }
      frame = requestAnimationFrame(check)
    }

    frame = requestAnimationFrame(check)
  })
}

// 当前批次里第一个任务完成后立刻通知,用于让全屏主题遮罩开始撤场。
// 注意这里只关心“首个面板已能展示新纹理”,不是等整批全部完成。
function notifyFirstSettled() {
  if (settledInGeneration > 0) return
  settledInGeneration += 1
  for (const resolve of firstSettledResolvers) resolve()
  firstSettledResolvers.clear()
}

function notifyIdle() {
  for (const resolve of idleResolvers) resolve()
  idleResolvers.clear()
}

function flushTextureUploadQueue() {
  textureUploadFrame = 0
  const task = textureUploadQueue.shift()
  if (!task) {
    notifyIdle()
    return
  }

  // 单帧只处理一个纹理上传任务,把 6 个 LiquidGlass 面板的 GPU 上传分摊开。
  task.execute()
  notifyFirstSettled()

  if (textureUploadQueue.length > 0) {
    textureUploadFrame = requestAnimationFrame(flushTextureUploadQueue)
  } else {
    notifyIdle()
  }
}

/** 将 WebGL 纹理上传任务分摊到逐帧执行,避免同一帧集中卡顿 */
export function enqueueTextureUpload(task: TextureUploadTask) {
  if (textureUploadQueue.length === 0 && !textureUploadFrame) {
    textureUploadGeneration += 1
    settledInGeneration = 0
  }
  textureUploadQueue.push(task)
  if (!textureUploadFrame) {
    textureUploadFrame = requestAnimationFrame(flushTextureUploadQueue)
  }
}

/** 等待当前批次第一个纹理上传任务完成,用于启动主题遮罩淡出 */
export function waitForFirstTextureUploadSettled(): Promise<void> {
  if (textureUploadGeneration > 0 && settledInGeneration > 0) {
    return Promise.resolve()
  }
  return new Promise((resolve) => {
    firstSettledResolvers.add(resolve)
  })
}

/** 等待调用之后产生的新批次首个纹理完成,无新批次时超时放行避免主题遮罩卡死 */
export function waitForNextTextureUploadSettled(timeoutMs = 1200): Promise<void> {
  const baseGeneration = textureUploadGeneration
  return waitForSettledGeneration(
    () => textureUploadGeneration > baseGeneration && settledInGeneration > 0,
    timeoutMs,
  )
}

/** 等待当前纹理上传队列排空 */
export function waitForTextureUploadQueueIdle(): Promise<void> {
  if (textureUploadQueue.length === 0 && !textureUploadFrame) {
    return Promise.resolve()
  }
  return new Promise((resolve) => {
    idleResolvers.add(resolve)
  })
}
