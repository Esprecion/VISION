<template>
  <div class="app-field">
    <label v-if="label" :for="inputId" class="app-field__label">
      {{ label }}
      <span v-if="required" class="app-field__req" aria-hidden="true">*</span>
    </label>
    <TextInput
      :id="inputId"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :size="size"
      :variant="variant"
      :model-value="modelValue"
      :debounce="debounce"
      v-bind="$attrs"
      @update:model-value="emit('update:modelValue', $event)"
    >
      <template v-if="$slots.prefix" #prefix><slot name="prefix" /></template>
      <template v-if="$slots.suffix" #suffix><slot name="suffix" /></template>
    </TextInput>
  </div>
</template>

<script setup>
import { useId } from 'vue'
import { TextInput } from 'frappe-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  size: { type: String, default: 'sm' },
  variant: { type: String, default: 'outline' },
  debounce: { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue'])
const inputId = useId()
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
