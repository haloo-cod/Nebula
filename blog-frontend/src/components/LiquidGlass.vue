<template>
  <div class="liquid-glass" ref="containerRef">
    <canvas
      ref="canvasRef"
      class="liquid-glass-canvas"
      :class="{ 'liquid-glass-canvas--visible': visible }"
    ></canvas>
    <div class="liquid-glass-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import darkBgUrl from '@/assets/img/test3.jpg'
import lightBgUrl from '@/assets/img/test6.png'
import { enqueueTextureUpload } from '@/components/liquidGlassQueue'
import { useUIStore } from '@/stores/ui'

const containerRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const visible = ref(false)
const ui = useUIStore()

const props = withDefaults(
  defineProps<{
    cornerRadius?: number
    blurRadius?: number
    glassThickness?: number
    ior?: number
    highlightWidth?: number
    overlayColor?: [number, number, number]
    allowReveal?: boolean
    realtimeOffset?: boolean
    theme?: 'light' | 'dark'
    rippleTrail?: boolean
    rippleStrength?: number
    rippleRadius?: number
    rippleDuration?: number
  }>(),
  {
    allowReveal: true,
    cornerRadius: 32,
    blurRadius: 0.0,
    glassThickness: 41,
    ior: 1.1,
    highlightWidth: 3.5,
    overlayColor: () => [0.85, 0.9, 1.0] as [number, number, number],
    theme: 'dark',
    realtimeOffset: false,
    rippleTrail: false,
    rippleStrength: 0.34,
    rippleRadius: 66,
    rippleDuration: 1100,
  },
)

type LiquidGlassTheme = 'light' | 'dark'

const backgroundUrls: Record<LiquidGlassTheme, string> = {
  dark: darkBgUrl,
  light: lightBgUrl,
}

const backgroundImageCache = new Map<string, Promise<HTMLImageElement>>()

function getCachedBackgroundImage(url: string): Promise<HTMLImageElement> {
  const cached = backgroundImageCache.get(url)
  if (cached) return cached

  const loader = new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error(`Failed to load background image: ${url}`))
    image.src = url
  })

  backgroundImageCache.set(url, loader)
  return loader
}

// 预热两张背景图,主题切换时直接复用已解码资源
void getCachedBackgroundImage(darkBgUrl)
void getCachedBackgroundImage(lightBgUrl)

// 两套液态玻璃参数预设
const glassPresets = {
  dark: {
    glassThickness: 41,
    ior: 1.1,
    highlightWidth: 3.5,
    blurRadius: 0.0,
    overlayColor: [0.15, 0.2, 0.25] as [number, number, number],
    normalStrength: 6.4,
    displacementScale: 1.0,
    heightTransitionWidth: 8.0,
    sminSmoothing: 20.0,
  },
  light: {
    glassThickness: 28,
    ior: 1.05,
    highlightWidth: 2.5,
    blurRadius: 0.5,
    overlayColor: [0.6, 0.65, 0.75] as [number, number, number],
    normalStrength: 5.0,
    displacementScale: 0.8,
    heightTransitionWidth: 6.0,
    sminSmoothing: 15.0,
  },
}

let gl: WebGLRenderingContext | null = null
let animationId: number = 0
let bgTexture: WebGLTexture | null = null
let program: WebGLProgram | null = null
let positionBuffer: WebGLBuffer | null = null
let bgLoaded = false
let textureRequestVersion = 0
let needsOffsetSync = true
let resizeObserver: ResizeObserver | null = null
let scrollOptions: AddEventListenerOptions | undefined
let scrollParents: HTMLElement[] = []
let scrollHandler: (() => void) | null = null

const MAX_TRAIL_POINTS = 12
const TRAIL_MIN_DISTANCE = 14

interface TrailPoint {
  x: number
  y: number
  startedAt: number
  strength: number
}

let trailPoints: TrailPoint[] = []
let lastTrailPoint: [number, number] | null = null

const uniforms = {
  resolution: { loc: null as WebGLUniformLocation | null, value: [0, 0] as [number, number] },
  mousePos: { loc: null as WebGLUniformLocation | null, value: [0, 0] as [number, number] },
  glassSize: { loc: null as WebGLUniformLocation | null, value: [0, 0] as [number, number] },
  canvasOffset: { loc: null as WebGLUniformLocation | null, value: [0, 0] as [number, number] },
  backgroundTexture: { loc: null as WebGLUniformLocation | null },
  cornerRadius: { loc: null as WebGLUniformLocation | null, value: 0 },
  ior: { loc: null as WebGLUniformLocation | null, value: 0 },
  glassThickness: { loc: null as WebGLUniformLocation | null, value: 0 },
  normalStrength: { loc: null as WebGLUniformLocation | null, value: 0 },
  displacementScale: { loc: null as WebGLUniformLocation | null, value: 0 },
  heightTransitionWidth: { loc: null as WebGLUniformLocation | null, value: 0 },
  sminSmoothing: { loc: null as WebGLUniformLocation | null, value: 0 },
  showNormals: { loc: null as WebGLUniformLocation | null, value: 0 },
  blurRadius: { loc: null as WebGLUniformLocation | null, value: 0 },
  overlayColor: {
    loc: null as WebGLUniformLocation | null,
    value: [0, 0, 0, 0] as [number, number, number, number],
  },
  highlightWidth: { loc: null as WebGLUniformLocation | null, value: 0 },
  trailPoints: {
    locs: [] as Array<WebGLUniformLocation | null>,
    value: Array.from(
      { length: MAX_TRAIL_POINTS },
      () => [0, 0, 1, 0] as [number, number, number, number],
    ),
  },
  trailRadius: { loc: null as WebGLUniformLocation | null, value: 0 },
  trailStrength: { loc: null as WebGLUniformLocation | null, value: 0 },
}

// bgUniforms 不再需要（背景由 PageBackground 渲染）

const vsSource = `
    precision mediump float;
    attribute vec2 a_position;
    uniform vec2 u_resolution;
    uniform vec2 u_mousePos;
    uniform vec2 u_glassSize;
    uniform vec2 u_canvasOffset;
    varying vec2 v_screenTexCoord;
    varying vec2 v_shapeCoord;
    void main() {
        // Canvas clip space (quad vertices are in [-0.5, 0.5])
        gl_Position = vec4(a_position * 2.0 * vec2(1.0, -1.0), 0.0, 1.0);
        // Screen space texture coordinates (for background sampling)
        vec2 screenPos = u_canvasOffset + u_mousePos + a_position * u_glassSize;
        v_screenTexCoord = screenPos / u_resolution;
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

// bgVsSource / bgFsSource 不再需要（背景由 PageBackground 渲染）

function createShader(gl: WebGLRenderingContext, type: number, source: string): WebGLShader | null {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error('Shader compile error:', gl.getShaderInfoLog(shader))
    gl.deleteShader(shader)
    return null
  }
  return shader
}

function initWebGL() {
  const canvas = canvasRef.value
  if (!canvas) return false

  gl = canvas.getContext('webgl')
  if (!gl) return false

  // Glass program
  const vs = createShader(gl, gl.VERTEX_SHADER, vsSource)
  const fs = createShader(gl, gl.FRAGMENT_SHADER, fsSource)
  if (!vs || !fs) return false

  program = gl.createProgram()
  gl.attachShader(program, vs)
  gl.attachShader(program, fs)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('Program link error:', gl.getProgramInfoLog(program))
    return false
  }

  // Background program (不再需要，背景由 PageBackground 渲染)
  // Position buffer
  const positions = [-0.5, -0.5, 0.5, -0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5, 0.5, 0.5]
  positionBuffer = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer)
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW)

  // Background texture (初始为透明，避免蓝色闪烁)
  bgTexture = gl.createTexture()
  gl.bindTexture(gl.TEXTURE_2D, bgTexture)
  gl.texImage2D(
    gl.TEXTURE_2D,
    0,
    gl.RGBA,
    1,
    1,
    0,
    gl.RGBA,
    gl.UNSIGNED_BYTE,
    new Uint8Array([0, 0, 0, 0]),
  )
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)

  // Uniform locations
  const posLoc = gl.getAttribLocation(program, 'a_position')
  uniforms.resolution.loc = gl.getUniformLocation(program, 'u_resolution')!
  uniforms.mousePos.loc = gl.getUniformLocation(program, 'u_mousePos')!
  uniforms.glassSize.loc = gl.getUniformLocation(program, 'u_glassSize')!
  uniforms.canvasOffset.loc = gl.getUniformLocation(program, 'u_canvasOffset')!
  uniforms.backgroundTexture.loc = gl.getUniformLocation(program, 'u_backgroundTexture')!
  uniforms.cornerRadius.loc = gl.getUniformLocation(program, 'u_cornerRadius')!
  uniforms.ior.loc = gl.getUniformLocation(program, 'u_ior')!
  uniforms.glassThickness.loc = gl.getUniformLocation(program, 'u_glassThickness')!
  uniforms.normalStrength.loc = gl.getUniformLocation(program, 'u_normalStrength')!
  uniforms.displacementScale.loc = gl.getUniformLocation(program, 'u_displacementScale')!
  uniforms.heightTransitionWidth.loc = gl.getUniformLocation(program, 'u_heightTransitionWidth')!
  uniforms.sminSmoothing.loc = gl.getUniformLocation(program, 'u_sminSmoothing')!
  uniforms.showNormals.loc = gl.getUniformLocation(program, 'u_showNormals')!
  uniforms.blurRadius.loc = gl.getUniformLocation(program, 'u_blurRadius')!
  uniforms.overlayColor.loc = gl.getUniformLocation(program, 'u_overlayColor')!
  uniforms.highlightWidth.loc = gl.getUniformLocation(program, 'u_highlightWidth')!
  uniforms.trailPoints.locs = Array.from({ length: MAX_TRAIL_POINTS }, (_, index) =>
    gl!.getUniformLocation(program!, `u_trailPoints[${index}]`),
  )
  uniforms.trailRadius.loc = gl.getUniformLocation(program, 'u_trailRadius')!
  uniforms.trailStrength.loc = gl.getUniformLocation(program, 'u_trailStrength')!

  // Store attribute locations
  ;(program as any).__posLoc = posLoc

  // Set default uniform values
  uniforms.cornerRadius.value = props.cornerRadius
  uniforms.ior.value = props.theme === 'light' ? glassPresets.light.ior : glassPresets.dark.ior
  uniforms.glassThickness.value =
    props.theme === 'light' ? glassPresets.light.glassThickness : glassPresets.dark.glassThickness
  uniforms.normalStrength.value =
    props.theme === 'light' ? glassPresets.light.normalStrength : glassPresets.dark.normalStrength
  uniforms.displacementScale.value =
    props.theme === 'light'
      ? glassPresets.light.displacementScale
      : glassPresets.dark.displacementScale
  uniforms.heightTransitionWidth.value =
    props.theme === 'light'
      ? glassPresets.light.heightTransitionWidth
      : glassPresets.dark.heightTransitionWidth
  uniforms.sminSmoothing.value =
    props.theme === 'light' ? glassPresets.light.sminSmoothing : glassPresets.dark.sminSmoothing
  uniforms.blurRadius.value = getEffectiveBlurRadius(props.theme)
  uniforms.highlightWidth.value =
    props.theme === 'light' ? glassPresets.light.highlightWidth : glassPresets.dark.highlightWidth
  uniforms.overlayColor.value = [
    ...(props.theme === 'light' ? glassPresets.light.overlayColor : glassPresets.dark.overlayColor),
    1.0,
  ] as [number, number, number, number]
  uniforms.trailRadius.value = props.rippleRadius
  uniforms.trailStrength.value = props.rippleTrail ? props.rippleStrength : 0

  return true
}

function resizeCanvas() {
  const container = containerRef.value
  const canvas = canvasRef.value
  if (!container || !canvas || !gl) return

  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'
  gl.viewport(0, 0, canvas.width, canvas.height)

  // u_resolution 是屏幕分辨率（用于纹理坐标映射）
  uniforms.resolution.value = [window.innerWidth * dpr, window.innerHeight * dpr]
  // u_glassSize 是 canvas 大小（玻璃区域）
  uniforms.glassSize.value = [canvas.width, canvas.height]
  // u_mousePos 是玻璃中心在 canvas 内的坐标
  uniforms.mousePos.value = [canvas.width / 2, canvas.height / 2]
  // u_canvasOffset 是 canvas 在屏幕上的偏移
  uniforms.canvasOffset.value = [rect.left * dpr, rect.top * dpr]
  trailPoints = []
  lastTrailPoint = null
  needsOffsetSync = false
}

function getPointerCanvasPoint(event: PointerEvent): [number, number] | null {
  const container = containerRef.value
  if (!container) return null
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  const [width, height] = uniforms.glassSize.value
  return [
    (event.clientX - rect.left) * dpr - width / 2,
    (event.clientY - rect.top) * dpr - height / 2,
  ]
}

function addTrailPoint(event: PointerEvent) {
  if (!props.rippleTrail) return
  const point = getPointerCanvasPoint(event)
  if (!point) return
  if (lastTrailPoint) {
    const dx = point[0] - lastTrailPoint[0]
    const dy = point[1] - lastTrailPoint[1]
    const dpr = window.devicePixelRatio || 1
    if (Math.hypot(dx, dy) < TRAIL_MIN_DISTANCE * dpr) return
  }
  lastTrailPoint = point
  trailPoints.push({ x: point[0], y: point[1], startedAt: performance.now(), strength: 1 })
  if (trailPoints.length > MAX_TRAIL_POINTS) trailPoints.shift()
}

function resetTrailPoint() {
  lastTrailPoint = null
}

function updateTrailUniforms() {
  const now = performance.now()
  const duration = Math.max(1, props.rippleDuration)
  trailPoints = trailPoints.filter((point) => now - point.startedAt < duration)
  for (let index = 0; index < MAX_TRAIL_POINTS; index += 1) {
    const point = trailPoints[index]
    uniforms.trailPoints.value[index] = point
      ? [point.x, point.y, (now - point.startedAt) / duration, point.strength]
      : [0, 0, 1, 0]
  }
  uniforms.trailRadius.value = props.rippleRadius * (window.devicePixelRatio || 1)
  uniforms.trailStrength.value = props.rippleTrail ? props.rippleStrength : 0
}

function syncCanvasOffset() {
  const container = containerRef.value
  if (!container || !gl) return
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  uniforms.resolution.value = [window.innerWidth * dpr, window.innerHeight * dpr]
  uniforms.canvasOffset.value = [rect.left * dpr, rect.top * dpr]
  needsOffsetSync = false
}

function markCanvasOffsetDirty() {
  needsOffsetSync = true
}

function isScrollableElement(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element)
  const overflow = `${style.overflow}${style.overflowX}${style.overflowY}`
  const canScroll = /(auto|scroll|overlay)/.test(overflow)
  return (
    canScroll &&
    (element.scrollWidth > element.clientWidth || element.scrollHeight > element.clientHeight)
  )
}

function getScrollParents(element: HTMLElement): HTMLElement[] {
  const parents: HTMLElement[] = []
  let current = element.parentElement
  while (current && current !== document.body) {
    if (isScrollableElement(current)) parents.push(current)
    current = current.parentElement
  }
  return parents
}

async function loadBgImage(bgUrl: string) {
  if (!gl || !bgTexture) return
  // 版本号用于丢弃快速连续切换主题时已经过期的纹理上传任务。
  const requestVersion = ++textureRequestVersion

  try {
    const image = await getCachedBackgroundImage(bgUrl)
    enqueueTextureUpload({
      execute: () => {
        if (!gl || !bgTexture || requestVersion !== textureRequestVersion) return
        gl.bindTexture(gl.TEXTURE_2D, bgTexture)
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true)
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image)
        const isPow2 = (v: number) => (v & (v - 1)) === 0
        if (isPow2(image.width) && isPow2(image.height)) {
          gl.generateMipmap(gl.TEXTURE_2D)
        } else {
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
        }
        bgLoaded = true
        // 方案 B:上传新纹理后先主动绘制一帧,再让 canvas 淡入。
        // 否则 visible=true 后 opacity 回升的最前几毫秒会暴露旧 canvas 像素。
        drawFrame()
        visible.value = true
        if (!animationId) {
          animationId = requestAnimationFrame(render)
        }
      },
    })
  } catch (error) {
    console.warn('[LiquidGlass] Failed to load background image:', error)
    bgLoaded = true
    visible.value = true
    if (!animationId) {
      animationId = requestAnimationFrame(render)
    }
  }
}

function syncBackgroundWithTheme(theme: LiquidGlassTheme) {
  // 复用首次加载流程:先隐藏 canvas,等新纹理上传并绘制完成后再淡入。
  if (props.allowReveal || ui.themeTransitioning) visible.value = false
  void loadBgImage(backgroundUrls[theme])
}

function getEffectiveBlurRadius(theme: 'light' | 'dark') {
  if (typeof props.blurRadius === 'number') return props.blurRadius
  return glassPresets[theme].blurRadius
}

function applyThemePreset(theme: 'light' | 'dark') {
  const p = glassPresets[theme]
  uniforms.ior.value = p.ior
  uniforms.glassThickness.value = p.glassThickness
  uniforms.normalStrength.value = p.normalStrength
  uniforms.displacementScale.value = p.displacementScale
  uniforms.heightTransitionWidth.value = p.heightTransitionWidth
  uniforms.sminSmoothing.value = p.sminSmoothing
  uniforms.blurRadius.value = getEffectiveBlurRadius(theme)
  uniforms.highlightWidth.value = p.highlightWidth
  uniforms.overlayColor.value = [...p.overlayColor, 1.0] as [number, number, number, number]
}

// 主题切换:重新应用玻璃参数预设,并直接从共享图片缓存刷新纹理
watch(
  () => props.theme,
  (theme) => {
    if (!gl) return
    applyThemePreset(theme)
    syncBackgroundWithTheme(theme)
  },
)

watch(
  () => props.blurRadius,
  () => {
    uniforms.blurRadius.value = getEffectiveBlurRadius(props.theme)
  },
)

/** 单帧绘制:用于常规 RAF 循环,也用于纹理更新后的立即刷新 */
function drawFrame() {
  if (!gl || !program || !positionBuffer || !bgTexture || !bgLoaded) {
    return false
  }

  gl.clearColor(0, 0, 0, 0)
  gl.clear(gl.COLOR_BUFFER_BIT)

  // 仅绘制玻璃效果（背景已由 PageBackground 渲染）
  gl.useProgram(program)
  gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer)
  gl.enableVertexAttribArray((program as any).__posLoc)
  gl.vertexAttribPointer((program as any).__posLoc, 2, gl.FLOAT, false, 0, 0)

  gl.uniform2fv(uniforms.resolution.loc!, uniforms.resolution.value)
  gl.uniform2fv(uniforms.mousePos.loc!, uniforms.mousePos.value)
  gl.uniform2fv(uniforms.glassSize.loc!, uniforms.glassSize.value)
  gl.uniform2fv(uniforms.canvasOffset.loc!, uniforms.canvasOffset.value)
  gl.uniform1f(uniforms.cornerRadius.loc!, uniforms.cornerRadius.value)
  gl.uniform1f(uniforms.ior.loc!, uniforms.ior.value)
  gl.uniform1f(uniforms.glassThickness.loc!, uniforms.glassThickness.value)
  gl.uniform1f(uniforms.normalStrength.loc!, uniforms.normalStrength.value)
  gl.uniform1f(uniforms.displacementScale.loc!, uniforms.displacementScale.value)
  gl.uniform1f(uniforms.heightTransitionWidth.loc!, uniforms.heightTransitionWidth.value)
  gl.uniform1f(uniforms.sminSmoothing.loc!, uniforms.sminSmoothing.value)
  gl.uniform1i(uniforms.showNormals.loc!, uniforms.showNormals.value)
  gl.uniform1f(uniforms.blurRadius.loc!, uniforms.blurRadius.value)
  gl.uniform4fv(uniforms.overlayColor.loc!, uniforms.overlayColor.value)
  gl.uniform1f(uniforms.highlightWidth.loc!, uniforms.highlightWidth.value)
  uniforms.trailPoints.locs.forEach((loc, index) => {
    if (loc) gl!.uniform4fv(loc, uniforms.trailPoints.value[index])
  })
  gl.uniform1f(uniforms.trailRadius.loc!, uniforms.trailRadius.value)
  gl.uniform1f(uniforms.trailStrength.loc!, uniforms.trailStrength.value)

  gl.activeTexture(gl.TEXTURE0)
  gl.bindTexture(gl.TEXTURE_2D, bgTexture)
  gl.uniform1i(uniforms.backgroundTexture.loc!, 0)

  gl.enable(gl.BLEND)
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
  gl.drawArrays(gl.TRIANGLES, 0, 6)
  gl.disable(gl.BLEND)
  return true
}

function render() {
  if (props.realtimeOffset && needsOffsetSync) syncCanvasOffset()
  updateTrailUniforms()
  drawFrame()
  animationId = requestAnimationFrame(render)
}

onMounted(() => {
  if (!initWebGL()) {
    console.warn('[LiquidGlass] WebGL not available, falling back to CSS')
    return
  }

  resizeCanvas()

  syncBackgroundWithTheme(props.theme)

  resizeObserver = new ResizeObserver(() => {
    markCanvasOffsetDirty()
    resizeCanvas()
  })
  resizeObserver.observe(containerRef.value!)

  window.addEventListener('resize', resizeCanvas)

  // 滚动时更新 canvas 偏移，使折射效果跟随页面实时变化
  scrollHandler = () => {
    if (props.realtimeOffset) {
      markCanvasOffsetDirty()
      return
    }
    syncCanvasOffset()
  }

  const containerEl = containerRef.value!
  containerEl.addEventListener('pointerenter', addTrailPoint)
  containerEl.addEventListener('pointermove', addTrailPoint)
  containerEl.addEventListener('pointerleave', resetTrailPoint)
  scrollOptions = { passive: true, capture: props.realtimeOffset }
  window.addEventListener('scroll', scrollHandler, scrollOptions)
  if (props.realtimeOffset) {
    scrollParents = getScrollParents(containerEl)
    scrollParents.forEach((parent) =>
      parent.addEventListener('scroll', scrollHandler!, scrollOptions),
    )
  }

  // 不立即启动渲染循环，等背景图加载完成后再开始（由 loadBgImage 中的 bgLoaded = true 触发）
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  resizeObserver?.disconnect()
  window.removeEventListener('resize', resizeCanvas)
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler, scrollOptions)
    scrollParents.forEach((parent) =>
      parent.removeEventListener('scroll', scrollHandler!, scrollOptions),
    )
  }
  const containerEl = containerRef.value
  containerEl?.removeEventListener('pointerenter', addTrailPoint)
  containerEl?.removeEventListener('pointermove', addTrailPoint)
  containerEl?.removeEventListener('pointerleave', resetTrailPoint)
  scrollParents = []
  scrollHandler = null
  resizeObserver = null
})
</script>

<style scoped>
.liquid-glass {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
}

.liquid-glass-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.12s ease-out;
}

.liquid-glass-canvas--visible {
  opacity: 1;
}

.liquid-glass-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
}
</style>
