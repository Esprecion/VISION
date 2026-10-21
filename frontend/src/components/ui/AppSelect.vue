<template>
  <div class="app-field">
    <label v-if="label" class="app-field__label">
      {{ label }}
      <span v-if="required" class="app-field__req" aria-hidden="true">*</span>
    </label>
    <Select
      :options="options"
      :model-value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :size="size"
      :variant="variant"
      v-bind="$attrs"
      @update:model-value="emit('update:modelValue', $event)"
    >
      <template v-for="(_, name) in $slots" #[name]="scope">
        <slot :name="name" v-bind="scope" />
      </template>
    </Select>
  </div>
</template>

<script setup>
import { Select } from 'frappe-ui'

defineOptions({ inheritAttrs: false })

defineProps({
  modelValue: { type: [String, Number, Boolean], default: undefined },
  label: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Select option' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  size: { type: String, default: 'sm' },
  variant: { type: String, default: 'outline' },
})

const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.app-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}
.app-field__label {
  font-size: var(--fs-xs);
  font-weight: 500;
  color: var(--color-gray-600);
}
.app-field__req {
  color: var(--color-red-600);
  margin-inline-start: 2px;
}
</style>
