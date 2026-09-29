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

const cells = (row) => (Array.isArray(row) ? row : Object.values(row ?? {}))
const rowsOf = (res) => (res.data?.result ?? []).map(cells)

const revenue = useReport('Revenue per Client')
const aging = useReport('Accounts Receivable Aging')
const burn = useReport('Net Burn Rate')

const revenueRows = computed(() => rowsOf(revenue)) // [client, total, count]
const totalRevenue = computed(() => revenueRows.value.reduce((s, r) => s + Number(r[1] || 0), 0))
const maxRevenue = computed(() => Math.max(1, ...revenueRows.value.map((r) => Number(r[1]) || 0)))

const agingRows = computed(() => rowsOf(aging)) // [invoice, client, amount, due_date, status, days_overdue]
const totalOutstanding = computed(() => agingRows.value.reduce((s, r) => s + Number(r[2] || 0), 0))

const burnRows = computed(() => rowsOf(burn)) // [month, revenue, expenses, net_burn]
const latestBurn = computed(() => burnRows.value[burnRows.value.length - 1])
const maxBurnAbs = computed(() =>
  Math.max(1, ...burnRows.value.flatMap((r) => [Math.abs(Number(r[1]) || 0), Math.abs(Number(r[2]) || 0)]))
)

const peso = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')
const width = (v, max) => Math.max(2, (Number(v) / max) * 100) + '%'
</script>

<template>
  <div class="dashboard">
    <header class="dash-header"><h1>Finance</h1></header>

    <div class="tiles">
      <div class="tile">
        <div class="label">TOTAL PAID REVENUE</div>
        <div class="value">{{ revenue.loading ? '···' : peso(totalRevenue) }}</div>
        <div class="sub">{{ revenueRows.length }} clients</div>
      </div>
      <div class="tile">
        <div class="label">OUTSTANDING (A/R)</div>
        <div class="value">{{ aging.loading ? '···' : peso(totalOutstanding) }}</div>
        <div class="sub">{{ agingRows.length }} unpaid invoices</div>
      </div>
      <div class="tile">
        <div class="label">LATEST NET BURN</div>
        <div class="value" :class="{ neg: Number(latestBurn?.[3]) < 0 }">
          {{ burn.loading ? '···' : peso(latestBurn?.[3] ?? 0) }}
        </div>
        <div class="sub" v-if="latestBurn">{{ latestBurn[0] }} · expenses minus revenue</div>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <div class="card-label">Revenue per Client</div>
        <div v-if="revenue.loading" class="muted">···</div>
        <div v-else class="bars">
          <div v-for="r in revenueRows" :key="r[0]" class="bar-row">
            <div class="bar-label">{{ r[0] }}</div>
            <div class="bar-track"><div class="bar-fill" :style="{ width: width(r[1], maxRevenue) }"></div></div>
            <div class="bar-value">{{ peso(r[1]) }}</div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-label">Net Burn Rate by Month</div>
        <div v-if="burn.loading" class="muted">···</div>
        <div v-else class="bars">
          <div v-for="r in burnRows" :key="r[0]" class="bar-row">
            <div class="bar-label">{{ r[0] }}</div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :class="{ gold: Number(r[3]) >= 0 }"
                :style="{ width: width(Math.abs(r[3]), maxBurnAbs) }"
              ></div>
            </div>
            <div class="bar-value" :class="{ neg: Number(r[3]) < 0 }">{{ peso(r[3]) }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-label">Accounts Receivable Aging</div>
      <div v-if="aging.loading" class="muted">···</div>
      <table v-else>
        <thead><tr><th>Invoice</th><th>Client</th><th>Amount</th><th>Due Date</th><th>Status</th><th>Days Overdue</th></tr></thead>
        <tbody>
          <tr v-for="r in agingRows" :key="r[0]">
            <td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ peso(r[2]) }}</td>
            <td>{{ r[3] }}</td><td>{{ r[4] }}</td>
            <td :class="{ stale: Number(r[5]) > 0 }">{{ r[5] }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.dashboard { background: #f9fafb; min-height: 100vh; padding: 32px; font-family: 'Inter', sans-serif; color: #111827; }
.dash-header h1 { font-size: 20px; font-weight: 600; margin: 0 0 24px; }
.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.tile, .card { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
.tile { padding: 16px 18px; }
.card { padding: 18px 20px; }
.label { font-size: 11px; color: #6b7280; font-weight: 600; letter-spacing: .03em; margin-bottom: 6px; }
.value { font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 700; color: #b45309; }
.value.neg { color: #16a34a; }
.sub { font-size: 12px; color: #9ca3af; margin-top: 4px; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.card-label { font-size: 12px; color: #6b7280; font-weight: 500; margin-bottom: 8px; }
.bars { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
.bar-row { display: grid; grid-template-columns: 130px 1fr 100px; align-items: center; gap: 10px; }
.bar-label { font-size: 12px; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { background: #e5e7eb; border-radius: 6px; height: 10px; overflow: hidden; }
.bar-fill { height: 100%; background: #3b82f6; border-radius: 6px; }
.bar-fill.gold { background: #b45309; }
.bar-value { font-family: 'Space Grotesk', sans-serif; font-size: 12px; font-weight: 600; text-align: right; }
.bar-value.neg { color: #16a34a; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; color: #6b7280; font-weight: 500; padding: 6px 4px; border-bottom: 1px solid #e5e7eb; }
td { padding: 8px 4px; border-bottom: 1px solid #e5e7eb; }
td.stale { color: #dc2626; font-weight: 600; }
.muted { color: #9ca3af; }
@media (max-width: 900px) { .tiles { grid-template-columns: 1fr; } .row { grid-template-columns: 1fr; } }
</style>
