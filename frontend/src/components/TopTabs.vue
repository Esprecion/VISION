<script setup lang="ts">
defineProps<{
  tabs: { label: string; to: string }[]
}>()
</script>

<template>
  <div class="top-tabs">
    <router-link
      v-for="tab in tabs"
      :key="tab.to"
      :to="tab.to"
      class="tab-item"
      active-class="tab-item-active"
    >
      {{ tab.label }}
    </router-link>
  </div>
</template>

<style scoped>
.top-tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
  padding: 0 1.5rem;
  background: #ffffff;
}
.tab-item {
  color: #6b7280;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  padding: 0.9rem 0.25rem;
  border-bottom: 2px solid transparent;
  text-decoration: none;
}
.tab-item-active {
  color: #b45309;
  border-bottom-color: #b45309;
}
</style>
