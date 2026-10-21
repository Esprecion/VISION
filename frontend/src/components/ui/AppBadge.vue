<template>
  <Badge :theme="mappedTheme" :variant="variant" :size="size" :label="label">
    <template v-if="$slots.default" #default><slot /></template>
    <template v-if="$slots.prefix" #prefix><slot name="prefix" /></template>
    <template v-if="$slots.suffix" #suffix><slot name="suffix" /></template>
  </Badge>
</template>

<script setup>
import { computed } from 'vue'
import { Badge } from 'frappe-ui'

const THEMES = {
  neutral: 'gray',
  success: 'green',
  warning: 'orange',
  danger: 'red',
  info: 'blue',
  amber: 'orange',
}

const props = defineProps({
  label: { type: [String, Number], default: '' },
  color: { type: String, default: 'neutral' },
  variant: { type: String, default: 'subtle' },
  size: { type: String, default: 'md' },
})

const mappedTheme = computed(() => THEMES[props.color] || 'gray')
</script>
