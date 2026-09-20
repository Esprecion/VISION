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
  border-bottom: 1px solid #1c2540;
  padding: 0 1.5rem;
}
.tab-item {
  color: #8b93a7;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  padding: 0.9rem 0.25rem;
  border-bottom: 2px solid transparent;
  text-decoration: none;
}
.tab-item-active {
  color: #C9A227;
  border-bottom-color: #C9A227;
}
</style>
