import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// Vite 构建配置
export default defineConfig({
  base: './',
  // 局域网开发预览时可恢复下面配置（生产部署不需要）：
  // server: {
  //   host: true,
  //   proxy: {
  //     '/api': { target: 'http://localhost:8000', changeOrigin: true },
  //     '/uploads': { target: 'http://localhost:8000', changeOrigin: true },
  //   },
  // },
  plugins: [
    vue(),
    tailwindcss(),
    // Element Plus 按需自动导入:组件 + API(ref/reactive 等不重复配置,只处理 ElMessage 等)
    AutoImport({
      resolvers: [ElementPlusResolver()],
      // 生成的类型声明文件,避免 TS 报错
      dts: 'src/auto-imports.d.ts',
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      // 禁止自动扫描 src/components/ 目录,博客前台组件继续用显式 import
      // 只让 ElementPlusResolver 处理 el-* 组件的按需加载
      dirs: [],
      // 生成的组件类型声明文件
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      // 路径别名 @ 指向 src 目录,与 tsconfig.json 的 paths 保持一致
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    // 暂停 CSS 压缩，保留标准 backdrop-filter 声明，避免生产产物只留下前缀版本。
    cssMinify: false,
    rollupOptions: {
      output: {
        // 手动分包:把体积较大的依赖拆出独立 chunk,优化首屏加载
        manualChunks(id: string) {
          if (
            id.includes('node_modules/vue') ||
            id.includes('node_modules/vue-router') ||
            id.includes('node_modules/pinia')
          ) {
            return 'vue-vendor'
          }
          if (id.includes('node_modules/marked')) {
            return 'marked'
          }
          // Element Plus 独立分包,博客前台访客不会加载
          if (id.includes('node_modules/element-plus')) {
            return 'element-plus'
          }
          // Vditor Markdown 编辑器独立分包
          if (id.includes('node_modules/vditor')) {
            return 'vditor'
          }
        },
      },
    },
  },
})
