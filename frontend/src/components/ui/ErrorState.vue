<template>
  <div class="error-state" role="alert">
    <AlertCircleIcon class="error-state__icon" aria-hidden="true" />
    <p class="error-state__title">{{ title }}</p>
    <p v-if="message" class="error-state__message">{{ message }}</p>
    <AppButton
      v-if="onRetry"
      class="error-state__retry"
      variant="outline"
      size="sm"
      @click="onRetry"
    >
      Retry
    </AppButton>
    <div v-if="$slots.action" class="error-state__action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppButton from './AppButton.vue'

defineProps({
  title: { type: String, default: 'Something went wrong' },
  message: { type: String, default: '' },
  onRetry: { type: Function, default: null },
})
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: var(--space-2);
  padding: var(--space-8) var(--space-4);
}
.error-state__icon {
  width: 28px;
  height: 28px;
  color: var(--color-red-600);
  margin-bottom: var(--space-1);
}
.error-state__title {
  margin: 0;
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--color-gray-900);
}
.error-state__message {
  margin: 0;
  font-size: var(--fs-sm);
  color: var(--color-gray-600);
  max-width: 48ch;
  word-break: break-word;
}
.error-state__retry,
.error-state__action {
  margin-top: var(--space-2);
}
</style>
