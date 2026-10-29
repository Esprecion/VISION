<template>
  <span class="status-badge" :class="`status-badge--${tone}`">{{ value || '—' }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [String, Number], default: '' },
})

const TONES = {
  Draft: 'neutral',
  Kickoff: 'neutral',
  Chat: 'neutral',
  Call: 'neutral',
  Sent: 'info',
  Development: 'info',
  Testing: 'info',
  Email: 'info',
  Paid: 'success',
  Deployed: 'success',
  Meeting: 'success',
  Finalized: 'success',
  Overdue: 'danger',
  'Under Negotiation': 'warning',
  'Sent to Finance': 'info',
  Inactive: 'danger',
}

const tone = computed(() => TONES[props.value] || 'neutral')
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--fs-xs);
  font-weight: 600;
  white-space: nowrap;
}
.status-badge--neutral {
  background: var(--color-gray-100);
  color: var(--color-gray-700);
}
.status-badge--info {
  background: var(--color-blue-100);
  color: var(--color-blue-700);
}
.status-badge--success {
  background: var(--color-emerald-100);
  color: var(--color-emerald-800);
}
.status-badge--warning {
  background: var(--color-amber-100);
  color: var(--color-amber-800);
}
.status-badge--danger {
  background: var(--color-red-100);
  color: var(--color-red-700);
}
</style>
