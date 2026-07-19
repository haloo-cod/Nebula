import img01 from '@/assets/img/test2.jpg'
import img02 from '@/assets/img/test3.jpg'
import img03 from '@/assets/img/test4.jpg'
import img04 from '@/assets/img/test5.PNG'
import img05 from '@/assets/img/test6.PNG'
import mob01 from '@/assets/img2/01.PNG'
import mob03 from '@/assets/img2/03.PNG'
import mob05 from '@/assets/img2/05.PNG'
import mob07 from '@/assets/img2/07.PNG'

/** 背景图条目 */
export interface BackgroundItem {
  src: string
}

/** 静态 fallback: dark 主题桌面端背景图组 */
export const darkBackgrounds: BackgroundItem[] = [
  { src: img01 },
  { src: img02 },
  { src: img03 },
]

/** 静态 fallback: light 主题桌面端背景图组 */
export const lightBackgrounds: BackgroundItem[] = [
  { src: img05 },
  { src: img04 },
]

/** 静态 fallback: dark 主题移动端背景图组 */
export const mobileDarkBackgrounds: BackgroundItem[] = [
  { src: mob01 },
  { src: mob03 },
]

/** 静态 fallback: light 主题移动端背景图组 */
export const mobileLightBackgrounds: BackgroundItem[] = [
  { src: mob05 },
  { src: mob07 },
]
