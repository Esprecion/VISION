<script setup lang="ts">
import TopTabs from '@/components/TopTabs.vue'

defineProps<{
  tabs: { label: string; to: string }[]
}>()
</script>

<template>
  <div>
    <TopTabs :tabs="tabs" />
    <div class="department-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.department-content {
  padding: 1.5rem;
}
</style>
