// ---------------------------------------------------------------------------
// 说说数据层
// 提供分页 getter,接口签名设计为将来可直接替换为 fetch 调用。
// ---------------------------------------------------------------------------

import type { Moment, MomentPage } from '@/types'

// 图片资源导入(mock 用)
import img01 from '@/assets/img2/01.PNG'
import img02 from '@/assets/img2/02.PNG'
import img03 from '@/assets/img2/03.PNG'
import img04 from '@/assets/img2/04.PNG'
import img05 from '@/assets/img2/05.PNG'

/** 全量说说数据(按时间倒序排列) */
const allMoments: Moment[] = [
  {
    id: 1,
    date: '2026-07-14T09:22:00',
    content: '今天把说说页重构了，终于有了液态玻璃的感觉，每张卡片都像是漂浮在水面上的便签纸。',
    mood: '开心',
    tags: ['博客', '开发'],
    images: [],
    likes: 3,
  },
  {
    id: 2,
    date: '2026-07-12T21:15:00',
    content: '深夜写代码的时候窗外下起了雨，雨声和键盘声混在一起，竟然觉得很治愈。',
    mood: '平静',
    tags: ['日常', '夜晚'],
    images: [img01],
    likes: 7,
  },
  {
    id: 3,
    date: '2026-07-12T14:30:00',
    content: '午后的阳光透过百叶窗在桌面上投下条纹状的光影，像极了代码编辑器里的斑马条纹高亮。',
    mood: '灵感',
    tags: ['日常'],
    images: [],
    likes: 5,
  },
  {
    id: 4,
    date: '2026-07-10T16:45:00',
    content: '在 Vue 里把一个 UI 拆成小组件的时候，就像在搭积木一样有成就感。今天把归档页的时间河流做好了！',
    mood: '开心',
    tags: ['前端', 'vue'],
    images: [img02, img03],
    likes: 12,
  },
  {
    id: 5,
    date: '2026-07-08T20:10:00',
    content: '晚上路过河边，看见有人在桥下弹吉他，声音飘在水面上，像另一种波光粼粼。',
    mood: '感动',
    tags: ['生活', '夜晚'],
    images: [],
    likes: 9,
  },
  {
    id: 6,
    date: '2026-07-05T11:00:00',
    content: '发现了一个超棒的 CSS 技巧，用 backdrop-filter 可以做出真正的毛玻璃效果，不过性能开销不小。后来改用 WebGL 实现了液态玻璃，效果炸裂。',
    mood: '灵感',
    tags: ['前端', 'CSS'],
    images: [img04, img05, img01],
    likes: 15,
  },
  {
    id: 7,
    date: '2026-07-03T08:30:00',
    content: '早起跑步，六点的城市特别安静，只有洒水车和早餐摊的声音。',
    mood: '平静',
    tags: ['生活'],
    images: [],
    likes: 4,
  },
  {
    id: 8,
    date: '2026-07-01T22:00:00',
    content: '终于把博客的归档树做好了，看着那些树枝上挂着文章卡片的样子，七月快乐。',
    mood: '开心',
    tags: ['博客', '开发'],
    images: [img02],
    likes: 8,
  },
  {
    id: 9,
    date: '2026-06-28T15:20:00',
    content: '读完了《重构》第二版，虽然很多内容已经知道了，但系统性地再看一遍还是有新的体会。代码就像文章，要反复打磨才能简洁有力。',
    mood: '思考',
    tags: ['阅读', '编程'],
    images: [],
    likes: 6,
  },
  {
    id: 10,
    date: '2026-06-25T19:45:00',
    content: '今天尝试用 Rust 写了一个小工具，编译器的错误提示真的太友好了，感觉被编译器教育了一整天。',
    mood: '疲惫',
    tags: ['Rust', '学习'],
    images: [],
    likes: 11,
  },
  {
    id: 11,
    date: '2026-06-22T10:00:00',
    content: '周末去了趟图书馆，找了个靠窗的位子，阳光、咖啡、代码，完美的一天。',
    mood: '开心',
    tags: ['日常', '周末'],
    images: [img03, img04],
    likes: 14,
  },
  {
    id: 12,
    date: '2026-06-20T23:30:00',
    content: '半夜突然想到一个 bug 的解法，爬起来写完才安心睡觉。程序员的强迫症没救了。',
    mood: '灵感',
    tags: ['编程', '日常'],
    images: [],
    likes: 10,
  },
  {
    id: 13,
    date: '2026-06-18T14:00:00',
    content: '给博客加了深色模式的主题切换，那个遮罩展开动画调了一下午终于满意了。',
    mood: '满足',
    tags: ['博客', '前端'],
    images: [img05],
    likes: 7,
  },
  {
    id: 14,
    date: '2026-06-15T09:00:00',
    content: '开始规划博客的书架功能，打算用 epubjs 在浏览器里直接阅读电子书。',
    mood: '期待',
    tags: ['博客', '计划'],
    images: [],
    likes: 5,
  },
  {
    id: 15,
    date: '2026-06-12T17:30:00',
    content: '今天的夕阳特别好看，橙红色渐变到紫色，像是 Tailwind 调色板里的 gradient。',
    mood: '感动',
    tags: ['日常', '自然'],
    images: [img01, img02, img03, img04],
    likes: 18,
  },
]

/**
 * 分页获取说说列表
 * @param page 页码(从 1 开始)
 * @param pageSize 每页条数,默认 10
 * @returns 当前页数据 + 总条数
 *
 * 将来替换为 API 调用时保持此签名即可无缝迁移:
 * export async function getMoments(page, pageSize): Promise<MomentPage>
 */
export function getMoments(page: number = 1, pageSize: number = 10): MomentPage {
  const start = (page - 1) * pageSize
  const items = allMoments.slice(start, start + pageSize)
  return { items, total: allMoments.length }
}

/** 获取全部说说(不分页,用于统计等场景) */
export function getAllMoments(): Moment[] {
  return allMoments
}
