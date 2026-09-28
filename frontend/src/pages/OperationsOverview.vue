<script setup>
import { computed } from 'vue'
import { createResource } from 'frappe-ui'

function useReport(name) {
  return createResource({
    url: 'frappe.desk.query_report.run',
    params: { report_name: name, filters: {} },
    auto: true,
  })
}

// Rows may come back as objects or arrays; read them by column position.
const cells = (row) => (Array.isArray(row) ? row : Object.values(row ?? {}))
const rowsOf = (res) => (res.data?.result ?? []).map(cells)

const onTime = useReport('On-time Delivery Rate')
const cycle = useReport('Average Project Cycle Time')
const active = useReport('Active Client Count')
const tenure = useReport('Average Client Tenure')
const cost = useReport('Tool and API Cost Trend')

const onTimeRow = computed(() => rowsOf(onTime)[0]) // [delivered, on_time, rate]
const cycleRow = computed(() => rowsOf(cycle)[0]) // [count, avg_days]
const activeRows = computed(() => rowsOf(active)) // [type, clients]
const activeTotal = computed(() => activeRows.value.reduce((s, r) => s + Number(r[1] || 0), 0))
const tenureRows = computed(() => rowsOf(tenure)) // [client, first, days]
const avgTenure = computed(() => {
  const r = tenureRows.value
  return r.length ? Math.round(r.reduce((s, x) => s + Number(x[2] || 0), 0) / r.length) : 0
})
const costRows = computed(() => rowsOf(cost)) // [month, total]
const maxCost = computed(() => Math.max(1, ...costRows.value.map((r) => Number(r[1]) || 0)))
const maxActive = computed(() => Math.max(1, ...activeRows.value.map((r) => Number(r[1]) || 0)))

const peso = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')
const width = (v, max) => Math.max(2, (Number(v) / max) * 100) + '%'
</script>

<template>
  <div class="dashboard">
    <header class="dash-header"><h1>Operations</h1></header>

    <div class="tiles">
      <div class="tile">
        <div class="label">ON-TIME DELIVERY</div>
        <div class="value">{{ onTime.loading ? '···' : Number(onTimeRow?.[2] ?? 0).toFixed(1) + '%' }}</div>
        <div class="sub" v-if="onTimeRow">{{ onTimeRow[1] ?? 0 }} of {{ onTimeRow[0] }} delivered projects</div>
      </div>
      <div class="tile">
        <div class="label">AVG PROJECT CYCLE TIME</div>
        <div class="value">{{ cycle.loading ? '···' : Math.round(cycleRow?.[1] ?? 0) + ' days' }}</div>
        <div class="sub" v-if="cycleRow">across {{ cycleRow[0] }} delivered projects</div>
      </div>
      <div class="tile">
        <div class="label">ACTIVE CLIENTS</div>
        <div class="value">{{ active.loading ? '···' : activeTotal }}</div>
        <div class="sub">with a project in progress</div>
      </div>
      <div class="tile">
        <div class="label">AVG CLIENT TENURE</div>
        <div class="value">{{ tenure.loading ? '···' : avgTenure + ' days' }}</div>
        <div class="sub">{{ tenureRows.length }} clients</div>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <div class="card-label">Active Clients by Project Type</div>
        <div v-if="active.loading" class="muted">···</div>
        <div v-else class="bars">
          <div v-for="r in activeRows" :key="r[0]" class="bar-row">
            <div class="bar-label">{{ r[0] }}</div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: width(r[1], maxActive) }"></div></div>
            <div class="bar-value">{{ r[1] }}</div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-label">Tool and API Cost Trend (monthly)</div>
        <div v-if="cost.loading" class="muted">···</div>
        <div v-else class="bars">
          <div v-for="r in costRows" :key="r[0]" class="bar-row">
            <div class="bar-label">{{ r[0] }}</div>
            <div class="bar-track"><div class="bar-fill gold" :style="{ width: width(r[1], maxCost) }"></div></div>
            <div class="bar-value">{{ peso(r[1]) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-label">Client Tenure</div>
      <table>
        <thead><tr><th>Client</th><th>First Contract</th><th>Tenure (days)</th></tr></thead>
        <tbody>
          <tr v-for="r in tenureRows" :key="r[0]"><td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.dashboard { background: #f9fafb; min-height: 100vh; padding: 32px; font-family: 'Inter', sans-serif; color: #111827; }
.dash-header h1 { font-size: 20px; font-weight: 600; margin: 0 0 24px; }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.tile, .card { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
.tile { padding: 16px 18px; }
.card { padding: 18px 20px; }
.label { font-size: 11px; color: #6b7280; font-weight: 600; letter-spacing: .03em; margin-bottom: 6px; }
.value { font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 700; color: #b45309; }
.sub { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card-label { font-size: 12px; color: #6b7280; font-weight: 500; margin-bottom: 8px; }
.bars { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
.bar-row { display: grid; grid-template-columns: 110px 1fr 90px; align-items: center; gap: 10px; }
.bar-label { font-size: 12px; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { background: #e5e7eb; border-radius: 6px; height: 10px; overflow: hidden; }
.bar-fill { height: 100%; background: #3b82f6; border-radius: 6px; }
.bar-fill.gold { background: #b45309; }
.bar-value { font-family: 'Space Grotesk', sans-serif; font-size: 12px; font-weight: 600; text-align: right; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; color: #6b7280; font-weight: 500; padding: 6px 4px; border-bottom: 1px solid #e5e7eb; }
td { padding: 8px 4px; border-bottom: 1px solid #e5e7eb; }
.muted { color: #9ca3af; }
@media (max-width: 900px) { .tiles { grid-template-columns: 1fr 1fr; } .row { grid-template-columns: 1fr; } }
</style>
