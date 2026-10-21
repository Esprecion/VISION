<template>
  <Card
    class="app-card"
    :title="title"
    :subtitle="subtitle"
    :loading="loading"
  >
    <template v-if="$slots['actions-left']" #actions-left>
      <slot name="actions-left" />
    </template>
    <template v-if="$slots.actions" #actions><slot name="actions" /></template>
    <template v-if="$slots.default" #default><slot /></template>
  </Card>
</template>

<script setup>
import { Card } from 'frappe-ui'

defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.app-card {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}
.app-card:focus-visible {
  outline: var(--focus-ring);
  outline-offset: var(--focus-ring-offset);
}
</style>
