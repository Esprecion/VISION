<template>
  <div class="empty-state">
    <component
      :is="icon"
      class="empty-state__icon"
      aria-hidden="true"
    />
    <p class="empty-state__title">{{ title }}</p>
    <p v-if="description" class="empty-state__description">{{ description }}</p>
    <div v-if="$slots.action" class="empty-state__action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import InboxIcon from '~icons/lucide/inbox'

defineProps({
  title: { type: String, default: 'Nothing here yet' },
  description: { type: String, default: '' },
  icon: { type: [String, Object], default: () => InboxIcon },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--space-2);
  padding: var(--space-8) var(--space-4);
}
.empty-state__icon {
  width: 28px;
  height: 28px;
  color: var(--color-gray-400);
  margin-bottom: var(--space-1);
}
.empty-state__title {
  margin: 0;
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--color-gray-900);
}
.empty-state__description {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--color-gray-600);
  max-width: 42ch;
}
.empty-state__action {
  margin-top: var(--space-2);
}
</style>
