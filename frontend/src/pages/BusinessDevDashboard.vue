<template>
  <div class="dashboard">
    <PageHeader title="Business Development">
      <template #actions>
        <div class="period-picker">
          <input type="date" v-model="fromInput" :max="toInput" aria-label="From date" />
          <span class="range-label">to</span>
          <input type="date" v-model="toInput" :min="fromInput" aria-label="To date" />
          <button type="button" @click="setRange(quarterRange(0))">This quarter</button>
          <button type="button" @click="setRange(quarterRange(-1))">Last quarter</button>
          <button type="button" @click="setRange(yearRange())">This year</button>
        </div>
        <RouterLink to="/business-dev/pipeline" class="kanban-link">
          View Pipeline
          <ArrowRightIcon class="kanban-link__icon" aria-hidden="true" />
        </RouterLink>
      </template>
    </PageHeader>

    <!-- Compact stat tile -->
    <div class="stat-tiles stat-tiles-single">
      <div v-if="conversionRate.loading" class="stat-tile">
        <AppSkeleton variant="tile" />
      </div>
      <div v-else-if="conversionRate.error" class="stat-tile">
        <div class="stat-label">CONVERSION RATE</div>
        <div class="stat-value">—</div>
        <div class="stat-sub stat-sub--error">
          Couldn't load.
          <button type="button" class="retry-link" @click="conversionRate.reload()">
            Retry
          </button>
        </div>
      </div>
      <div v-else class="stat-tile">
        <div class="stat-label">CONVERSION RATE</div>
        <div class="stat-value">{{ conversionRateDisplay }}%</div>
        <div class="stat-sub" v-if="conversionRow">
          {{ conversionRow.won_count }} won of {{ conversionRow.total_deals }} deals
        </div>
        <div class="stat-sub" v-else>No deals in this period</div>
      </div>
    </div>

    <div class="chart-row">
      <!-- Average Time per Pipeline Stage -->
      <div class="card chart-card">
        <div class="card-label">Average Time per Pipeline Stage</div>
        <BarList
          :rows="stageTimeBarRows"
          :loading="stageTime.loading"
          :error="stageTime.error"
          :on-retry="() => stageTime.reload()"
          color="blue"
        />
        <button
          v-if="stageTimeRows.length > 4"
          type="button"
          class="see-more"
          @click="showAllStageTime = !showAllStageTime"
        >
          <template v-if="showAllStageTime">
            Show less
            <ChevronUpIcon class="see-more__icon" aria-hidden="true" />
          </template>
          <template v-else>
            +{{ stageTimeRows.length - 4 }} more
            <ChevronDownIcon class="see-more__icon" aria-hidden="true" />
          </template>
        </button>
      </div>

      <!-- Product Type Performance -->
      <div class="card chart-card">
        <div class="card-label">Product Type Performance</div>
        <BarList
          :rows="productTypeBarRows"
          :loading="productType.loading"
          :error="productType.error"
          :on-retry="() => productType.reload()"
          color="amber"
        />
        <button
          v-if="productTypeRows.length > 4"
          type="button"
          class="see-more"
          @click="showAllProductType = !showAllProductType"
        >
          <template v-if="showAllProductType">
            Show less
            <ChevronUpIcon class="see-more__icon" aria-hidden="true" />
          </template>
          <template v-else>
            +{{ productTypeRows.length - 4 }} more
            <ChevronDownIcon class="see-more__icon" aria-hidden="true" />
          </template>
        </button>
      </div>
    </div>

    <div class="chart-row">
      <!-- Geographic Distribution -->
      <div class="card chart-card">
        <div class="card-label">Geographic Distribution of Clients</div>
        <BarList
          :rows="geoBarRows"
          :loading="geo.loading"
          :error="geo.error"
          :on-retry="() => geo.reload()"
          color="blue"
        />
        <button
          v-if="geoRows.length > 4"
          type="button"
          class="see-more"
          @click="showAllGeo = !showAllGeo"
        >
          <template v-if="showAllGeo">
            Show less
            <ChevronUpIcon class="see-more__icon" aria-hidden="true" />
          </template>
          <template v-else>
            +{{ geoRows.length - 4 }} more
            <ChevronDownIcon class="see-more__icon" aria-hidden="true" />
          </template>
        </button>
      </div>

      <!-- Client Pipeline Velocity — table, not a chart -->
      <div class="card chart-card">
        <div class="card-label">Client Pipeline Velocity</div>
        <AppSkeleton v-if="velocity.loading" variant="table" :rows="4" :cols="3" />
        <ErrorState
          v-else-if="velocity.error"
          title="Couldn't load this table"
          :message="velocity.error.message"
          :on-retry="() => velocity.reload()"
        />
        <EmptyState
          v-else-if="!velocityRows.length"
          title="No deals in this period"
          description="Deals that entered the pipeline during the selected dates will appear here."
        />
        <template v-else>
          <div class="table-scroll">
            <table class="velocity-table">
              <thead>
                <tr>
                  <th>Deal</th>
                  <th>Client</th>
                  <th>Hours in Pipeline</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in visibleVelocityRows" :key="row.deal">
                  <td>{{ row.deal_title }}</td>
                  <td>{{ row.client_name }}</td>
                  <td :class="{ stale: row.velocity_hours > 336 }">
                    {{ row.velocity_hours ?? '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <button
            v-if="velocityRows.length > 4"
            type="button"
            class="see-more"
            @click="showAllVelocity = !showAllVelocity"
          >
            <template v-if="showAllVelocity">
              Show less
              <ChevronUpIcon class="see-more__icon" aria-hidden="true" />
            </template>
            <template v-else>
              +{{ velocityRows.length - 4 }} more
              <ChevronDownIcon class="see-more__icon" aria-hidden="true" />
            </template>
          </button>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { quarterRange, yearRange } from '../utils/dateRange'
import PageHeader from '@/components/ui/PageHeader.vue'
import BarList from '@/components/ui/BarList.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ArrowRightIcon from '~icons/lucide/arrow-right'
import ChevronUpIcon from '~icons/lucide/chevron-up'
import ChevronDownIcon from '~icons/lucide/chevron-down'

const initialRange = quarterRange(0)
const fromInput = ref(initialRange.from)
const toInput = ref(initialRange.to)
const fromDate = computed(() => fromInput.value)
const toDate = computed(() => `${toInput.value} 23:59:59`)
function setRange(r) {
  fromInput.value = r.from
  toInput.value = r.to
}

const reportRegistry = []

function useReport(reportName) {
  const resource = createResource({
    url: 'frappe.desk.query_report.run',
    params: {
      report_name: reportName,
      filters: { from_date: fromDate.value, to_date: toDate.value },
    },
    auto: true,
  })
  reportRegistry.push({ resource, reportName })
  return resource
}

const conversionRate = useReport('Pipeline Conversion Rate')
const stageTime = useReport('Average Time Per Pipeline Stage')
const productType = useReport('Product Type Performance')
const geo = useReport('Geographic Distribution of Clients')
const velocity = useReport('Client Pipeline Velocity')

watch([fromInput, toInput], () => {
  if (!fromInput.value || !toInput.value || fromInput.value > toInput.value) return
  const filters = { from_date: fromDate.value, to_date: toDate.value }
  reportRegistry.forEach(({ resource, reportName }) => {
    resource.update({ params: { report_name: reportName, filters } })
    resource.reload()
  })
})

const conversionRow = computed(() => conversionRate.data?.result?.[0])
const conversionRateDisplay = computed(() =>
  conversionRow.value ? Number(conversionRow.value.conversion_rate_pct).toFixed(2) : '0.00'
)

const showAllStageTime = ref(false)
const stageTimeRows = computed(() => stageTime.data?.result ?? [])
const visibleStageTimeRows = computed(() => showAllStageTime.value ? stageTimeRows.value : stageTimeRows.value.slice(0, 4))
const stageTimeBarRows = computed(() =>
  visibleStageTimeRows.value.map((r) => ({
    label: r.stage,
    value: r.avg_hours_in_stage,
    display: `${r.avg_hours_in_stage}h`,
  }))
)

const showAllProductType = ref(false)
const productTypeRows = computed(() => productType.data?.result ?? [])
const visibleProductTypeRows = computed(() => showAllProductType.value ? productTypeRows.value : productTypeRows.value.slice(0, 4))
const productTypeBarRows = computed(() =>
  visibleProductTypeRows.value.map((r) => ({
    label: r.product_type,
    value: r.total_value,
    display: peso(r.total_value),
  }))
)

const showAllGeo = ref(false)
const geoRows = computed(() => geo.data?.result ?? [])
const visibleGeoRows = computed(() => showAllGeo.value ? geoRows.value : geoRows.value.slice(0, 4))
const geoBarRows = computed(() =>
  visibleGeoRows.value.map((r) => ({
    label: r.territory || 'Unassigned',
    value: r.total_value,
    display: peso(r.total_value),
  }))
)

const showAllVelocity = ref(false)
const velocityRows = computed(() => velocity.data?.result ?? [])
const visibleVelocityRows = computed(() => showAllVelocity.value ? velocityRows.value : velocityRows.value.slice(0, 4))

function peso(n) {
  if (n == null) return '₱0'
  return '₱' + Number(n).toLocaleString('en-PH')
}
</script>

<style scoped>
.dashboard {
  background: var(--color-gray-50);
  min-height: 100vh;
  padding: var(--page-pad);
  color: var(--color-gray-900);
}

.period-picker {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.period-picker input {
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-sm);
  padding: 6px var(--space-2);
  font-size: var(--fs-sm);
  background: var(--color-white);
  color: var(--color-gray-900);
  font-family: inherit;
}
.period-picker button {
  border: 1px solid var(--color-gray-200);
  background: var(--color-white);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-size: var(--fs-sm);
  color: var(--color-gray-900);
  cursor: pointer;
  font-family: inherit;
}
.period-picker button:hover {
  background: var(--color-gray-100);
}
.range-label {
  color: var(--color-gray-600);
  font-size: var(--fs-xs);
  white-space: nowrap;
}
.kanban-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-gray-600);
  text-decoration: none;
  font-size: var(--fs-sm);
  font-weight: 500;
  white-space: nowrap;
}
.kanban-link:hover {
  color: var(--color-amber-700);
}
.kanban-link__icon {
  width: 14px;
  height: 14px;
}

.card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-xs);
}

.stat-tiles {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.stat-tiles-single {
  grid-template-columns: minmax(200px, 280px);
}
.stat-tile {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-5);
  box-shadow: var(--shadow-xs);
}
.stat-label {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  font-weight: 600;
  letter-spacing: 0.03em;
  margin-bottom: var(--space-2);
}
.stat-value {
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--color-gray-900);
  font-variant-numeric: tabular-nums;
}
.stat-sub {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  margin-top: var(--space-1);
}
.stat-sub--error {
  color: var(--color-red-600);
}
.retry-link {
  background: none;
  border: none;
  padding: 0;
  color: var(--color-amber-700);
  font-weight: 600;
  font-size: var(--fs-xs);
  cursor: pointer;
  text-decoration: underline;
  font-family: inherit;
}
.see-more {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  background: none;
  border: none;
  color: var(--color-amber-700);
  font-size: var(--fs-xs);
  font-weight: 600;
  cursor: pointer;
  padding: var(--space-1) 0 0;
  text-align: left;
  font-family: inherit;
}
.see-more__icon {
  width: 12px;
  height: 12px;
}
.card-label {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  font-weight: 500;
  margin-bottom: var(--space-2);
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  align-items: stretch;
}
.chart-card {
  min-height: 200px;
}

.table-scroll {
  overflow-x: auto;
}
.velocity-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: var(--space-2);
  font-size: var(--fs-sm);
}
.velocity-table th {
  text-align: left;
  color: var(--color-gray-600);
  font-weight: 500;
  padding: var(--space-2) var(--space-1);
  border-bottom: 1px solid var(--color-gray-200);
  white-space: nowrap;
}
.velocity-table td {
  padding: var(--space-2) var(--space-1);
  border-bottom: 1px solid var(--color-gray-200);
  color: var(--color-gray-900);
}
.velocity-table td.stale {
  color: var(--color-red-600);
  font-weight: 600;
}

@media (max-width: 900px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .stat-tiles-single {
    grid-template-columns: 1fr;
  }
}
</style>
