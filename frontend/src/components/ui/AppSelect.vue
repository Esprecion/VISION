<template>
  <div class="app-field" :class="{ 'app-field--error': error }">
    <label v-if="label" :id="labelId" class="app-field__label">
      {{ label }}
      <span v-if="required" class="app-field__req" aria-hidden="true">*</span>
    </label>
    <Select
      :id="selectId"
      :options="options"
      :model-value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :size="size"
      :variant="variant"
      :aria-invalid="error ? 'true' : undefined"
      :aria-labelledby="label ? labelId : undefined"
      :aria-required="required ? 'true' : undefined"
      v-bind="$attrs"
      @update:model-value="emit('update:modelValue', $event)"
    >
      <template v-for="(_, name) in $slots" #[name]="scope">
        <slot :name="name" v-bind="scope" />
      </template>
    </Select>
    <p v-if="error" class="app-field__error" role="alert">{{ error }}</p>
  </div>
</template>

<script setup>
import { useId } from 'vue'
import { Select } from 'frappe-ui'

defineOptions({ inheritAttrs: false })

defineProps({
  modelValue: { type: [String, Number, Boolean], default: undefined },
  label: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Select option' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  error: { type: String, default: '' },
  size: { type: String, default: 'sm' },
  variant: { type: String, default: 'outline' },
})

const emit = defineEmits(['update:modelValue'])
const selectId = useId()
const labelId = `${selectId}-label`
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
.app-field--error :deep(button) {
  border-color: var(--color-red-400);
}
</style>
