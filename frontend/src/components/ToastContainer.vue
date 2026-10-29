<template>
  <div class="toast-stack" role="region" aria-label="Notifications" aria-live="polite">
    <div
      v-for="t in toasts"
      :key="t.id"
      class="toast"
      :class="t.type"
      :role="t.type === 'error' ? 'alert' : 'status'"
      aria-atomic="true"
    >
      <span>{{ t.message }}</span>
      <button v-if="t.action" class="toast-action" @click="onAction(t)">{{ t.action.label }}</button>
      <button class="toast-close" aria-label="Dismiss notification" @click="dismissToast(t.id)">
        <XIcon aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { useToast } from '@/composables/useToast'
import XIcon from '~icons/lucide/x'
const { toasts, dismissToast } = useToast()
function onAction(t) {
  t.action.onClick()
  dismissToast(t.id)
}
</script>

<style scoped>
.toast-stack {
  position: fixed;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 100;
}
.toast {
  background: var(--color-gray-900);
  color: var(--color-white);
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: toast-in 0.2s ease-out;
  display: flex;
  align-items: center;
  gap: 12px;
}
.toast.success {
  background: var(--color-emerald-800);
}
.toast.error {
  background: var(--color-red-800);
}
.toast-action {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: var(--color-white);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}
.toast-action:hover {
  background: rgba(255, 255, 255, 0.25);
}
.toast-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
}
.toast-close:hover,
.toast-close:focus-visible {
  color: var(--color-white);
  background: rgba(255, 255, 255, 0.15);
}
.toast-close svg {
  width: 14px;
  height: 14px;
}
@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
