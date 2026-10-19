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
  border-bottom: 1px solid var(--color-gray-200);
  padding: 0 1.5rem;
  background: var(--color-white);
}
.tab-item {
  color: var(--color-gray-500);
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  padding: 0.9rem 0.25rem;
  border-bottom: 2px solid transparent;
  text-decoration: none;
}
.tab-item-active {
  color: var(--color-amber-700);
  border-bottom-color: var(--color-amber-700);
}
</style>
