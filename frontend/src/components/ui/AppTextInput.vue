<template>
  <div class="app-field" :class="{ 'app-field--error': error }">
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
      :aria-invalid="error ? 'true' : undefined"
      v-bind="$attrs"
      @update:model-value="onUpdate"
    >
      <template v-if="$slots.prefix" #prefix><slot name="prefix" /></template>
      <template v-if="$slots.suffix" #suffix><slot name="suffix" /></template>
    </TextInput>
    <p v-if="error" class="app-field__error" role="alert">{{ error }}</p>
  </div>
</template>

<script setup>
import { useId } from 'vue'
import { TextInput } from 'frappe-ui'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  modelModifiers: { type: Object, default: () => ({}) },
  id: { type: String, default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  error: { type: String, default: '' },
  size: { type: String, default: 'sm' },
  variant: { type: String, default: 'outline' },
  debounce: { type: Number, default: 0 },
})

const emit = defineEmits(['update:modelValue'])
const generatedId = useId()
const inputId = props.id || generatedId

function onUpdate(val) {
  if (props.modelModifiers?.number) {
    if (val === '' || val === null || val === undefined) {
      emit('update:modelValue', '')
      return
    }
    const num = Number(val)
    emit('update:modelValue', isNaN(num) ? val : num)
    return
  }
  emit('update:modelValue', val)
}
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
.app-field__error {
  margin: 0;
  font-size: var(--fs-xs);
  color: var(--color-red-600);
}
.app-field--error :deep(input) {
  border-color: var(--color-red-400);
}
</style>
