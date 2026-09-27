<template>
  <div class="toast-stack">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="t.type">
      <span>{{ t.message }}</span>
      <button v-if="t.action" class="toast-action" @click="onAction(t)">{{ t.action.label }}</button>
    </div>
  </div>
</template>

<script setup>
import { useToast } from '@/composables/useToast'
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
  background: #111827;
  color: #ffffff;
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
  background: #065f46;
}
.toast.error {
  background: #991b1b;
}
.toast-action {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: #ffffff;
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
