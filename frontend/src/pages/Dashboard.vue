<template>
  <div class="dashboard">
    <PageHeader title="Dashboard" />
    <EmptyState
      title="Coming soon"
      description="Cross-department overview — coming once more modules exist."
    />
  </div>
</template>

<script setup>
import PageHeader from '@/components/ui/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
</script>

<style scoped>
.dashboard {
  background: var(--color-gray-50);
  min-height: 100vh;
  padding: var(--page-pad);
  color: var(--color-gray-900);
}
</style>
