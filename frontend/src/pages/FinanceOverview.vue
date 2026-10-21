<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import { yearRange } from '../utils/dateRange'
import { quarterRange } from '../utils/dateRange'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import XIcon from '~icons/lucide/x'

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

const errText = (res) => res.error?.messages?.[0] || res.error?.message || ''

const peso = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')
const width = (v, max) => Math.max(2, (Number(v) / max) * 100) + '%'
</script>

<template>
  <div class="dashboard">
    <PageHeader title="Finance">
      <template #actions>
        <div class="period-picker">
          <input type="date" v-model="fromInput" :max="toInput" aria-label="From date" />
          <span class="to">to</span>
          <input type="date" v-model="toInput" :min="fromInput" aria-label="To date" />
          <button type="button" @click="setRange(quarterRange(0))">This quarter</button>
          <button type="button" @click="setRange(quarterRange(-1))">Last quarter</button>
          <button type="button" @click="setRange(yearRange())">This year</button>
        </div>
      </template>
    </PageHeader>

    <div class="tiles">
      <div class="tile">
        <template v-if="revenue.loading && !revenue.data">
          <div class="label">TOTAL PAID REVENUE</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="revenue.error && !revenue.data">
          <div class="label">TOTAL PAID REVENUE</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="revenue.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">TOTAL PAID REVENUE</div>
          <div class="value">{{ peso(totalRevenue) }}</div>
          <div class="sub">{{ revenueRows.length }} clients</div>
        </template>
      </div>
      <div class="tile">
        <template v-if="aging.loading && !aging.data">
          <div class="label">OUTSTANDING (A/R)</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="aging.error && !aging.data">
          <div class="label">OUTSTANDING (A/R)</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="aging.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">OUTSTANDING (A/R)</div>
          <div class="value">{{ peso(totalOutstanding) }}</div>
          <div class="sub">{{ agingRows.length }} unpaid invoices</div>
        </template>
      </div>
      <div class="tile">
        <template v-if="burn.loading && !burn.data">
          <div class="label">LATEST NET BURN</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="burn.error && !burn.data">
          <div class="label">LATEST NET BURN</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="burn.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">LATEST NET BURN</div>
          <div class="value" :class="{ neg: Number(latestBurn?.[3]) < 0 }">
            {{ peso(latestBurn?.[3] ?? 0) }}
          </div>
          <div class="sub" v-if="latestBurn">{{ latestBurn[0] }} · expenses minus revenue</div>
          <div class="sub" v-else>No data in this range</div>
        </template>
      </div>
      <div class="tile">
        <template v-if="profit.loading && !profit.data">
          <div class="label">NET PROFIT</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="profit.error && !profit.data">
          <div class="label">NET PROFIT</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="profit.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">NET PROFIT</div>
          <div class="value" :class="{ loss: profitNet < 0 }">{{ peso(profitNet) }}</div>
          <div class="sub">{{ profitMargin }} margin</div>
        </template>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <div class="card-label">Revenue per Client</div>
        <ErrorState v-if="revenue.error" title="Couldn't load this chart" :message="errText(revenue)" :on-retry="() => revenue.reload()" />
        <AppSkeleton v-else-if="revenue.loading" variant="chart" :rows="4" />
        <EmptyState v-else-if="!revenueRows.length" title="No paid revenue" description="No paid invoices for this date range." />
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
        <div v-if="burnNote" class="muted note">{{ burnNote }}</div>
        <ErrorState v-if="burn.error" title="Couldn't load this chart" :message="errText(burn)" :on-retry="() => burn.reload()" />
        <AppSkeleton v-else-if="burn.loading" variant="chart" :rows="4" />
        <EmptyState v-else-if="!burnRows.length" title="No monthly data" description="No net burn data for this date range." />
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
      <ErrorState v-if="profit.error" title="Couldn't load this table" :message="errText(profit)" :on-retry="() => profit.reload()" />
      <AppSkeleton v-else-if="profit.loading" variant="table" :rows="4" :cols="6" />
      <EmptyState v-else-if="!profitRows.length" title="No projects in this range" description="Project profitability appears once invoices are paid." />
      <template v-else>
        <div class="table-scroll">
          <table>
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
        </div>
        <div class="muted note">Expenses shown are project costs only (subscriptions, hardware, contractors, labor).</div>
      </template>

      <div v-if="drill" class="drill-overlay" @click.self="drill = null">
        <div class="drill-box" role="dialog" :aria-label="drill.kind === 'expense' ? 'Expenses' : 'Paid invoices'">
          <div class="drill-head">
            <strong>{{ drill.kind === 'expense' ? 'Expenses' : 'Paid invoices' }} · {{ drill.title }}</strong>
            <button type="button" class="drill-close" aria-label="Close" @click="drill = null">
              <XIcon aria-hidden="true" />
            </button>
          </div>
          <AppSkeleton v-if="drillRes.loading" variant="table" :rows="4" :cols="4" />
          <EmptyState v-else-if="!drillRows.length" title="No records in this date range" />
          <div v-else class="table-scroll">
            <table>
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
    </div>

    <div class="card">
      <div class="card-label">Accounts Receivable Aging</div>
      <ErrorState v-if="aging.error" title="Couldn't load aging" :message="errText(aging)" :on-retry="() => aging.reload()" />
      <AppSkeleton v-else-if="aging.loading" variant="table" :rows="4" :cols="5" />
      <EmptyState v-else-if="!agingRows.length" title="Nothing outstanding" description="No unpaid invoices in this date range." />
      <template v-else>
        <div class="aging-top">
          <svg viewBox="0 0 100 100" class="donut" aria-hidden="true">
            <circle v-for="s in agingDonut" :key="s.key" cx="50" cy="50" r="40" fill="none"
                    stroke-width="14" :stroke="s.color"
                    :stroke-dasharray="s.dash" :stroke-dashoffset="s.offset" />
          </svg>
          <div class="table-scroll">
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
        </div>
        <div class="table-scroll" v-for="b in agingBuckets.filter((x) => x.rows.length)" :key="b.key">
          <table>
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
        </div>
      </template>
    </div>

    <div class="card">
      <div class="card-label">Expenses by Category</div>
      <ErrorState v-if="expenseRep.error" title="Couldn't load expenses" :message="errText(expenseRep)" :on-retry="() => expenseRep.reload()" />
      <AppSkeleton v-else-if="expenseRep.loading" variant="table" :rows="4" :cols="2" />
      <EmptyState v-else-if="!expenseGroups.length" title="No expenses in this date range" />
      <template v-else>
        <div class="aging-top">
          <svg viewBox="0 0 100 100" class="donut" aria-hidden="true">
            <circle v-for="s in expenseDonut" :key="s.key" cx="50" cy="50" r="40" fill="none"
                    stroke-width="14" :stroke="s.color"
                    :stroke-dasharray="s.dash" :stroke-dashoffset="s.offset" />
          </svg>
          <div class="table-scroll">
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
        </div>
        <div class="table-scroll" v-for="g in expenseGroups" :key="g.key">
          <table>
            <thead>
              <tr><th colspan="2" :style="{ color: g.color }">{{ g.label }} · {{ peso(g.total) }}</th></tr>
              <tr><th>Vendor</th><th>Amount</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in g.rows" :key="r[1]"><td>{{ r[1] }}</td><td>{{ peso(r[2]) }}</td></tr>
              <tr class="total"><td>Subtotal</td><td>{{ peso(g.total) }}</td></tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard { background: var(--color-gray-50); min-height: 100vh; padding: var(--page-pad); color: var(--color-gray-900); }
.period-picker { display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
.period-picker input { border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm); padding: 6px var(--space-2); font-size: var(--fs-sm); background: var(--color-white); color: var(--color-gray-900); font-family: inherit; }
.period-picker button { border: 1px solid var(--color-gray-200); background: var(--color-white); border-radius: var(--radius-sm); padding: 6px 10px; font-size: var(--fs-sm); cursor: pointer; font-family: inherit; color: var(--color-gray-900); }
.period-picker button:hover { background: var(--color-gray-100); }
.period-picker .to { font-size: var(--fs-xs); color: var(--color-gray-600); }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); margin-bottom: var(--space-5); }
.tile, .card { background: var(--color-white); border: 1px solid var(--color-gray-200); border-radius: var(--radius-lg); box-shadow: var(--shadow-xs); }
.tile { padding: var(--space-4) var(--space-5); }
.card { padding: var(--space-5); }
.label { font-size: var(--fs-xs); color: var(--color-gray-600); font-weight: 600; letter-spacing: .03em; margin-bottom: var(--space-2); }
.value { font-size: var(--fs-xl); font-weight: 700; color: var(--color-gray-900); font-variant-numeric: tabular-nums; }
.value.neg { color: var(--color-green-600); }
.value.loss { color: var(--color-red-600); }
.sub { font-size: var(--fs-xs); color: var(--color-gray-600); margin-top: var(--space-1); }
.sub--error { color: var(--color-red-600); }
.retry-link {
  background: none; border: none; padding: 0; color: var(--color-amber-700);
  font-weight: 600; font-size: var(--fs-xs); cursor: pointer; text-decoration: underline; font-family: inherit;
}
.row { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); margin-bottom: var(--space-4); }
.row .card { min-height: 200px; }
.card-label { font-size: var(--fs-xs); color: var(--color-gray-600); font-weight: 500; margin-bottom: var(--space-2); }
.bars { display: flex; flex-direction: column; gap: var(--space-3); margin-top: var(--space-3); }
.bar-row { display: grid; grid-template-columns: 130px 1fr 100px; align-items: center; gap: var(--space-3); }
.bar-label { font-size: var(--fs-xs); color: var(--color-gray-600); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { background: var(--color-gray-200); border-radius: var(--radius-sm); height: 10px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--color-blue-500); border-radius: var(--radius-sm); }
.bar-fill.gold { background: var(--color-amber-700); }
.bar-value { font-size: var(--fs-xs); font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; color: var(--color-gray-900); }
.bar-value.neg { color: var(--color-green-600); }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); table-layout: fixed; }
th { text-align: left; color: var(--color-gray-600); font-weight: 500; padding: var(--space-2) var(--space-1); border-bottom: 1px solid var(--color-gray-200); }
td { padding: var(--space-2) var(--space-1); border-bottom: 1px solid var(--color-gray-200); overflow-wrap: break-word; }
td.stale { color: var(--color-red-600); font-weight: 600; }
.profit-card { margin-bottom: var(--space-4); }
tr.overhead td { color: var(--color-gray-600); font-style: italic; }
tr.total td { font-weight: 700; border-top: 2px solid var(--color-gray-900); border-bottom: none; }
td.loss { color: var(--color-red-600); font-weight: 600; }
.note { font-size: var(--fs-xs); margin-top: var(--space-2); color: var(--color-gray-600); }
.muted { color: var(--color-gray-600); }
td.link { cursor: pointer; text-decoration: underline dotted; text-underline-offset: 3px; }
td.link:hover { color: var(--color-amber-700); }
.drill-overlay { position: fixed; inset: 0; background: rgba(17,24,39,.45); display: flex; align-items: center; justify-content: center; z-index: 50; }
.drill-box { background: var(--color-white); border-radius: var(--radius-lg); padding: var(--space-5); width: min(560px, 92vw); max-height: 80vh; overflow: auto; box-shadow: var(--shadow-md); }
.drill-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-3); gap: var(--space-3); }
.drill-close {
  display: inline-flex; align-items: center; justify-content: center;
  border: none; background: none; cursor: pointer; color: var(--color-gray-500);
  padding: var(--space-1); border-radius: var(--radius-sm);
}
.drill-close svg { width: 18px; height: 18px; }
.drill-close:hover { background: var(--color-gray-100); color: var(--color-gray-900); }
.drill-box a { color: var(--color-amber-700); text-decoration: none; }
.drill-box a:hover { text-decoration: underline; }
tr.drill-total td { font-weight: 700; border-top: 2px solid var(--color-gray-900); border-bottom: none; }
.aging-top { display: flex; gap: var(--space-6); align-items: center; margin-bottom: var(--space-4); flex-wrap: wrap; }
.donut { width: 160px; height: 160px; transform: rotate(-90deg); flex: none; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: var(--space-2); }
.bucket-table { width: auto; min-width: 300px; }
.bucket-table td { padding: var(--space-1) var(--space-3) var(--space-1) 0; }
@media (max-width: 900px) {
  .tiles { grid-template-columns: repeat(2, 1fr); }
  .row { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .tiles { grid-template-columns: 1fr; }
  .bar-row { grid-template-columns: 90px 1fr 84px; gap: var(--space-2); }
}
</style>
