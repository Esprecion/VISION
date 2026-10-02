<script setup>
import { ref, computed } from 'vue'
import { createResource, call } from 'frappe-ui'
import FinanceFormDialog from '../components/FinanceFormDialog.vue'
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

function show(row, col) {
  const v = row[col.key]
  if (v == null || v === '') return '—'
  if (col.type === 'money') return '₱' + Number(v).toLocaleString('en-PH')
  return v
}
function openNew() { editName.value = null; showForm.value = true }
function openEdit(r) { editName.value = r.name; showForm.value = true }
async function remove(r) {
  if (!window.confirm('Delete ' + props.createKind + ' ' + r.name + '? This cannot be undone.')) return
  msg.value = ''
  try {
    await call('frappe.client.delete', { doctype: props.doctype, name: r.name })
    list.reload()
  } catch (e) {
    msg.value = String(e?.messages?.[0] || e?.message || 'Could not delete').replace(/<[^>]+>/g, '')
  }
}
</script>

<template>
  <div class="page">
    <header class="head">
      <h1>{{ title }}</h1>
      <div class="head-right">
        <input v-model="search" class="search" placeholder="Search..." />
        <button v-if="canCreate" class="btn-new" @click="openNew">+ New {{ createKind }}</button>
      </div>
    </header>
    <div class="filters">
      <label>From <input type="date" v-model="fromDate" :max="toDate || undefined" /></label>
      <label>To <input type="date" v-model="toDate" :min="fromDate || undefined" /></label>
      <button type="button" @click="setRange(quarterRange(0))">This quarter</button>
      <button type="button" @click="setRange(quarterRange(-1))">Last quarter</button>
      <button type="button" @click="setRange(yearRange())">This year</button>
      <select v-if="filterCol" v-model="optFilter">
        <option value="">All {{ filterCol.label.toLowerCase() }}</option>
        <option v-for="o in filterOptions" :key="o" :value="o">{{ o }}</option>
      </select>
      <button v-if="hasFilters" type="button" class="clear" @click="clearFilters">Clear</button>
      <span class="summary">Showing {{ rows.length }} of {{ (list.data || []).length }}<template v-if="moneyKey"> · {{ money(total) }}</template></span>
    </div>
    <div v-if="dateInvalid" class="err">The end date is before the start date, so the date filter is ignored.</div>
    <div v-if="msg" class="err">{{ msg }}</div>
    <div class="card">
      <div v-if="list.loading" class="muted">···</div>
      <div v-else-if="!rows.length" class="muted">Nothing found.</div>
      <table v-else>
        <thead>
          <tr><th v-for="c in columns" :key="c.key">{{ c.label }}</th><th v-if="hasActions"></th></tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.name">
            <td v-for="c in columns" :key="c.key">{{ show(r, c) }}</td>
            <td v-if="hasActions" class="actions">
              <button v-if="canEdit" type="button" class="act" @click="openEdit(r)">Edit</button>
              <button v-if="canDelete" type="button" class="act del" @click="remove(r)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <FinanceFormDialog v-if="createKind" v-model="showForm" :kind="createKind" :edit-name="editName" @created="list.reload()" />
  </div>
</template>

<style scoped>
.page { background: #f9fafb; min-height: 100vh; padding: 32px; font-family: 'Inter', sans-serif; color: #111827; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.head h1 { font-size: 20px; font-weight: 600; margin: 0; }
.head-right { display: flex; gap: 10px; align-items: center; }
.search { border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px 10px; font-size: 13px; width: 240px; }
.btn-new { background: #111827; color: #fff; border: none; border-radius: 6px; padding: 7px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px 20px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; color: #6b7280; font-weight: 500; padding: 8px 4px; border-bottom: 1px solid #e5e7eb; }
td { padding: 10px 4px; border-bottom: 1px solid #f3f4f6; }
.muted { color: #9ca3af; padding: 16px 0; }
.err { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; border-radius: 8px; padding: 10px 12px; font-size: 13px; margin-bottom: 12px; }
.actions { white-space: nowrap; text-align: right; }
.act { background: none; border: 1px solid #e5e7eb; border-radius: 6px; padding: 3px 10px; font-size: 12px; cursor: pointer; margin-left: 6px; color: #374151; }
.act:hover { background: #f3f4f6; }
.act.del { color: #dc2626; border-color: #fecaca; }
.filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 14px; font-size: 13px; color: #6b7280; }
.filters label { display: flex; align-items: center; gap: 6px; }
.filters input, .filters select { border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px 8px; font-size: 13px; background: #fff; color: #111827; font-family: inherit; }
.filters button { border: 1px solid #e5e7eb; background: #fff; border-radius: 6px; padding: 6px 10px; font-size: 13px; color: #111827; cursor: pointer; font-family: inherit; }
.filters button:hover { background: #f3f4f6; }
.filters .clear { color: #dc2626; border-color: #fecaca; }
.filters .summary { margin-left: auto; color: #4b5563; font-weight: 500; }
</style>
