<template>
  <div
    v-if="variant === 'table'"
    class="skeleton-table"
    role="presentation"
    aria-hidden="true"
  >
    <div class="skeleton-table__row skeleton-table__row--head">
      <span
        v-for="c in cols"
        :key="'h' + c"
        class="skeleton"
        style="height: 10px; width: 70%"
      />
    </div>
    <div v-for="r in rows" :key="r" class="skeleton-table__row">
      <span
        v-for="c in cols"
        :key="c"
        class="skeleton"
        style="height: 12px"
        :style="{ width: c === 1 ? '85%' : '60%' }"
      />
    </div>
  </div>

  <div
    v-else-if="variant === 'chart'"
    class="skeleton-chart"
    role="presentation"
    aria-hidden="true"
  >
    <div v-for="r in rows" :key="r" class="skeleton-chart__row">
      <span class="skeleton" style="height: 12px; width: 90px" />
      <span class="skeleton skeleton-chart__track" style="height: 10px" />
      <span class="skeleton" style="height: 12px; width: 56px" />
    </div>
  </div>

  <div
    v-else-if="variant === 'tile'"
    class="skeleton skeleton-tile"
    role="presentation"
    aria-hidden="true"
  >
    <span class="skeleton" style="height: 10px; width: 60%" />
    <span class="skeleton" style="height: 22px; width: 45%" />
    <span class="skeleton" style="height: 10px; width: 70%" />
  </div>

  <div
    v-else-if="variant === 'card'"
    class="skeleton skeleton-card"
    role="presentation"
    aria-hidden="true"
  >
    <span class="skeleton" style="height: 12px; width: 50%" />
    <span class="skeleton" style="height: 10px; width: 80%" />
    <span class="skeleton" style="height: 10px; width: 65%" />
  </div>

  <div
    v-else
    class="skeleton-lines"
    role="presentation"
    aria-hidden="true"
  >
    <span
      v-for="r in rows"
      :key="r"
      class="skeleton"
      style="height: 12px"
      :style="{ width: r === rows ? '60%' : '100%' }"
    />
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'text', // text | tile | card | chart | table
  },
  rows: { type: Number, default: 4 },
  cols: { type: Number, default: 4 },
})
</script>

<style scoped>
.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: 100%;
}
.skeleton-tile {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}
.skeleton-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-5);
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}
.skeleton-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  width: 100%;
}
.skeleton-chart__row {
  display: grid;
  grid-template-columns: 90px 1fr 56px;
  gap: var(--space-3);
  align-items: center;
}
.skeleton-chart__track {
  width: 100%;
}
.skeleton-table {
  display: flex;
  flex-direction: column;
  width: 100%;
}
.skeleton-table__row {
  display: grid;
  grid-auto-columns: 1fr;
  grid-auto-flow: column;
  gap: var(--space-4);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-gray-100);
}
.skeleton-table__row--head {
  background: var(--color-gray-50);
}
@media (max-width: 640px) {
  .skeleton-chart__row {
    grid-template-columns: 70px 1fr 48px;
    gap: var(--space-2);
  }
}
</style>
