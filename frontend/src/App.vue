<template>
  <div class="app-shell">
    <Sidebar />
    <main class="app-main">
      <router-view />
    </main>
    <ToastContainer />
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import ToastContainer from '@/components/ToastContainer.vue'
</script>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--color-gray-50);
}
.app-main {
  flex: 1;
  min-width: 0;
}
</style>
