<template>
  <Dialog v-model="show" :options="{ title: 'New ' + kind }">
    <template #body-content>
      <div class="form-grid">
        <template v-if="kind === 'Invoice'">
          <div class="field">
            <label>Client *</label>
            <select v-model="form.client">
              <option value="">Select client</option>
              <option v-for="c in clients.data || []" :key="c.name" :value="c.name">{{ c.client_name || c.name }}</option>
            </select>
          </div>
          <div class="field">
            <label>Contract</label>
            <select v-model="form.contract">
              <option value="">None</option>
              <option v-for="c in contracts.data || []" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
          </div>
          <div class="field">
            <label>Amount *</label>
            <input v-model.number="form.amount" type="number" min="0" step="0.01" />
          </div>
          <div class="field">
            <label>Issue Date *</label>
            <input v-model="form.issue_date" type="date" />
          </div>
          <div class="field">
            <label>Due Date *</label>
            <input v-model="form.due_date" type="date" :min="form.issue_date" />
          </div>
          <div class="field">
            <label>Status</label>
            <select v-model="form.status">
              <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
        </template>

        <template v-else>
          <div class="field">
            <label>Category *</label>
            <select v-model="form.category">
              <option value="">Select category</option>
              <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="field">
            <label>Amount *</label>
            <input v-model.number="form.amount" type="number" min="0" step="0.01" />
          </div>
          <div class="field">
            <label>Date *</label>
            <input v-model="form.expense_date" type="date" />
          </div>
          <div class="field">
            <label>Project</label>
            <select v-model="form.project">
              <option value="">None</option>
              <option v-for="p in projects.data || []" :key="p.name" :value="p.name">{{ p.name }}</option>
            </select>
          </div>
        </template>

        <div v-if="createDoc.error" class="error-msg">
          {{ createDoc.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <button class="btn-primary" :disabled="!valid || createDoc.loading" @click="submit">
        {{ createDoc.loading ? 'Saving...' : 'Save ' + kind }}
      </button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, createResource } from 'frappe-ui'
import { formatLocalDate } from '../utils/dateRange'

const props = defineProps({
  modelValue: Boolean,
  kind: { type: String, default: 'Invoice' }, // 'Invoice' | 'Expense'
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => emit('update:modelValue', v))

const statuses = ['Draft', 'Sent', 'Paid', 'Overdue']
const categories = ['Salaries', 'Tools and Subscriptions', 'Infrastructure', 'Other']

function blank() {
  const t = formatLocalDate(new Date())
  return props.kind === 'Invoice'
    ? { client: '', contract: '', amount: null, issue_date: t, due_date: t, status: 'Draft' }
    : { category: '', amount: null, expense_date: t, project: '' }
}
const form = reactive(blank())

const isInvoice = props.kind === 'Invoice'
const clients = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Client', fields: ['name', 'client_name'], limit_page_length: 500 },
  auto: isInvoice,
})
const contracts = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Service Contract', fields: ['name'], limit_page_length: 500 },
  auto: isInvoice,
})
const projects = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Project', fields: ['name'], limit_page_length: 500 },
  auto: !isInvoice,
})

const valid = computed(() => {
  if (!(Number(form.amount) > 0)) return false
  if (isInvoice) return !!form.client && !!form.issue_date && !!form.due_date && form.due_date >= form.issue_date
  return !!form.category && !!form.expense_date
})

const createDoc = createResource({ url: 'frappe.client.insert', method: 'POST' })

function submit() {
  const doc = { doctype: props.kind }
  for (const [k, v] of Object.entries(form)) {
    if (v !== '' && v !== null) doc[k] = v
  }
  createDoc.submit(
    { doc },
    {
      onSuccess: (saved) => {
        emit('created', saved)
        show.value = false
        Object.assign(form, blank())
      },
    }
  )
}
</script>

<style scoped>
.form-grid { display: flex; flex-direction: column; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 13px; color: #4b5563; font-weight: 500; }
.field input, .field select { border: 1px solid #d1d5db; border-radius: 6px; padding: 8px 10px; font-size: 14px; background: #fff; }
.field input:focus, .field select:focus { outline: none; border-color: #6366f1; }
.error-msg { color: #dc2626; font-size: 13px; }
.btn-primary { background: #111827; color: #fff; border: none; border-radius: 6px; padding: 9px 16px; font-weight: 600; font-size: 14px; cursor: pointer; width: 100%; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
