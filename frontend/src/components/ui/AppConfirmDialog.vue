<template>
  <Dialog v-model="show" :options="{ title, size: 'sm' }" @close="close">
    <template #body-content>
      <p class="confirm-dialog__message">{{ message }}</p>
    </template>
    <template #actions="{ close: dismiss }">
      <div class="confirm-dialog__actions">
        <AppButton variant="outline" size="md" @click="dismiss">
          Cancel
        </AppButton>
        <AppButton
          :theme="destructive ? 'red' : 'gray'"
          variant="solid"
          size="md"
          :loading="loading"
          @click="confirm"
        >
          {{ confirmLabel }}
        </AppButton>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed } from 'vue'
import { Dialog } from 'frappe-ui'
import AppButton from './AppButton.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  destructive: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const show = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

function confirm() {
  emit('confirm')
}

function close() {
  emit('cancel')
}
</script>

<style scoped>
.confirm-dialog__message {
  margin: 0;
  font-size: var(--fs-sm);
  line-height: 1.5;
  color: var(--color-gray-700);
}
.confirm-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
</style>
