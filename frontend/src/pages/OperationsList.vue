<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import FinanceFormDialog from '../components/FinanceFormDialog.vue'

const props = defineProps({
  title: String,
  doctype: String,
  orderBy: { type: String, default: 'modified desc' },
  columns: Array, // [{ key, label, type? }]
  createKind: { type: String, default: null }, // 'Invoice' | 'Expense' shows a "+ New" button
})

const search = ref('')
const showForm = ref(false)

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
const perm = createResource({
  url: 'my_custom_app.api.can_create',
  params: { doctype: props.doctype },
  auto: !!props.createKind,
})
const canCreate = computed(() => !!props.createKind && perm.data === true)

const rows = computed(() => {
  const q = search.value.trim().toLowerCase()
  const all = list.data ?? []
  if (!q) return all
  return all.filter((r) => Object.values(r).some((v) => String(v ?? '').toLowerCase().includes(q)))
})

function show(row, col) {
  const v = row[col.key]
  if (v == null || v === '') return '—'
  if (col.type === 'money') return '₱' + Number(v).toLocaleString('en-PH')
  return v
}
</script>

<template>
  <div class="page">
    <header class="head">
      <h1>{{ title }}</h1>
      <div class="head-right">
        <input v-model="search" class="search" placeholder="Search..." />
        <button v-if="canCreate" class="btn-new" @click="showForm = true">+ New {{ createKind }}</button>
      </div>
    </header>
    <div class="card">
      <div v-if="list.loading" class="muted">···</div>
      <div v-else-if="!rows.length" class="muted">Nothing found.</div>
      <table v-else>
        <thead>
          <tr><th v-for="c in columns" :key="c.key">{{ c.label }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.name">
            <td v-for="c in columns" :key="c.key">{{ show(r, c) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <FinanceFormDialog v-if="createKind" v-model="showForm" :kind="createKind" @created="list.reload()" />
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
</style>
