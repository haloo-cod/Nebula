/** 液态玻璃渲染器中可独立测试的轻量计算。 */

/** 判断是否需要执行背景模糊采样。 */
export function shouldBlurBackground(blurRadius: number): boolean {
  return blurRadius > 0
}

/** 统计仍在播放的涟漪点数量。 */
export function countActiveTrailPoints(points: Array<[number, number, number, number]>): number {
  return points.reduce((count, point) => count + (point[3] > 0 && point[2] < 1 ? 1 : 0), 0)
}

/** 生成静态 uniform 的稳定键,避免不同实例错误复用状态。 */
export function buildStaticUniformKey(values: readonly unknown[]): string {
  return values.map((value) => (Array.isArray(value) ? value.join(',') : String(value))).join('|')
}
