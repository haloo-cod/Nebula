import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// Vite 构建配置
export default defineConfig({
  base: './',
  plugins: [
    vue(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // 路径别名 @ 指向 src 目录,与 tsconfig.json 的 paths 保持一致
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
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
        },
      },
    },
  },
})
