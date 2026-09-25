<template>
  <div class="dashboard">
    <header class="dash-header">
      <h1>Business Development</h1>
      <div class="header-right">
        <div class="period-picker">
          <select v-model.number="selectedQuarter">
            <option :value="1">Q1</option>
            <option :value="2">Q2</option>
            <option :value="3">Q3</option>
            <option :value="4">Q4</option>
          </select>
          <select v-model.number="selectedYear">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <span class="range-label">{{ rangeLabel }}</span>
        <RouterLink to="/business-dev/pipeline" class="kanban-link">View Pipeline →</RouterLink>
      </div>
    </header>

    <!-- Pipeline Conversion Rate -->
    <div class="card hero-card">
      <div class="card-label">Pipeline Conversion Rate</div>
      <div v-if="conversionRate.loading" class="card-value loading">···</div>
      <div v-else class="card-value hero">{{ conversionRateDisplay }}%</div>
      <div class="card-sub" v-if="conversionRow">
        {{ conversionRow.won_count }} won of {{ conversionRow.total_deals }} deals
      </div>
    </div>

    <div class="chart-row">
      <!-- Average Time per Pipeline Stage -->
      <div class="card chart-card">
        <div class="card-label">Average Time per Pipeline Stage</div>
        <div v-if="stageTime.loading" class="card-value loading">···</div>
        <div v-else class="bars">
          <div
            v-for="row in stageTimeRows"
            :key="row.stage"
            class="bar-row"
          >
            <div class="bar-label">{{ row.stage }}</div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: barWidth(row.avg_hours_in_stage, maxStageHours) }"
              ></div>
            </div>
            <div class="bar-value">{{ row.avg_hours_in_stage }}h</div>
          </div>
        </div>
      </div>

      <!-- Product Type Performance -->
      <div class="card chart-card">
        <div class="card-label">Product Type Performance</div>
        <div v-if="productType.loading" class="card-value loading">···</div>
        <div v-else class="bars">
          <div
            v-for="row in productTypeRows"
            :key="row.product_type"
            class="bar-row"
          >
            <div class="bar-label">{{ row.product_type }}</div>
            <div class="bar-track">
              <div
                class="bar-fill gold"
                :style="{ width: barWidth(row.total_value, maxProductValue) }"
              ></div>
            </div>
            <div class="bar-value">{{ peso(row.total_value) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-row">
      <!-- Geographic Distribution -->
      <div class="card chart-card">
        <div class="card-label">Geographic Distribution of Clients</div>
        <div v-if="geo.loading" class="card-value loading">···</div>
        <div v-else class="bars">
          <div
            v-for="row in geoRows"
            :key="row.territory || 'unassigned'"
            class="bar-row"
          >
            <div class="bar-label">{{ row.territory || 'Unassigned' }}</div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: barWidth(row.total_value, maxGeoValue) }"
              ></div>
            </div>
            <div class="bar-value">{{ peso(row.total_value) }}</div>
          </div>
        </div>
      </div>

      <!-- Client Pipeline Velocity — table, not a chart -->
      <div class="card chart-card">
        <div class="card-label">Client Pipeline Velocity</div>
        <div v-if="velocity.loading" class="card-value loading">···</div>
        <table v-else class="velocity-table">
          <thead>
            <tr>
              <th>Deal</th>
              <th>Client</th>
              <th>Hours in Pipeline</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in velocityRows" :key="row.deal">
              <td>{{ row.deal_title }}</td>
              <td>{{ row.client_name }}</td>
              <td :class="{ stale: row.velocity_hours > 336 }">
                {{ row.velocity_hours ?? '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const today = new Date()
const currentQuarter = Math.ceil((today.getMonth() + 1) / 3)
const selectedQuarter = ref(currentQuarter)
const selectedYear = ref(today.getFullYear())
const yearOptions = computed(() => {
  const y = today.getFullYear()
  return [y - 2, y - 1, y, y + 1]
})

const quarterRanges = {
  1: ['01-01', '03-31'],
  2: ['04-01', '06-30'],
  3: ['07-01', '09-30'],
  4: ['10-01', '12-31'],
}

const fromDate = computed(() => `${selectedYear.value}-${quarterRanges[selectedQuarter.value][0]}`)
const toDate = computed(() => `${selectedYear.value}-${quarterRanges[selectedQuarter.value][1]}`)

function formatDisplayDate(isoStr) {
  const d = new Date(isoStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
const rangeLabel = computed(
  () => `${formatDisplayDate(fromDate.value)} – ${formatDisplayDate(toDate.value)}, ${selectedYear.value}`
)

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

watch([selectedQuarter, selectedYear], () => {
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

const stageTimeRows = computed(() => stageTime.data?.result ?? [])
const maxStageHours = computed(() =>
  Math.max(1, ...stageTimeRows.value.map((r) => Number(r.avg_hours_in_stage) || 0))
)

const productTypeRows = computed(() => productType.data?.result ?? [])
const maxProductValue = computed(() =>
  Math.max(1, ...productTypeRows.value.map((r) => Number(r.total_value) || 0))
)

const geoRows = computed(() => geo.data?.result ?? [])
const maxGeoValue = computed(() =>
  Math.max(1, ...geoRows.value.map((r) => Number(r.total_value) || 0))
)

const velocityRows = computed(() => velocity.data?.result ?? [])

function barWidth(value, max) {
  const pct = Math.max(2, (Number(value) / max) * 100)
  return pct + '%'
}

function peso(n) {
  if (n == null) return '₱0'
  return '₱' + Number(n).toLocaleString('en-PH')
}
</script>

<style scoped>
.dashboard {
  background: #f9fafb;
  min-height: 100vh;
  padding: 32px;
  color: #111827;
  font-family: 'Inter', sans-serif;
}

.dash-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.dash-header h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #111827;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.period-picker {
  display: flex;
  gap: 6px;
}
.period-picker select {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 13px;
  background: #ffffff;
  color: #111827;
}
.range-label {
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
}
.kanban-link {
  color: #6b7280;
  text-decoration: none;
  font-size: 13px;
}
.kanban-link:hover {
  color: #b45309;
}

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.hero-card {
  margin-bottom: 20px;
}
.card-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 8px;
}
.card-value {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.card-value.hero {
  font-size: 34px;
  color: #b45309;
}
.card-value.loading {
  font-size: 24px;
  color: #9ca3af;
}
.card-sub {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
@media (max-width: 900px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
}
.bar-row {
  display: grid;
  grid-template-columns: 110px 1fr 90px;
  align-items: center;
  gap: 10px;
}
.bar-label {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bar-track {
  background: #e5e7eb;
  border-radius: 6px;
  height: 10px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: #3b82f6;
  border-radius: 6px;
}
.bar-fill.gold {
  background: #b45309;
}
.bar-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
  color: #111827;
}

.velocity-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  font-size: 13px;
}
.velocity-table th {
  text-align: left;
  color: #6b7280;
  font-weight: 500;
  padding: 6px 4px;
  border-bottom: 1px solid #e5e7eb;
}
.velocity-table td {
  padding: 8px 4px;
  border-bottom: 1px solid #e5e7eb;
  color: #111827;
}
.velocity-table td.stale {
  color: #dc2626;
  font-weight: 600;
}
</style>
