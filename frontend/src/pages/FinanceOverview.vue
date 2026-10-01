<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { yearRange } from '../utils/dateRange'
import { quarterRange } from '../utils/dateRange'

const initialRange = yearRange()
const fromInput = ref(initialRange.from)
const toInput = ref(initialRange.to)
const range = () => ({ from_date: fromInput.value, to_date: toInput.value })
function setRange(r) {
  fromInput.value = r.from
  toInput.value = r.to
}

function useReport(name, filters = {}) {
  return createResource({
    url: 'frappe.desk.query_report.run',
    params: { report_name: name, filters },
    auto: true,
  })
}

const cells = (row) => (Array.isArray(row) ? row : Object.values(row ?? {}))
const rowsOf = (res) => (res.data?.result ?? []).map(cells)

const revenue = useReport('Revenue per Client', range())
const aging = useReport('Accounts Receivable Aging')
const burn = useReport('Net Burn Rate', range())
const profit = useReport('Project Profitability', range())
const expenseRep = useReport('Expense by Category', range())

const projectsRes = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Project', fields: ['name', 'contract'], limit_page_length: 500 },
  auto: true,
})
const drill = ref(null)
const drillRes = createResource({ url: 'frappe.client.get_list', auto: false })
const drillRows = computed(() =>
  (drillRes.data || []).map((d) =>
    drill.value?.kind === 'expense'
      ? { id: d.name, label: d.category + (d.project ? ' · ' + d.project : ''), date: d.expense_date, amount: d.amount, href: '/app/expense/' + d.name }
      : { id: d.name, label: d.client, date: d.issue_date, amount: d.amount, href: '/app/invoice/' + d.name }
  )
)
const drillTotal = computed(() => drillRows.value.reduce((t, r) => t + Number(r.amount || 0), 0))
function openDrill(kind, r) {
  const all = r[0] === 'COMPANY TOTAL'
  const { from_date, to_date } = range()
  let params
  if (kind === 'expense') {
    const filters = { expense_date: ['between', [from_date, to_date]] }
    if (!all) filters.project = r[0]
    params = { doctype: 'Expense', fields: ['name', 'category', 'amount', 'expense_date', 'project'], filters, order_by: 'expense_date desc', limit_page_length: 200 }
  } else {
    const filters = { status: 'Paid', issue_date: ['between', [from_date, to_date]] }
    if (!all) filters.contract = (projectsRes.data || []).find((p) => p.name === r[0])?.contract || '__none__'
    params = { doctype: 'Invoice', fields: ['name', 'client', 'amount', 'issue_date'], filters, order_by: 'issue_date desc', limit_page_length: 200 }
  }
  drill.value = { kind, title: all ? 'All projects' : r[0] }
  drillRes.update({ params })
  drillRes.reload()
}

watch([fromInput, toInput], () => {
  if (!fromInput.value || !toInput.value || fromInput.value > toInput.value) return
  for (const [res, name] of [[revenue, 'Revenue per Client'], [burn, 'Net Burn Rate'], [profit, 'Project Profitability'], [expenseRep, 'Expense by Category']]) {
    res.update({ params: { report_name: name, filters: range() } })
    res.reload()
  }
})

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

const profitRows = computed(() => rowsOf(profit)) // [project, client, revenue, expenses, net, margin]
const isOverhead = (r) => r[0] === 'Unassigned / Overhead'
const isTotal = (r) => r[0] === 'COMPANY TOTAL'
const margin = (r) => {
  const rev = Number(r[2]) || 0
  if (isOverhead(r) || rev <= 0) return '—'
  return ((Number(r[4]) / rev) * 100).toFixed(1) + '%'
}

// ---------- A/R aging buckets ----------
const BUCKETS = [
  { key: 'current', label: 'Current', color: '#10b981', test: (d) => d <= 0 },
  { key: 'b1', label: '1-30 days', color: '#f59e0b', test: (d) => d >= 1 && d <= 30 },
  { key: 'b2', label: '31-60 days', color: '#f97316', test: (d) => d >= 31 && d <= 60 },
  { key: 'b3', label: '61-90 days', color: '#ef4444', test: (d) => d >= 61 && d <= 90 },
  { key: 'b4', label: '90+ days', color: '#991b1b', test: (d) => d > 90 },
]
const agingBuckets = computed(() =>
  BUCKETS.map((b) => {
    const rows = agingRows.value.filter((r) => b.test(Number(r[5]) || 0))
    return { ...b, rows, total: rows.reduce((t, r) => t + Number(r[2] || 0), 0) }
  })
)
function donutSegments(items, r = 40) {
  const C = 2 * Math.PI * r
  const sum = items.reduce((t, i) => t + i.total, 0) || 1
  let used = 0
  return items.map((i) => {
    const len = (i.total / sum) * C
    const seg = { ...i, dash: len + ' ' + (C - len), offset: -used }
    used += len
    return seg
  })
}
const agingDonut = computed(() => donutSegments(agingBuckets.value.filter((b) => b.total > 0)))
const dueLabel = (d) => {
  d = Number(d) || 0
  if (d > 0) return d + (d === 1 ? ' day overdue' : ' days overdue')
  if (d === 0) return 'Due today'
  return 'Due in ' + (-d) + (d === -1 ? ' day' : ' days')
}

// ---------- Expense by category ----------
const expenseRows = computed(() => rowsOf(expenseRep)) // [category, vendor, amount]
const PALETTE = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#a855f7', '#84cc16', '#f97316']
const expenseGroups = computed(() => {
  const m = new Map()
  for (const r of expenseRows.value) {
    const k = r[0] || 'Uncategorized'
    if (!m.has(k)) m.set(k, { key: k, label: k, rows: [], total: 0 })
    const g = m.get(k)
    g.rows.push(r)
    g.total += Number(r[2] || 0)
  }
  return [...m.values()].sort((a, b) => b.total - a.total).map((g, i) => ({ ...g, color: PALETTE[i % PALETTE.length] }))
})
const totalExpenses = computed(() => expenseGroups.value.reduce((t, g) => t + g.total, 0))
const expenseDonut = computed(() => donutSegments(expenseGroups.value.filter((g) => g.total > 0)))

// ---------- Profit tile ----------
const companyTotal = computed(() => profitRows.value.find(isTotal))
const profitNet = computed(() => Number(companyTotal.value?.[4] || 0))
const profitMargin = computed(() => (companyTotal.value ? margin(companyTotal.value) : '—'))

// ---------- Net Burn note ----------
const burnSyncedAt = ref(null)
watch(() => burn.data, (d) => { if (d) burnSyncedAt.value = new Date() })
const burnNote = computed(() => {
  const rows = burnRows.value
  if (!rows.length) return ''
  const when = burnSyncedAt.value ? burnSyncedAt.value.toLocaleString('en-PH') : '—'
  return 'Net burn = expenses minus revenue per month. Covers ' + rows.length + ' month(s), ' + rows[0][0] + ' to ' + rows[rows.length - 1][0] + '. Last synced ' + when + '.'
})

const peso = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')
const width = (v, max) => Math.max(2, (Number(v) / max) * 100) + '%'
</script>

<template>
  <div class="dashboard">
    <header class="dash-header">
      <h1>Finance</h1>
      <div class="period-picker">
        <input type="date" v-model="fromInput" :max="toInput" />
        <span class="to">to</span>
        <input type="date" v-model="toInput" :min="fromInput" />
        <button type="button" @click="setRange(quarterRange(0))">This quarter</button>
        <button type="button" @click="setRange(quarterRange(-1))">Last quarter</button>
        <button type="button" @click="setRange(yearRange())">This year</button>
      </div>
    </header>

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
      <div class="tile">
        <div class="label">NET PROFIT</div>
        <div class="value" :class="{ neg: profitNet < 0 }">{{ profit.loading ? '···' : peso(profitNet) }}</div>
        <div class="sub">{{ profitMargin }} margin</div>
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
        <div class="muted note">{{ burnNote }}</div>
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

    <div class="card profit-card">
      <div class="card-label">Project Profitability (paid revenue minus expenses)</div>
      <div v-if="profit.loading" class="muted">···</div>
      <table v-else>
        <thead><tr><th>Project</th><th>Client</th><th>Revenue</th><th>Expenses</th><th>Net</th><th>Margin</th></tr></thead>
        <tbody>
          <tr v-for="r in profitRows" :key="r[0]" :class="{ overhead: isOverhead(r), total: isTotal(r) }">
            <td>{{ r[0] }}</td><td>{{ r[1] || '' }}</td>
            <td class="link" @click="openDrill('revenue', r)">{{ peso(r[2]) }}</td><td class="link" @click="openDrill('expense', r)">{{ peso(r[3]) }}</td>
            <td :class="{ loss: Number(r[4]) < 0 }">{{ peso(r[4]) }}</td>
            <td>{{ margin(r) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="muted note">Expenses shown are project costs only (subscriptions, hardware, contractors, labor).</div>

    <div v-if="drill" class="drill-overlay" @click.self="drill = null">
      <div class="drill-box">
        <div class="drill-head">
          <strong>{{ drill.kind === 'expense' ? 'Expenses' : 'Paid invoices' }} · {{ drill.title }}</strong>
          <button type="button" @click="drill = null">×</button>
        </div>
        <div v-if="drillRes.loading" class="muted">···</div>
        <div v-else-if="!drillRows.length" class="muted">No records in this date range.</div>
        <table v-else>
          <thead><tr><th>ID</th><th>Details</th><th>Date</th><th>Amount</th></tr></thead>
          <tbody>
            <tr v-for="d in drillRows" :key="d.id">
              <td><a :href="d.href" target="_blank">{{ d.id }}</a></td>
              <td>{{ d.label }}</td><td>{{ d.date }}</td><td>{{ peso(d.amount) }}</td>
            </tr>
            <tr class="drill-total"><td colspan="3">Total</td><td>{{ peso(drillTotal) }}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    </div>

    <div class="card">
      <div class="card-label">Accounts Receivable Aging</div>
      <div v-if="aging.loading" class="muted">···</div>
      <template v-else>
        <div class="aging-top">
          <svg viewBox="0 0 100 100" class="donut">
            <circle v-for="s in agingDonut" :key="s.key" cx="50" cy="50" r="40" fill="none"
                    stroke-width="14" :stroke="s.color"
                    :stroke-dasharray="s.dash" :stroke-dashoffset="s.offset" />
          </svg>
          <table class="bucket-table">
            <tbody>
              <tr v-for="b in agingBuckets" :key="b.key">
                <td><span class="dot" :style="{ background: b.color }"></span>{{ b.label }}</td>
                <td>{{ b.rows.length }} inv.</td>
                <td>{{ peso(b.total) }}</td>
              </tr>
              <tr class="total"><td>Total</td><td>{{ agingRows.length }}</td><td>{{ peso(totalOutstanding) }}</td></tr>
            </tbody>
          </table>
        </div>
        <table v-for="b in agingBuckets.filter((x) => x.rows.length)" :key="b.key">
          <thead>
            <tr><th colspan="5" :style="{ color: b.color }">{{ b.label }} · {{ peso(b.total) }}</th></tr>
            <tr><th>Invoice</th><th>Client</th><th>Amount</th><th>Due Date</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in b.rows" :key="r[0]">
              <td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ peso(r[2]) }}</td>
              <td>{{ r[3] }}</td>
              <td :class="{ stale: Number(r[5]) > 0 }">{{ dueLabel(r[5]) }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>

    <div class="card">
      <div class="card-label">Expenses by Category</div>
      <div v-if="expenseRep.loading" class="muted">···</div>
      <div v-else-if="!expenseGroups.length" class="muted">No expenses in this date range.</div>
      <template v-else>
        <div class="aging-top">
          <svg viewBox="0 0 100 100" class="donut">
            <circle v-for="s in expenseDonut" :key="s.key" cx="50" cy="50" r="40" fill="none"
                    stroke-width="14" :stroke="s.color"
                    :stroke-dasharray="s.dash" :stroke-dashoffset="s.offset" />
          </svg>
          <table class="bucket-table">
            <tbody>
              <tr v-for="g in expenseGroups" :key="g.key">
                <td><span class="dot" :style="{ background: g.color }"></span>{{ g.label }}</td>
                <td>{{ peso(g.total) }}</td>
              </tr>
              <tr class="total"><td>Total</td><td>{{ peso(totalExpenses) }}</td></tr>
            </tbody>
          </table>
        </div>
        <table v-for="g in expenseGroups" :key="g.key">
          <thead>
            <tr><th colspan="2" :style="{ color: g.color }">{{ g.label }} · {{ peso(g.total) }}</th></tr>
            <tr><th>Vendor</th><th>Amount</th></tr>
          </thead>
          <tbody>
            <tr v-for="r in g.rows" :key="r[1]"><td>{{ r[1] }}</td><td>{{ peso(r[2]) }}</td></tr>
            <tr class="total"><td>Subtotal</td><td>{{ peso(g.total) }}</td></tr>
          </tbody>
        </table>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard { background: #f9fafb; min-height: 100vh; padding: 32px; font-family: 'Inter', sans-serif; color: #111827; }
.dash-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.dash-header h1 { font-size: 20px; font-weight: 600; margin: 0; }
.period-picker { display: flex; gap: 8px; align-items: center; }
.period-picker input { border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px 8px; font-size: 13px; background: #fff; }
.period-picker button { border: 1px solid #e5e7eb; background: #fff; border-radius: 6px; padding: 6px 10px; font-size: 13px; cursor: pointer; }
.period-picker button:hover { background: #f3f4f6; }
.period-picker .to { font-size: 12px; color: #9ca3af; }
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
.profit-card { margin-bottom: 16px; }
tr.overhead td { color: #6b7280; font-style: italic; }
tr.total td { font-weight: 700; border-top: 2px solid #111827; border-bottom: none; }
td.loss { color: #dc2626; font-weight: 600; }
.note { font-size: 12px; margin-top: 8px; }
.muted { color: #9ca3af; }
td.link { cursor: pointer; text-decoration: underline dotted; text-underline-offset: 3px; }
td.link:hover { color: #b45309; }
.drill-overlay { position: fixed; inset: 0; background: rgba(17,24,39,.45); display: flex; align-items: center; justify-content: center; z-index: 50; }
.drill-box { background: #fff; border-radius: 14px; padding: 18px 20px; width: min(560px, 92vw); max-height: 80vh; overflow: auto; }
.drill-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.drill-head button { border: none; background: none; font-size: 20px; cursor: pointer; }
.drill-box a { color: #b45309; text-decoration: none; }
tr.drill-total td { font-weight: 700; border-top: 2px solid #111827; border-bottom: none; }
@media (max-width: 900px) { .tiles { grid-template-columns: 1fr; } .row { grid-template-columns: 1fr; } }
.aging-top { display: flex; gap: 24px; align-items: center; margin-bottom: 16px; }
.donut { width: 160px; height: 160px; transform: rotate(-90deg); flex: none; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
.bucket-table td { padding: 4px 12px 4px 0; }
/* tiles-fix */
.tiles { grid-template-columns: repeat(4, 1fr) !important; }
.bucket-table { width: auto !important; min-width: 360px; }
/* cols-fix */
.card table:not(.bucket-table) { table-layout: fixed; width: 100%; }
</style>
