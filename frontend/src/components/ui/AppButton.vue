<template>
  <Button
    class="app-button"
    :theme="theme"
    :variant="variant"
    :size="size"
    :loading="loading"
    :disabled="disabled"
    :label="label"
    v-bind="$attrs"
  >
    <template v-if="$slots.prefix" #prefix><slot name="prefix" /></template>
    <template v-if="$slots.default" #default><slot /></template>
    <template v-if="$slots.suffix" #suffix><slot name="suffix" /></template>
  </Button>
</template>

<script setup>
import { Button } from 'frappe-ui'

defineOptions({ inheritAttrs: false })

defineProps({
  label: { type: String, default: '' },
  theme: { type: String, default: 'gray' },
  variant: { type: String, default: 'subtle' },
  size: { type: String, default: 'md' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})
</script>

<style scoped>
.app-button:focus-visible {
  outline: var(--focus-ring);
  outline-offset: var(--focus-ring-offset);
  box-shadow: none;
}
</style>
