<template>
  <div class="bar-list">
    <AppSkeleton v-if="loading" variant="chart" :rows="4" />
    <ErrorState
      v-else-if="error"
      title="Couldn't load this chart"
      :message="errorMessage"
      :on-retry="onRetry"
    />
    <EmptyState
      v-else-if="!rows.length"
      :title="emptyTitle"
      :description="emptyDescription"
    />
    <div v-else class="bar-list__rows" role="list">
      <div
        v-for="row in rows"
        :key="row.label"
        class="bar-row"
        role="listitem"
      >
        <div class="bar-row__label" :title="row.label">{{ row.label }}</div>
        <div class="bar-track">
          <div
            class="bar-fill"
            :class="`bar-fill--${color}`"
            :style="{ width: pct(row.value) }"
          />
        </div>
        <div class="bar-row__value">{{ row.display ?? format(row.value) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppSkeleton from './AppSkeleton.vue'
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: [Object, Error, Boolean], default: null },
  onRetry: { type: Function, default: null },
  color: { type: String, default: 'blue' }, // blue | amber | green | red | indigo
  emptyTitle: { type: String, default: 'No data for this period' },
  emptyDescription: { type: String, default: '' },
})

const max = computed(() => {
  const values = props.rows.map((r) => Number(r.value) || 0)
  return Math.max(1, ...values)
})

function pct(value) {
  const v = Number(value) || 0
  return `${Math.max(v > 0 ? 2 : 0, (v / max.value) * 100)}%`
}

function format(value) {
  return String(value ?? '')
}

const errorMessage = computed(() => {
  const e = props.error
  if (!e) return ''
  if (typeof e === 'string') return e
  return e.message || 'The request failed. Please try again.'
})
</script>

<style scoped>
.bar-list {
  width: 100%;
  min-width: 0;
}
.bar-list__rows {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.bar-row {
  display: grid;
  grid-template-columns: minmax(0, 130px) 1fr 92px;
  gap: var(--space-3);
  align-items: center;
}
.bar-row__label {
  font-size: var(--fs-sm);
  color: var(--color-gray-700);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bar-track {
  height: 10px;
  border-radius: var(--radius-full);
  background: var(--color-gray-100);
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}
.bar-fill--blue {
  background: var(--color-blue-500);
}
.bar-fill--indigo {
  background: var(--color-indigo-500);
}
.bar-fill--amber {
  background: var(--color-amber-500);
}
.bar-fill--green {
  background: var(--color-emerald-500);
}
.bar-fill--red {
  background: var(--color-red-500);
}
.bar-row__value {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--color-gray-900);
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
@media (max-width: 640px) {
  .bar-row {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      'label value'
      'track track';
    row-gap: var(--space-1);
  }
  .bar-row__label {
    grid-area: label;
  }
  .bar-track {
    grid-area: track;
  }
  .bar-row__value {
    grid-area: value;
  }
}
</style>
