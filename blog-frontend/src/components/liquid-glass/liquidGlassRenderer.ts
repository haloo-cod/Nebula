/**
 * 液态玻璃共享 WebGL 渲染器 — 模块单例
 *
 * 全站所有 LiquidGlass 实例共享同一个 WebGL 上下文（OffscreenCanvas）。
 * 每帧遍历所有已注册且可渲染的实例,逐个渲染到 offscreen → drawImage 到实例的 2D canvas。
 *
 * 好处：
 * - 全站只有 1 个 WebGL 上下文,永远不会触发浏览器的上下文数量限制
 * - 背景纹理按 URL 缓存,只上传一次,所有实例共用
 * - 新实例注册后下一帧即可渲染,无需等待纹理上传
 * - context lost/restored 集中处理
 */

// ============================================================================
// 常量
// ============================================================================

const MAX_TRAIL_POINTS = 12

// ============================================================================
// 类型定义
// ============================================================================

/** 每个实例的 uniform 状态 */
export interface GlassUniforms {
  resolution: [number, number]
  mousePos: [number, number]
  glassSize: [number, number]
  canvasOffset: [number, number]
  texAspect: number // 纹理原始宽高比(width/height),用于 cover 模式 UV 校正
  cornerRadius: number
  ior: number
  glassThickness: number
  normalStrength: number
  displacementScale: number
  heightTransitionWidth: number
  sminSmoothing: number
  showNormals: number
  blurRadius: number
  overlayColor: [number, number, number, number]
  highlightWidth: number
  trailPoints: Array<[number, number, number, number]>
  trailRadius: number
  trailStrength: number
}

/** 注册实例所需的信息 */
export interface GlassInstance {
  /** 实例唯一 ID */
  id: number
  /** 该实例的可见 canvas（使用 2D context 接收渲染结果） */
  canvas: HTMLCanvasElement
  /** 2D context */
  ctx2d: CanvasRenderingContext2D
  /** 该实例当前的 uniform 值 */
  uniforms: GlassUniforms
  /** 当前使用的背景纹理 URL */
  backgroundUrl: string
  /** 是否应该渲染（纹理就绪 + 尺寸有效） */
  ready: boolean
  /** 首次渲染完成的回调（组件用于设 visible=true） */
  onFirstRender: (() => void) | null
  /** 是否已执行过首次渲染回调 */
  hasRenderedOnce: boolean
}

// ============================================================================
// 模块状态
// ============================================================================

let gl: WebGLRenderingContext | null = null
let offscreenCanvas: HTMLCanvasElement | null = null
let program: WebGLProgram | null = null
let positionBuffer: WebGLBuffer | null = null
let posLoc = 0
let animationId = 0
let contextLost = false
let initialized = false

// Uniform locations（共享 program 的 uniform 位置）
interface UniformLocations {
  resolution: WebGLUniformLocation | null
  mousePos: WebGLUniformLocation | null
  glassSize: WebGLUniformLocation | null
  canvasOffset: WebGLUniformLocation | null
  texAspect: WebGLUniformLocation | null
  backgroundTexture: WebGLUniformLocation | null
  cornerRadius: WebGLUniformLocation | null
  ior: WebGLUniformLocation | null
  glassThickness: WebGLUniformLocation | null
  normalStrength: WebGLUniformLocation | null
  displacementScale: WebGLUniformLocation | null
  heightTransitionWidth: WebGLUniformLocation | null
  sminSmoothing: WebGLUniformLocation | null
  showNormals: WebGLUniformLocation | null
  blurRadius: WebGLUniformLocation | null
  overlayColor: WebGLUniformLocation | null
  highlightWidth: WebGLUniformLocation | null
  trailPoints: Array<WebGLUniformLocation | null>
  trailRadius: WebGLUniformLocation | null
  trailStrength: WebGLUniformLocation | null
}

let locs: UniformLocations = createEmptyLocs()

function createEmptyLocs(): UniformLocations {
  return {
    resolution: null,
    mousePos: null,
    glassSize: null,
    canvasOffset: null,
    texAspect: null,
    backgroundTexture: null,
    cornerRadius: null,
    ior: null,
    glassThickness: null,
    normalStrength: null,
    displacementScale: null,
    heightTransitionWidth: null,
    sminSmoothing: null,
    showNormals: null,
    blurRadius: null,
    overlayColor: null,
    highlightWidth: null,
    trailPoints: [],
    trailRadius: null,
    trailStrength: null,
  }
}

// 纹理缓存：按 URL 索引
interface TextureEntry {
  texture: WebGLTexture
  aspect: number // 纹理原始宽高比(width/height)
}

const textureMap = new Map<string, TextureEntry>()

// 实例注册表
const instances = new Map<number, GlassInstance>()
let nextInstanceId = 1

// offscreen 当前尺寸（避免不必要的 resize）
let offscreenWidth = 0
let offscreenHeight = 0

// context lost 时通知所有实例的回调
const contextLostCallbacks = new Set<() => void>()
const contextRestoredCallbacks = new Set<() => void>()

// 纹理就绪通知（主题切换协调用）
const textureReadyCallbacks = new Set<() => void>()

// 渲染缩放比（集显自动降低,独显保持 1.0）
let renderScale = 1.0

// 帧率节流：无 trail 活跃时降为 30fps（每 2 帧渲染 1 次）
let frameCount = 0

// 滚动感知：滚动期间保持 60fps，停止后 200ms 缓冲再退回 30fps
let lastScrollTime = 0
if (typeof window !== 'undefined') {
  window.addEventListener('scroll', () => {
    lastScrollTime = performance.now()
  }, { passive: true })
}

// ============================================================================
// Shader 源码
// ============================================================================

const vsSource = `
    precision mediump float;
    attribute vec2 a_position;
    uniform vec2 u_resolution;
    uniform vec2 u_mousePos;
    uniform vec2 u_glassSize;
    uniform vec2 u_canvasOffset;
    uniform float u_texAspect;
    varying vec2 v_screenTexCoord;
    varying vec2 v_shapeCoord;
    void main() {
        gl_Position = vec4(a_position * 2.0 * vec2(1.0, -1.0), 0.0, 1.0);
        vec2 screenPos = u_canvasOffset + u_mousePos + a_position * u_glassSize;
        vec2 uv = screenPos / u_resolution;

        // Cover 模式:保持纹理宽高比,等比裁切覆盖视口
        float viewAspect = u_resolution.x / u_resolution.y;
        if (viewAspect > u_texAspect) {
            // 视口更宽(横屏):纹理高度填满,上下裁切
            float scale = u_texAspect / viewAspect;
            uv.y = (uv.y - 0.5) * scale + 0.5;
        } else {
            // 视口更窄(竖屏):纹理宽度填满,左右裁切
            float scale = viewAspect / u_texAspect;
            uv.x = (uv.x - 0.5) * scale + 0.5;
        }

        v_screenTexCoord = uv;
        v_screenTexCoord.y = 1.0 - v_screenTexCoord.y;
        v_shapeCoord = a_position;
    }
`

const fsSource = `
    precision mediump float;
    uniform sampler2D u_backgroundTexture;
    uniform vec2 u_resolution;
    uniform vec2 u_glassSize;
    uniform float u_cornerRadius;
    uniform float u_ior;
    uniform float u_glassThickness;
    uniform float u_normalStrength;
    uniform float u_displacementScale;
    uniform float u_heightTransitionWidth;
    uniform float u_sminSmoothing;
    uniform int u_showNormals;
    uniform float u_blurRadius;
    uniform vec4 u_overlayColor;
    uniform float u_highlightWidth;
    uniform vec4 u_trailPoints[${MAX_TRAIL_POINTS}];
    uniform float u_trailRadius;
    uniform float u_trailStrength;
    varying vec2 v_screenTexCoord;
    varying vec2 v_shapeCoord;

    float smin_polynomial(float a, float b, float k) {
        if (k <= 0.0) return min(a, b);
        float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
        return mix(b, a, h) - k * h * (1.0 - h);
    }

    float smax_polynomial(float a, float b, float k) {
        if (k <= 0.0) return max(a, b);
        float h = clamp(0.5 + 0.5 * (a - b) / k, 0.0, 1.0);
        return mix(b, a, h) + k * h * (1.0 - h);
    }

    float sdRoundedBoxSmooth(vec2 p, vec2 b, float r, float k_smooth) {
        if (k_smooth <= 0.0) {
            vec2 q = abs(p) - b + r;
            return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r;
        }
        vec2 q = abs(p) - b + r;
        float termA_smooth = smax_polynomial(q.x, q.y, k_smooth);
        float termB_smooth = smin_polynomial(termA_smooth, 0.0, k_smooth * 0.5);
        vec2 q_for_length_smooth = vec2(
            smax_polynomial(q.x, 0.0, k_smooth),
            smax_polynomial(q.y, 0.0, k_smooth)
        );
        float termC_smooth = length(q_for_length_smooth);
        return termB_smooth + termC_smooth - r;
    }

    float getHeightFromSDF(vec2 p_pixel_space, vec2 b_pixel_space, float r_pixel, float k_s, float transition_w) {
        float dist_sample = sdRoundedBoxSmooth(p_pixel_space, b_pixel_space, r_pixel, k_s);
        float normalized_dist = dist_sample / transition_w;
        const float steepness_factor = 6.0;
        float height = 1.0 - (1.0 / (1.0 + exp(-normalized_dist * steepness_factor)));
        return clamp(height, 0.0, 1.0);
    }

    float getTrailDent(vec2 p_pixel_space) {
        float dent = 0.0;
        for (int i = 0; i < ${MAX_TRAIL_POINTS}; i++) {
            vec4 point = u_trailPoints[i];
            float age = clamp(point.z, 0.0, 1.0);
            float strength = point.w * u_trailStrength;
            if (strength > 0.0 && age < 1.0) {
                float fade = pow(1.0 - age, 2.2);
                float radius = mix(u_trailRadius * 0.6, u_trailRadius * 1.35, age);
                float dist = length(p_pixel_space - point.xy);
                float bowl = exp(-(dist * dist) / (radius * radius));
                dent += bowl * fade * strength;
            }
        }
        return dent;
    }

    float getCombinedHeight(vec2 p_pixel_space, vec2 b_pixel_space, float r_pixel, float k_s, float transition_w) {
        float baseHeight = getHeightFromSDF(p_pixel_space, b_pixel_space, r_pixel, k_s, transition_w);
        return clamp(baseHeight - getTrailDent(p_pixel_space), 0.0, 1.0);
    }

    void main() {
        float actualCornerRadius = min(u_cornerRadius, min(u_glassSize.x, u_glassSize.y) / 2.0);
        vec2 current_p_pixel = v_shapeCoord * u_glassSize;
        vec2 glass_half_size_pixel = u_glassSize / 2.0;

        float dist_for_shape_boundary = sdRoundedBoxSmooth(current_p_pixel, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing);
        if (dist_for_shape_boundary > 0.001) {
            discard;
        }

        vec2 pixel_step_in_norm_space = vec2(1.0 / u_glassSize.x, 1.0 / u_glassSize.y);
        float norm_step_x1 = pixel_step_in_norm_space.x * 0.75;
        float norm_step_y1 = pixel_step_in_norm_space.y * 0.75;
        float norm_step_x2 = pixel_step_in_norm_space.x * 1.5;
        float norm_step_y2 = pixel_step_in_norm_space.y * 1.5;

        float h_px1 = getCombinedHeight((v_shapeCoord + vec2(norm_step_x1, 0.0)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float h_nx1 = getCombinedHeight((v_shapeCoord - vec2(norm_step_x1, 0.0)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float h_px2 = getCombinedHeight((v_shapeCoord + vec2(norm_step_x2, 0.0)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float h_nx2 = getCombinedHeight((v_shapeCoord - vec2(norm_step_x2, 0.0)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float grad_x1 = (h_px1 - h_nx1) / (2.0 * norm_step_x1 * u_glassSize.x);
        float grad_x2 = (h_px2 - h_nx2) / (2.0 * norm_step_x2 * u_glassSize.x);
        float delta_x = mix(grad_x1, grad_x2, 0.5);

        float h_py1 = getCombinedHeight((v_shapeCoord + vec2(0.0, norm_step_y1)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float h_ny1 = getCombinedHeight((v_shapeCoord - vec2(0.0, norm_step_y1)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float h_py2 = getCombinedHeight((v_shapeCoord + vec2(0.0, norm_step_y2)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float h_ny2 = getCombinedHeight((v_shapeCoord - vec2(0.0, norm_step_y2)) * u_glassSize, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        float grad_y1 = (h_py1 - h_ny1) / (2.0 * norm_step_y1 * u_glassSize.y);
        float grad_y2 = (h_py2 - h_ny2) / (2.0 * norm_step_y2 * u_glassSize.y);
        float delta_y = mix(grad_y1, grad_y2, 0.5);

        vec3 surfaceNormal3D = normalize(vec3(-delta_x * u_normalStrength, -delta_y * u_normalStrength, 1.0));

        if (u_showNormals == 1) {
            gl_FragColor = vec4(surfaceNormal3D * 0.5 + 0.5, 1.0);
            return;
        }

        vec3 incidentLightDir = normalize(vec3(0.0, 0.0, -1.0));
        vec3 refractedIntoGlass = refract(incidentLightDir, surfaceNormal3D, 1.0 / u_ior);
        vec3 refractedOutOfGlass = refract(refractedIntoGlass, -surfaceNormal3D, u_ior);

        vec2 offset_in_pixels = refractedOutOfGlass.xy * u_glassThickness;
        vec2 offset = (offset_in_pixels / u_resolution) * u_displacementScale;

        vec2 refractedTexCoord = v_screenTexCoord + offset;
        refractedTexCoord = clamp(refractedTexCoord, 0.001, 0.999);

        vec4 blurredColor = vec4(0.0);
        vec2 texelSize = 1.0 / u_resolution;
        float blurPixelRadius = u_blurRadius;

        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2(-1.0, -1.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2( 0.0, -1.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2( 1.0, -1.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2(-1.0,  0.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2( 0.0,  0.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2( 1.0,  0.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2(-1.0,  1.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2( 0.0,  1.0) * blurPixelRadius * texelSize);
        blurredColor += texture2D(u_backgroundTexture, refractedTexCoord + vec2( 1.0,  1.0) * blurPixelRadius * texelSize);
        blurredColor /= 9.0;

        float height_val = getCombinedHeight(current_p_pixel, glass_half_size_pixel, actualCornerRadius, u_sminSmoothing, u_heightTransitionWidth);
        vec4 finalColor = mix(blurredColor, u_overlayColor, height_val * 0.15);

        float highlight_dist = abs(dist_for_shape_boundary);
        float highlight_alpha = 1.0 - smoothstep(0.0, u_highlightWidth, highlight_dist);
        highlight_alpha = max(0.0, highlight_alpha);
        float directionalFactor = (surfaceNormal3D.x * surfaceNormal3D.y + 1.0) * 0.5;
        float finalHighlightAlpha = highlight_alpha * directionalFactor;

        gl_FragColor = mix(finalColor, vec4(1.0, 1.0, 1.0, 1.0), finalHighlightAlpha);
    }
`

// ============================================================================
// WebGL 初始化
// ============================================================================

function createShader(glCtx: WebGLRenderingContext, type: number, source: string): WebGLShader | null {
  const shader = glCtx.createShader(type)
  if (!shader) return null
  glCtx.shaderSource(shader, source)
  glCtx.compileShader(shader)
  if (!glCtx.getShaderParameter(shader, glCtx.COMPILE_STATUS)) {
    console.error('[LiquidGlassRenderer] Shader compile error:', glCtx.getShaderInfoLog(shader))
    glCtx.deleteShader(shader)
    return null
  }
  return shader
}

/** 初始化共享 WebGL 资源（上下文、shader、buffer） */
function initGL(): boolean {
  if (!offscreenCanvas) {
    // 使用隐藏的 HTMLCanvasElement 作为 offscreen（兼容性最好）
    offscreenCanvas = document.createElement('canvas')
    offscreenCanvas.style.display = 'none'
    document.body.appendChild(offscreenCanvas)
  }

  // 初始尺寸最小化,渲染时按需 resize 到实例尺寸
  offscreenCanvas.width = 1
  offscreenCanvas.height = 1
  offscreenWidth = 1
  offscreenHeight = 1

  gl = offscreenCanvas.getContext('webgl', {
    premultipliedAlpha: false,
    alpha: true,
    preserveDrawingBuffer: true,
  })
  if (!gl) {
    console.warn('[LiquidGlassRenderer] WebGL 不可用')
    return false
  }

  // 编译 shader
  const vs = createShader(gl, gl.VERTEX_SHADER, vsSource)
  const fs = createShader(gl, gl.FRAGMENT_SHADER, fsSource)
  if (!vs || !fs) return false

  program = gl.createProgram()!
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('[LiquidGlassRenderer] Program link error:', gl.getProgramInfoLog(program))
    return false
  }

  // Position buffer（全 quad）
  const positions = [-0.5, -0.5, 0.5, -0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5, 0.5, 0.5]
  positionBuffer = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW)

  // Uniform locations
  posLoc = gl.getAttribLocation(program, 'a_position')
  locs = {
    resolution: gl.getUniformLocation(program, 'u_resolution'),
    mousePos: gl.getUniformLocation(program, 'u_mousePos'),
    glassSize: gl.getUniformLocation(program, 'u_glassSize'),
    canvasOffset: gl.getUniformLocation(program, 'u_canvasOffset'),
    texAspect: gl.getUniformLocation(program, 'u_texAspect'),
    backgroundTexture: gl.getUniformLocation(program, 'u_backgroundTexture'),
    cornerRadius: gl.getUniformLocation(program, 'u_cornerRadius'),
    ior: gl.getUniformLocation(program, 'u_ior'),
    glassThickness: gl.getUniformLocation(program, 'u_glassThickness'),
    normalStrength: gl.getUniformLocation(program, 'u_normalStrength'),
    displacementScale: gl.getUniformLocation(program, 'u_displacementScale'),
    heightTransitionWidth: gl.getUniformLocation(program, 'u_heightTransitionWidth'),
    sminSmoothing: gl.getUniformLocation(program, 'u_sminSmoothing'),
    showNormals: gl.getUniformLocation(program, 'u_showNormals'),
    blurRadius: gl.getUniformLocation(program, 'u_blurRadius'),
    overlayColor: gl.getUniformLocation(program, 'u_overlayColor'),
    highlightWidth: gl.getUniformLocation(program, 'u_highlightWidth'),
    trailPoints: Array.from({ length: MAX_TRAIL_POINTS }, (_, i) =>
      gl!.getUniformLocation(program!, `u_trailPoints[${i}]`),
    ),
    trailRadius: gl.getUniformLocation(program, 'u_trailRadius'),
    trailStrength: gl.getUniformLocation(program, 'u_trailStrength'),
  }

  // 注册 context lost/restored 事件
  offscreenCanvas.addEventListener('webglcontextlost', handleContextLost)
  offscreenCanvas.addEventListener('webglcontextrestored', handleContextRestored)

  // 检测 GPU 性能,自动设定渲染缩放比
  renderScale = detectRenderScale(gl)

  initialized = true
  return true
}

/** 通过 WEBGL_debug_renderer_info 检测 GPU,集显自动降低渲染分辨率 */
function detectRenderScale(glCtx: WebGLRenderingContext): number {
  const ext = glCtx.getExtension('WEBGL_debug_renderer_info')
  if (!ext) return 1.0
  const renderer = glCtx.getParameter(ext.UNMASKED_RENDERER_WEBGL) as string
  // 集成显卡关键词匹配（Intel UHD/HD/Iris、AMD Radeon Vega 集显、Apple 低端等）
  if (/Intel|UHD|HD Graphics|Iris|Vega \d$|Mali|Adreno/i.test(renderer)) {
    return 0.65
  }
  return 1.0
}

/** 获取当前渲染缩放比（组件用于设置 canvas buffer 尺寸） */
export function getRenderScale(): number {
  return renderScale
}

/** 重新初始化（context restored 后调用） */
function reinitGL(): boolean {
  // 清理旧纹理引用（GL 对象已失效）
  textureMap.clear()
  locs = createEmptyLocs()
  program = null
  positionBuffer = null
  gl = null

  return initGL()
}

// ============================================================================
// Context Lost / Restored 处理
// ============================================================================

function handleContextLost(e: Event) {
  e.preventDefault()
  contextLost = true
  console.warn('[LiquidGlassRenderer] WebGL context lost')
  // 通知所有实例隐藏
  for (const cb of contextLostCallbacks) cb()
}

function handleContextRestored() {
  console.info('[LiquidGlassRenderer] WebGL context restored, reinitializing...')
  if (reinitGL()) {
    contextLost = false
    // 重新上传所有已缓存的纹理图片
    for (const [url] of textureMap) {
      // 纹理需要从图片重新上传,通知外部
      textureMap.delete(url)
    }
    for (const cb of contextRestoredCallbacks) cb()
  }
}

// ============================================================================
// 纹理管理
// ============================================================================

/** 图片缓存（避免重复加载） */
const imageCache = new Map<string, Promise<HTMLImageElement>>()

/** 加载并缓存图片 */
export function loadImage(url: string): Promise<HTMLImageElement> {
  const cached = imageCache.get(url)
  if (cached) return cached

  const loader = new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error(`Failed to load image: ${url}`))
    image.src = url
  })

  imageCache.set(url, loader)
  return loader
}

/** 上传纹理到 GPU（如果已缓存则直接返回） */
export function uploadTexture(url: string, image: HTMLImageElement): boolean {
  if (!gl || contextLost) return false
  if (textureMap.has(url)) return true

  const texture = gl.createTexture()
  if (!texture) return false

  gl.bindTexture(gl.TEXTURE_2D, texture)
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image)

  // Non-power-of-2 纹理参数
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)

  textureMap.set(url, { texture, aspect: image.naturalWidth / (image.naturalHeight || 1) })

  // 通知纹理就绪
  for (const cb of textureReadyCallbacks) cb()
  textureReadyCallbacks.clear()

  return true
}

/** 检查纹理是否已就绪 */
export function hasTexture(url: string): boolean {
  return textureMap.has(url)
}

/** 获取已上传纹理的原始宽高比(width/height),未就绪时返回 1 */
export function getTextureAspect(url: string): number {
  const entry = textureMap.get(url)
  return entry ? entry.aspect : 1
}

/** 删除指定 URL 的纹理（可选,用于内存清理） */
export function deleteTexture(url: string): void {
  const entry = textureMap.get(url)
  if (entry && gl) {
    gl.deleteTexture(entry.texture)
    textureMap.delete(url)
  }
}

/** 等待指定 URL 的纹理就绪（用于主题切换协调） */
export function waitForTexture(url: string, timeoutMs = 1200): Promise<void> {
  if (textureMap.has(url)) return Promise.resolve()
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, timeoutMs)
    const cb = () => {
      if (textureMap.has(url)) {
        clearTimeout(timer)
        textureReadyCallbacks.delete(cb)
        resolve()
      }
    }
    textureReadyCallbacks.add(cb)
  })
}

// ============================================================================
// 实例管理
// ============================================================================

/** 注册一个新的 LiquidGlass 实例 */
export function registerInstance(
  canvas: HTMLCanvasElement,
  ctx2d: CanvasRenderingContext2D,
  uniforms: GlassUniforms,
  backgroundUrl: string,
  onFirstRender: () => void,
): number {
  ensureInitialized()

  const id = nextInstanceId++
  instances.set(id, {
    id,
    canvas,
    ctx2d,
    uniforms,
    backgroundUrl,
    ready: false,
    onFirstRender,
    hasRenderedOnce: false,
  })
  return id
}

/** 注销实例 */
export function unregisterInstance(id: number): void {
  instances.delete(id)
}

/** 标记实例为可渲染（纹理就绪 + 尺寸有效后调用） */
export function markInstanceReady(id: number, ready: boolean): void {
  const inst = instances.get(id)
  if (inst) inst.ready = ready
}

/** 更新实例的背景 URL */
export function setInstanceBackground(id: number, url: string): void {
  const inst = instances.get(id)
  if (inst) {
    inst.backgroundUrl = url
    inst.hasRenderedOnce = false
  }
}

/** 更新实例的首次渲染回调 */
export function setInstanceFirstRenderCallback(id: number, cb: (() => void) | null): void {
  const inst = instances.get(id)
  if (inst) {
    inst.onFirstRender = cb
    inst.hasRenderedOnce = false
  }
}

/** 注册 context lost 回调 */
export function onContextLost(cb: () => void): void {
  contextLostCallbacks.add(cb)
}

/** 注册 context restored 回调 */
export function onContextRestored(cb: () => void): void {
  contextRestoredCallbacks.add(cb)
}

/** 移除 context lost/restored 回调 */
export function offContextCallbacks(lostCb: () => void, restoredCb: () => void): void {
  contextLostCallbacks.delete(lostCb)
  contextRestoredCallbacks.delete(restoredCb)
}

/** 检查渲染器是否可用 */
export function isRendererAvailable(): boolean {
  return initialized && !contextLost && gl !== null
}

// ============================================================================
// 渲染循环
// ============================================================================

/** 确保渲染器已初始化 */
function ensureInitialized() {
  if (initialized) return
  if (!initGL()) {
    console.warn('[LiquidGlassRenderer] 初始化失败')
    return
  }
  // 启动渲染循环
  if (!animationId) {
    animationId = requestAnimationFrame(renderLoop)
  }
}

/** 为指定实例上传 uniforms 并绘制一帧到 offscreen */
function renderInstance(inst: GlassInstance): boolean {
  if (!gl || !program || !positionBuffer || contextLost) return false

  const { uniforms, backgroundUrl } = inst
  const [gw, gh] = uniforms.glassSize
  if (gw < 1 || gh < 1) return false

  // 检查纹理是否就绪
  const texEntry = textureMap.get(backgroundUrl)
  if (!texEntry) return false

  // 设置 viewport 为实例尺寸
  const w = Math.ceil(gw)
  const h = Math.ceil(gh)

  // 每个实例渲染前把 offscreen 调整为该实例尺寸,
  // 确保 WebGL 渲染填满整个 offscreen,drawImage 直接拷贝整个 offscreen 即可
  if (offscreenWidth !== w || offscreenHeight !== h) {
    offscreenCanvas!.width = w
    offscreenCanvas!.height = h
    offscreenWidth = w
    offscreenHeight = h
  }

  gl.viewport(0, 0, w, h)
  gl.clearColor(0, 0, 0, 0)
  gl.clear(gl.COLOR_BUFFER_BIT)

  gl.useProgram(program)
  gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer)
  gl.enableVertexAttribArray(posLoc)
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0)

  // 上传 uniforms
  gl.uniform2fv(locs.resolution!, uniforms.resolution)
  gl.uniform2fv(locs.mousePos!, uniforms.mousePos)
  gl.uniform2fv(locs.glassSize!, uniforms.glassSize)
  gl.uniform2fv(locs.canvasOffset!, uniforms.canvasOffset)
  gl.uniform1f(locs.texAspect!, uniforms.texAspect)
  gl.uniform1f(locs.cornerRadius!, uniforms.cornerRadius)
  gl.uniform1f(locs.ior!, uniforms.ior)
  gl.uniform1f(locs.glassThickness!, uniforms.glassThickness)
  gl.uniform1f(locs.normalStrength!, uniforms.normalStrength)
  gl.uniform1f(locs.displacementScale!, uniforms.displacementScale)
  gl.uniform1f(locs.heightTransitionWidth!, uniforms.heightTransitionWidth)
  gl.uniform1f(locs.sminSmoothing!, uniforms.sminSmoothing)
  gl.uniform1i(locs.showNormals!, uniforms.showNormals)
  gl.uniform1f(locs.blurRadius!, uniforms.blurRadius)
  gl.uniform4fv(locs.overlayColor!, uniforms.overlayColor)
  gl.uniform1f(locs.highlightWidth!, uniforms.highlightWidth)
  gl.uniform1f(locs.trailRadius!, uniforms.trailRadius)
  gl.uniform1f(locs.trailStrength!, uniforms.trailStrength)
  gl.uniform1i(locs.backgroundTexture!, 0)

  // Trail points
  for (let i = 0; i < MAX_TRAIL_POINTS; i++) {
    const loc = locs.trailPoints[i]
    if (loc) gl.uniform4fv(loc, uniforms.trailPoints[i])
  }

  // 绑定纹理
  gl.activeTexture(gl.TEXTURE0)
  gl.bindTexture(gl.TEXTURE_2D, texEntry.texture)

  // 绘制
  gl.enable(gl.BLEND)
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
  gl.drawArrays(gl.TRIANGLES, 0, 6)
  gl.disable(gl.BLEND)

  return true
}

/** 检查是否有任何实例存在活跃的 trail 动画 */
function hasActiveTrails(): boolean {
  for (const inst of instances.values()) {
    if (!inst.ready) continue
    // trailPoints 中 age < 1 的表示仍在动画中
    for (const tp of inst.uniforms.trailPoints) {
      if (tp[3] > 0 && tp[2] < 1) return true
    }
  }
  return false
}

/** 单帧渲染循环:遍历所有可渲染实例 */
function renderLoop() {
  animationId = requestAnimationFrame(renderLoop)

  if (contextLost || !gl || !program) return

  frameCount++

  // 帧率节流：无 trail/无滚动时降为 30fps（跳帧）,减轻集显负载
  // 首次渲染回调未完成的实例不受节流影响（确保淡入不延迟）
  // 滚动期间 + 停止后 200ms 缓冲期内保持 60fps，消除拖拽感
  const SCROLL_BUFFER_MS = 200
  const scrollActive = performance.now() - lastScrollTime < SCROLL_BUFFER_MS
  const hasTrail = hasActiveTrails()
  const hasPendingFirstRender = [...instances.values()].some(
    (inst) => inst.ready && !inst.hasRenderedOnce,
  )
  const needsFullFps = hasTrail || hasPendingFirstRender || scrollActive
  if (!needsFullFps && frameCount % 2 !== 0) return

  for (const inst of instances.values()) {
    if (!inst.ready) continue

    // 渲染到 offscreen
    const success = renderInstance(inst)
    if (!success) continue

    // 拷贝到实例的 2D canvas
    // canvas.width/height 已经是像素尺寸（乘过 dpr * renderScale）,2D context 操作使用像素坐标
    const { canvas, ctx2d } = inst

    ctx2d.clearRect(0, 0, canvas.width, canvas.height)
    ctx2d.drawImage(offscreenCanvas!, 0, 0, canvas.width, canvas.height)

    // 首次渲染回调
    if (!inst.hasRenderedOnce && inst.onFirstRender) {
      inst.hasRenderedOnce = true
      inst.onFirstRender()
    }
  }
}

// ============================================================================
// 预热：加载默认背景图（模块加载时即执行）
// ============================================================================

/** 预热背景纹理：加载图片并上传到 GPU */
export async function preloadTexture(url: string): Promise<boolean> {
  try {
    const image = await loadImage(url)
    ensureInitialized()
    return uploadTexture(url, image)
  } catch {
    return false
  }
}

// 导出 MAX_TRAIL_POINTS 供组件使用
export { MAX_TRAIL_POINTS }
