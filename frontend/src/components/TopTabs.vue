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
  gap: var(--space-2);
  border-bottom: 1px solid var(--color-gray-200);
  padding: 0 var(--page-pad);
  background: var(--color-white);
  position: sticky;
  top: 0;
  z-index: 30;
  overflow-x: auto;
  scrollbar-width: none;
}
.top-tabs::-webkit-scrollbar {
  display: none;
}
.tab-item {
  color: var(--color-gray-600);
  font-size: var(--fs-sm);
  padding: var(--space-3) var(--space-1);
  border-bottom: 2px solid transparent;
  text-decoration: none;
  white-space: nowrap;
}
.tab-item:hover {
  color: var(--color-gray-900);
}
.tab-item-active {
  color: var(--color-amber-800);
  border-bottom-color: var(--color-amber-700);
}
</style>
