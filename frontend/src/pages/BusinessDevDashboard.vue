<template>
  <div class="dashboard">
    <header class="dash-header">
      <h1>Business Development</h1>
      <RouterLink to="/business-dev/pipeline" class="kanban-link">View Pipeline →</RouterLink>
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
import { computed } from 'vue'
import { createResource } from 'frappe-ui'

function useReport(reportName) {
  return createResource({
    url: 'frappe.desk.query_report.run',
    params: { report_name: reportName },
    auto: true,
  })
}

const conversionRate = useReport('Pipeline Conversion Rate')
const stageTime = useReport('Average Time Per Pipeline Stage')
const productType = useReport('Product Type Performance')
const geo = useReport('Geographic Distribution of Clients')
const velocity = useReport('Client Pipeline Velocity')

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
  background: radial-gradient(1200px 600px at 10% -10%, #101b33 0%, #0a0f1d 55%);
  min-height: 100vh;
  padding: 32px;
  color: #edeff5;
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
}
.kanban-link {
  color: #7c87a3;
  text-decoration: none;
  font-size: 13px;
}
.kanban-link:hover {
  color: #c9a227;
}

.card {
  background: #101728;
  border: 1px solid #1a2338;
  border-radius: 14px;
  padding: 18px 20px;
}

.hero-card {
  margin-bottom: 20px;
}
.card-label {
  font-size: 12px;
  color: #7c87a3;
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
  color: #c9a227;
}
.card-value.loading {
  font-size: 24px;
  color: #4e5876;
}
.card-sub {
  font-size: 13px;
  color: #7c87a3;
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
  color: #7c87a3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bar-track {
  background: #1a2338;
  border-radius: 6px;
  height: 10px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: #4c8dff;
  border-radius: 6px;
}
.bar-fill.gold {
  background: #c9a227;
}
.bar-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.velocity-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  font-size: 13px;
}
.velocity-table th {
  text-align: left;
  color: #7c87a3;
  font-weight: 500;
  padding: 6px 4px;
  border-bottom: 1px solid #1a2338;
}
.velocity-table td {
  padding: 8px 4px;
  border-bottom: 1px solid #1a2338;
}
.velocity-table td.stale {
  color: #e5636b;
  font-weight: 600;
}
</style>
