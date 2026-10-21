<script setup>
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'

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

const errText = (res) => String(res.error?.messages?.[0] || res.error?.message || 'Something went wrong').replace(/<[^>]+>/g, '')
const peso = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')
const width = (v, max) => Math.max(2, (Number(v) / max) * 100) + '%'
</script>

<template>
  <div class="dashboard">
    <PageHeader title="Operations" />

    <div class="tiles">
      <div class="tile">
        <template v-if="onTime.loading && !onTime.data">
          <div class="label">ON-TIME DELIVERY</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="onTime.error && !onTime.data">
          <div class="label">ON-TIME DELIVERY</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="onTime.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">ON-TIME DELIVERY</div>
          <div class="value">{{ Number(onTimeRow?.[2] ?? 0).toFixed(1) }}%</div>
          <div class="sub" v-if="onTimeRow">{{ onTimeRow[1] ?? 0 }} of {{ onTimeRow[0] }} delivered projects</div>
          <div class="sub" v-else>No delivered projects yet</div>
        </template>
      </div>
      <div class="tile">
        <template v-if="cycle.loading && !cycle.data">
          <div class="label">AVG PROJECT CYCLE TIME</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="cycle.error && !cycle.data">
          <div class="label">AVG PROJECT CYCLE TIME</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="cycle.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">AVG PROJECT CYCLE TIME</div>
          <div class="value">{{ Math.round(cycleRow?.[1] ?? 0) }} days</div>
          <div class="sub" v-if="cycleRow">across {{ cycleRow[0] }} delivered projects</div>
          <div class="sub" v-else>No delivered projects yet</div>
        </template>
      </div>
      <div class="tile">
        <template v-if="active.loading && !active.data">
          <div class="label">ACTIVE CLIENTS</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="active.error && !active.data">
          <div class="label">ACTIVE CLIENTS</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="active.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">ACTIVE CLIENTS</div>
          <div class="value">{{ activeTotal }}</div>
          <div class="sub">with a project in progress</div>
        </template>
      </div>
      <div class="tile">
        <template v-if="tenure.loading && !tenure.data">
          <div class="label">AVG CLIENT TENURE</div>
          <AppSkeleton variant="text" :rows="2" />
        </template>
        <template v-else-if="tenure.error && !tenure.data">
          <div class="label">AVG CLIENT TENURE</div>
          <div class="value">—</div>
          <div class="sub sub--error">
            Couldn't load.
            <button type="button" class="retry-link" @click="tenure.reload()">Retry</button>
          </div>
        </template>
        <template v-else>
          <div class="label">AVG CLIENT TENURE</div>
          <div class="value">{{ avgTenure }} days</div>
          <div class="sub">{{ tenureRows.length }} clients</div>
        </template>
      </div>
    </div>

    <div class="row">
      <div class="card">
        <div class="card-label">Active Clients by Project Type</div>
        <ErrorState v-if="active.error" title="Couldn't load this chart" :message="errText(active)" :on-retry="() => active.reload()" />
        <AppSkeleton v-else-if="active.loading" variant="chart" :rows="4" />
        <EmptyState v-else-if="!activeRows.length" title="No active projects" description="Clients with a project in progress will show up here." />
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
        <ErrorState v-if="cost.error" title="Couldn't load this chart" :message="errText(cost)" :on-retry="() => cost.reload()" />
        <AppSkeleton v-else-if="cost.loading" variant="chart" :rows="4" />
        <EmptyState v-else-if="!costRows.length" title="No cost data" description="Monthly tool and API costs will appear once recorded." />
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
      <ErrorState v-if="tenure.error" title="Couldn't load client tenure" :message="errText(tenure)" :on-retry="() => tenure.reload()" />
      <AppSkeleton v-else-if="tenure.loading" variant="table" :rows="5" :cols="3" />
      <EmptyState v-else-if="!tenureRows.length" title="No clients yet" description="Client tenure appears once contracts exist." />
      <div v-else class="table-scroll">
        <table>
          <thead><tr><th>Client</th><th>First Contract</th><th>Tenure (days)</th></tr></thead>
          <tbody>
            <tr v-for="r in tenureRows" :key="r[0]"><td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] }}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { background: var(--color-gray-50); min-height: 100vh; padding: var(--page-pad); color: var(--color-gray-900); }
.tiles { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); margin-bottom: var(--space-5); }
.tile, .card { background: var(--color-white); border: 1px solid var(--color-gray-200); border-radius: var(--radius-lg); box-shadow: var(--shadow-xs); }
.tile { padding: var(--space-4) var(--space-5); }
.card { padding: var(--space-5); }
.label { font-size: var(--fs-xs); color: var(--color-gray-600); font-weight: 600; letter-spacing: .03em; margin-bottom: var(--space-2); }
.value { font-size: var(--fs-xl); font-weight: 700; color: var(--color-gray-900); font-variant-numeric: tabular-nums; }
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
.bar-row { display: grid; grid-template-columns: 110px 1fr 90px; align-items: center; gap: var(--space-3); }
.bar-label { font-size: var(--fs-xs); color: var(--color-gray-600); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bar-track { background: var(--color-gray-200); border-radius: var(--radius-sm); height: 10px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--color-blue-500); border-radius: var(--radius-sm); }
.bar-fill.gold { background: var(--color-amber-700); }
.bar-value { font-size: var(--fs-xs); font-weight: 600; text-align: right; font-variant-numeric: tabular-nums; color: var(--color-gray-900); }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
th { text-align: left; color: var(--color-gray-600); font-weight: 500; padding: var(--space-2) var(--space-1); border-bottom: 1px solid var(--color-gray-200); }
td { padding: var(--space-2) var(--space-1); border-bottom: 1px solid var(--color-gray-200); }
tbody tr:last-child td { border-bottom: none; }
@media (max-width: 900px) {
  .tiles { grid-template-columns: repeat(2, 1fr); }
  .row { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .tiles { grid-template-columns: 1fr; }
  .bar-row { grid-template-columns: 90px 1fr 84px; gap: var(--space-2); }
}
</style>
