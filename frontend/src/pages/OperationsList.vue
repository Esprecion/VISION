<script setup>
import { ref, computed } from 'vue'
import { createResource, call } from 'frappe-ui'
import FinanceFormDialog from '../components/FinanceFormDialog.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import SearchIcon from '~icons/lucide/search'
import PlusIcon from '~icons/lucide/plus'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import { quarterRange, yearRange } from '../utils/dateRange'

const props = defineProps({
  title: String,
  doctype: String,
  orderBy: { type: String, default: 'modified desc' },
  columns: Array, // [{ key, label, type? }]
  createKind: { type: String, default: null }, // 'Invoice' | 'Expense' shows a "+ New" button
})

const search = ref('')
const showForm = ref(false)
const editName = ref(null)
const msg = ref('')

const list = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: props.doctype,
    fields: ['name', ...props.columns.map((c) => c.key)],
    order_by: props.orderBy,
    limit_page_length: 200,
  },
  auto: true,
})

// Only roles with create permission see the button (the server enforces it too)
const perms = createResource({
  url: 'my_custom_app.api.get_perms',
  params: { doctype: props.doctype },
  auto: !!props.createKind,
})
const canCreate = computed(() => !!props.createKind && perms.data?.create === true)
const canEdit = computed(() => !!props.createKind && perms.data?.write === true)
const canDelete = computed(() => !!props.createKind && perms.data?.delete === true)
const hasActions = computed(() => canEdit.value || canDelete.value)

const fromDate = ref('')
const toDate = ref('')
const optFilter = ref('')
const dateKey = computed(() => props.columns.find((c) => c.key === 'issue_date' || c.key === 'expense_date')?.key)
const filterCol = computed(() => props.columns.find((c) => c.key === 'status' || c.key === 'category'))
const moneyKey = computed(() => props.columns.find((c) => c.type === 'money')?.key)
const filterOptions = computed(() => {
  const k = filterCol.value?.key
  if (!k) return []
  return [...new Set((list.data ?? []).map((r) => r[k]).filter(Boolean))].sort()
})
const dateInvalid = computed(() => !!fromDate.value && !!toDate.value && fromDate.value > toDate.value)
const hasFilters = computed(() => !!(fromDate.value || toDate.value || optFilter.value || search.value))
function setRange(r) { fromDate.value = r.from; toDate.value = r.to }
function clearFilters() { fromDate.value = ''; toDate.value = ''; optFilter.value = ''; search.value = '' }
const money = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')

const rows = computed(() => {
  const q = search.value.trim().toLowerCase()
  const dk = dateKey.value
  const fk = filterCol.value?.key
  return (list.data ?? []).filter((r) => {
    if (fk && optFilter.value && r[fk] !== optFilter.value) return false
    if (dk && !dateInvalid.value) {
      const d = r[dk]
      if (fromDate.value && (!d || d < fromDate.value)) return false
      if (toDate.value && (!d || d > toDate.value)) return false
    }
    if (q && !Object.values(r).some((v) => String(v ?? '').toLowerCase().includes(q))) return false
    return true
  })
})
const total = computed(() => rows.value.reduce((t, r) => t + Number(r[moneyKey.value] || 0), 0))

const listError = computed(() =>
  String(list.error?.messages?.[0] || list.error?.message || 'Something went wrong').replace(/<[^>]+>/g, '')
)

const STATUS_CLASSES = {
  Draft: 'is-neutral',
  Sent: 'is-sent',
  Paid: 'is-paid',
  Overdue: 'is-overdue',
}
const statusClass = (v) => STATUS_CLASSES[v] || 'is-neutral'

function show(row, col) {
  const v = row[col.key]
  if (v == null || v === '') return '—'
  if (col.type === 'money') return '₱' + Number(v).toLocaleString('en-PH')
  return v
}
function openNew() { editName.value = null; showForm.value = true }
function openEdit(r) { editName.value = r.name; showForm.value = true }

const showConfirm = ref(false)
const pendingDelete = ref(null)
const deleting = ref(false)
function askDelete(r) { pendingDelete.value = r; showConfirm.value = true }
async function doDelete() {
  if (!pendingDelete.value) return
  msg.value = ''
  deleting.value = true
  try {
    await call('frappe.client.delete', { doctype: props.doctype, name: pendingDelete.value.name })
    showConfirm.value = false
    list.reload()
  } catch (e) {
    msg.value = String(e?.messages?.[0] || e?.message || 'Could not delete').replace(/<[^>]+>/g, '')
    showConfirm.value = false
  } finally {
    deleting.value = false
    pendingDelete.value = null
  }
}
</script>

<template>
  <div class="page">
    <PageHeader :title="title">
      <template #actions>
        <div class="head-right">
          <div class="search-wrap">
            <SearchIcon aria-hidden="true" />
            <input v-model="search" class="search" :placeholder="'Search ' + title.toLowerCase() + '...'" :aria-label="'Search ' + title" />
          </div>
          <button v-if="canCreate" class="btn-new" @click="openNew">
            <PlusIcon aria-hidden="true" /> New {{ createKind }}
          </button>
        </div>
      </template>
    </PageHeader>

    <div class="filters">
      <label>From <input type="date" v-model="fromDate" :max="toDate || undefined" aria-label="From date" /></label>
      <label>To <input type="date" v-model="toDate" :min="fromDate || undefined" aria-label="To date" /></label>
      <button type="button" @click="setRange(quarterRange(0))">This quarter</button>
      <button type="button" @click="setRange(quarterRange(-1))">Last quarter</button>
      <button type="button" @click="setRange(yearRange())">This year</button>
      <select v-if="filterCol" v-model="optFilter" :aria-label="'Filter by ' + filterCol.label">
        <option value="">All {{ filterCol.label.toLowerCase() }}</option>
        <option v-for="o in filterOptions" :key="o" :value="o">{{ o }}</option>
      </select>
      <button v-if="hasFilters" type="button" class="clear" @click="clearFilters">Clear</button>
      <span class="summary">Showing {{ rows.length }} of {{ (list.data || []).length }}<template v-if="moneyKey"> · {{ money(total) }}</template></span>
    </div>
    <div v-if="dateInvalid" class="err">
      <AlertCircleIcon aria-hidden="true" />
      <span>The end date is before the start date, so the date filter is ignored.</span>
    </div>
    <div v-if="msg" class="err" role="alert">
      <AlertCircleIcon aria-hidden="true" />
      <span>{{ msg }}</span>
    </div>

    <div class="card">
      <ErrorState v-if="list.error" title="Couldn't load this list" :message="listError" :on-retry="() => list.reload()" />
      <AppSkeleton v-else-if="list.loading" variant="table" :rows="6" :cols="columns.length + (hasActions ? 1 : 0)" />
      <EmptyState
        v-else-if="!rows.length"
        :title="hasFilters ? 'No matches' : 'No ' + title.toLowerCase() + ' yet'"
        :description="hasFilters ? 'Try adjusting or clearing the filters.' : ('Create your first ' + (createKind || 'record').toLowerCase() + ' to get started.')"
      >
        <template v-if="hasFilters" #action>
          <button type="button" class="btn-clear" @click="clearFilters">Clear filters</button>
        </template>
      </EmptyState>
      <div v-else class="table-scroll">
        <table>
          <thead>
            <tr><th v-for="c in columns" :key="c.key">{{ c.label }}</th><th v-if="hasActions"></th></tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.name">
              <td v-for="c in columns" :key="c.key">
                <span v-if="c.key === 'status'" class="status" :class="statusClass(show(r, c))">{{ show(r, c) }}</span>
                <template v-else>{{ show(r, c) }}</template>
              </td>
              <td v-if="hasActions" class="actions">
                <button v-if="canEdit" type="button" class="act" @click="openEdit(r)">Edit</button>
                <button v-if="canDelete" type="button" class="act del" @click="askDelete(r)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <FinanceFormDialog v-if="createKind" v-model="showForm" :kind="createKind" :edit-name="editName" @created="list.reload()" />
    <AppConfirmDialog
      v-model="showConfirm"
      :title="'Delete ' + (createKind || 'record')"
      :message="pendingDelete ? 'Delete ' + createKind + ' ' + pendingDelete.name + '? This cannot be undone.' : ''"
      confirm-label="Delete"
      destructive
      :loading="deleting"
      @confirm="doDelete"
      @cancel="pendingDelete = null"
    />
  </div>
</template>

<style scoped>
.page { background: var(--color-gray-50); min-height: 100vh; padding: var(--page-pad); color: var(--color-gray-900); }
.head-right { display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap; }
.search-wrap {
  display: flex; align-items: center; gap: var(--space-2);
  border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm);
  background: var(--color-white); padding-left: var(--space-3);
}
.search-wrap svg { width: 16px; height: 16px; color: var(--color-gray-500); flex: none; }
.search { border: none; padding: var(--space-2) var(--space-3) var(--space-2) 0; font-size: var(--fs-sm); width: 200px; font-family: inherit; color: var(--color-gray-900); background: transparent; }
.search::placeholder { color: var(--color-gray-500); }
.search-wrap:focus-within { border-color: var(--color-amber-700); }
.btn-new {
  display: inline-flex; align-items: center; gap: var(--space-1);
  background: var(--color-gray-900); color: var(--color-white); border: none;
  border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3);
  font-size: var(--fs-sm); font-weight: 600; cursor: pointer; font-family: inherit;
}
.btn-new svg { width: 15px; height: 15px; }
.btn-new:hover { background: var(--color-gray-700); }
.card { background: var(--color-white); border: 1px solid var(--color-gray-200); border-radius: var(--radius-lg); padding: var(--space-3) var(--space-5); box-shadow: var(--shadow-xs); }
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: var(--fs-sm); }
th { text-align: left; color: var(--color-gray-600); font-weight: 500; padding: var(--space-2) var(--space-1); border-bottom: 1px solid var(--color-gray-200); white-space: nowrap; }
td { padding: var(--space-3) var(--space-1); border-bottom: 1px solid var(--color-gray-100); }
tbody tr:last-child td { border-bottom: none; }
.status {
  display: inline-block; padding: 2px var(--space-2); border-radius: 999px;
  font-size: var(--fs-xs); font-weight: 600; white-space: nowrap;
}
.status.is-neutral { background: var(--color-gray-100); color: var(--color-gray-700); }
.status.is-sent { background: var(--color-blue-100); color: var(--color-blue-700); }
.status.is-paid { background: var(--color-emerald-100); color: var(--color-emerald-800); }
.status.is-overdue { background: var(--color-red-100); color: var(--color-red-700); }
.err {
  display: flex; align-items: flex-start; gap: var(--space-2);
  background: var(--color-red-50, #fef2f2); border: 1px solid var(--color-red-200);
  color: var(--color-red-700); border-radius: var(--radius-md);
  padding: var(--space-3); font-size: var(--fs-sm); margin-bottom: var(--space-3);
}
.err svg { width: 16px; height: 16px; flex: none; margin-top: 2px; }
.actions { white-space: nowrap; text-align: right; }
.act { background: none; border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm); padding: 3px 10px; font-size: var(--fs-xs); cursor: pointer; margin-left: var(--space-2); color: var(--color-gray-700); font-family: inherit; }
.act:hover { background: var(--color-gray-100); }
.act.del { color: var(--color-red-600); border-color: var(--color-red-200); }
.act.del:hover { background: var(--color-red-50, #fef2f2); }
.btn-clear {
  background: none; border: none; color: var(--color-amber-700);
  font-size: var(--fs-sm); font-weight: 600; cursor: pointer; text-decoration: underline; font-family: inherit;
}
.filters { display: flex; flex-wrap: wrap; gap: var(--space-2); align-items: center; margin-bottom: var(--space-3); font-size: var(--fs-sm); color: var(--color-gray-600); }
.filters label { display: flex; align-items: center; gap: var(--space-2); }
.filters input, .filters select { border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm); padding: 6px var(--space-2); font-size: var(--fs-sm); background: var(--color-white); color: var(--color-gray-900); font-family: inherit; }
.filters button { border: 1px solid var(--color-gray-200); background: var(--color-white); border-radius: var(--radius-sm); padding: 6px 10px; font-size: var(--fs-sm); color: var(--color-gray-900); cursor: pointer; font-family: inherit; }
.filters button:hover { background: var(--color-gray-100); }
.filters .clear { color: var(--color-red-600); border-color: var(--color-red-200); }
.filters .summary { margin-left: auto; color: var(--color-gray-600); font-weight: 500; }
@media (max-width: 640px) {
  .search { width: 140px; }
  .filters .summary { margin-left: 0; width: 100%; }
}
</style>
