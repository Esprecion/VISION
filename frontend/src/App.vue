<template>
  <div class="app-shell">
    <Sidebar />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/Sidebar.vue'
</script>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  background: #05070d;
}
.app-main {
  flex: 1;
  min-width: 0;
}
</style>
