<template>
  <div class="app-search">
    <label :for="inputId" class="sr-only">{{ label }}</label>
    <AppTextInput
      :id="inputId"
      :model-value="modelValue"
      type="search"
      :placeholder="placeholder"
      :size="size"
      :debounce="debounce"
      @update:model-value="emit('update:modelValue', $event)"
    >
      <template #prefix>
        <SearchIcon class="app-search__icon" aria-hidden="true" />
      </template>
    </AppTextInput>
  </div>
</template>

<script setup>
import { useId } from 'vue'
import SearchIcon from '~icons/lucide/search'
import AppTextInput from '@/components/ui/AppTextInput.vue'

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: 'Search' },
  placeholder: { type: String, default: 'Search...' },
  size: { type: String, default: 'sm' },
  debounce: { type: Number, default: 0 },
})
const emit = defineEmits(['update:modelValue'])
const inputId = useId()
</script>

<style scoped>
.app-search {
  min-width: 0;
}
.app-search__icon {
  width: 16px;
  height: 16px;
  color: var(--color-gray-500);
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
