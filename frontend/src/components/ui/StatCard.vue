<template>
  <article class="stat-card">
    <div class="stat-card__label">{{ label }}</div>
    <AppSkeleton v-if="loading" variant="text" :rows="2" />
    <template v-else>
      <div class="stat-card__value" :class="`stat-card__value--${tone}`">{{ value }}</div>
      <div v-if="sub" class="stat-card__sub">{{ sub }}</div>
      <div v-if="$slots.default" class="stat-card__extra"><slot /></div>
    </template>
  </article>
</template>

<script setup>
import AppSkeleton from '@/components/ui/AppSkeleton.vue'

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  sub: { type: String, default: '' },
  tone: { type: String, default: 'default' },
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.stat-card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  padding: var(--space-4) var(--space-5);
}
.stat-card__label {
  margin-bottom: var(--space-2);
  color: var(--color-gray-600);
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.stat-card__value {
  color: var(--color-gray-900);
  font-size: var(--fs-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.stat-card__value--positive {
  color: var(--color-emerald-800);
}
.stat-card__value--negative {
  color: var(--color-red-700);
}
.stat-card__sub {
  margin-top: var(--space-1);
  color: var(--color-gray-600);
  font-size: var(--fs-xs);
}
.stat-card__extra {
  margin-top: var(--space-3);
}
</style>
