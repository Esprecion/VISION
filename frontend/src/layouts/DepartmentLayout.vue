<script setup lang="ts">
import TopTabs from '@/components/TopTabs.vue'

defineProps<{
  tabs: { label: string; to: string }[]
}>()
</script>

<template>
  <div class="department-layout">
    <TopTabs :tabs="tabs" />
    <router-view :key="$route.fullPath" />
  </div>
</template>

<style scoped>
.department-layout {
  min-width: 0;
}
</style>
