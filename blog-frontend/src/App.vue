<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'

onMounted(() => {
  const splash = document.getElementById('splash')
  const app = document.getElementById('app')
  if (app) app.style.opacity = '1'
  if (splash) {
    splash.classList.add('hide')
    setTimeout(() => splash.remove(), 400)
  }
})
</script>

<template>
  <div class="app-shell">
    <NavBar />
    <RouterView />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}
</style>
