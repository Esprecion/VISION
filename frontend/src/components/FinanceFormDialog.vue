<template>
  <Dialog v-model="show" :options="{ title: 'New ' + kind, size: '2xl' }">
    <template #body-content>
      <div class="form-grid">
        <template v-if="isInvoice">
          <div class="field">
            <label>Client *</label>
            <select v-model="form.client" :disabled="!!prefill?.client">
              <option value="">Select client</option>
              <option v-if="form.client && !(clients.data || []).some((c) => c.name === form.client)" :value="form.client">{{ form.client }}</option>
              <option v-for="c in clients.data || []" :key="c.name" :value="c.name">{{ c.client_name || c.name }}</option>
            </select>
          </div>
          <div class="field">
            <label>Contract (deal and client)</label>
            <select v-model="form.contract" :disabled="!!prefill?.contract">
              <option value="">None</option>
              <option v-if="form.contract && !(contracts.data || []).some((c) => c.name === form.contract)" :value="form.contract">{{ form.contract }}</option>
              <option v-for="c in contracts.data || []" :key="c.name" :value="c.name">{{ contractLabel(c) }}</option>
            </select>
          </div>
          <div v-if="form.contract" class="field">
            <label>Milestone</label>
            <select :value="form.milestone" :disabled="!!prefill?.milestone" @change="pickMilestone($event.target.value)">
              <option value="">Select milestone</option>
              <option v-if="form.milestone && !milestoneOptions.some((m) => m.milestone_name === form.milestone)" :value="form.milestone">{{ form.milestone }}</option>
              <option v-for="m in milestoneOptions" :key="m.milestone_name" :value="m.milestone_name">{{ m.milestone_name }} ({{ peso(m.amount) }})</option>
            </select>
          </div>

          <div v-if="contractTerms.text || form.contract" class="terms-box">
            <div class="terms-title">Contract terms: due {{ contractTerms.days }} days after issue</div>
            <div v-if="contractTerms.text" class="terms-body">{{ contractTerms.text }}</div>
          </div>

          <div class="section">Products / services</div>
          <div v-for="(it, i) in form.items" :key="'i' + i" class="line items">
            <input v-model="it.item_name" type="text" placeholder="Item" />
            <input v-model.number="it.quantity" type="number" min="0" step="any" placeholder="Qty" />
            <input v-model.number="it.rate" type="number" min="0" step="0.01" placeholder="Rate" />
            <span class="amt">{{ peso((Number(it.quantity) || 0) * (Number(it.rate) || 0)) }}</span>
            <button type="button" class="x" @click="form.items.splice(i, 1)">×</button>
          </div>
          <button type="button" class="btn-link" @click="form.items.push({ item_name: '', quantity: 1, rate: 0 })">+ Add item</button>

          <div class="section">Additional charges</div>
          <div v-for="(c, i) in form.charges" :key="'c' + i" class="line charges">
            <input v-model="c.description" type="text" placeholder="e.g. Rush fee, Hosting setup" />
            <input v-model.number="c.amount" type="number" step="0.01" placeholder="Amount" />
            <button type="button" class="x" @click="form.charges.splice(i, 1)">×</button>
          </div>
          <button type="button" class="btn-link" @click="form.charges.push({ description: '', amount: 0 })">+ Add charge</button>

          <div class="totals">
            <div>Subtotal <b>{{ peso(subtotal) }}</b></div>
            <div>Charges <b>{{ peso(chargesTotal) }}</b></div>
            <div class="grand">Total <b>{{ peso(total) }}</b></div>
          </div>

          <div class="two">
            <div class="field">
              <label>Issue Date *</label>
              <input v-model="form.issue_date" type="date" />
            </div>
            <div class="field">
              <label>Due Date *</label>
              <input v-model="form.due_date" type="date" :min="form.issue_date" />
            </div>
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
            <label>Date *</label>
            <input v-model="form.expense_date" type="date" />
          </div>
          <div class="field">
            <label>Project *</label>
            <select v-model="form.project">
              <option value="">Select project</option>
              <option v-for="p in projects.data || []" :key="p.name" :value="p.name">{{ projectLabel(p) }}</option>
            </select>
          </div>

          <div class="section">Cost breakdown (vendor / platform)</div>
          <div v-for="(it, i) in form.items" :key="'e' + i" class="line exp">
            <input v-model="it.vendor" type="text" placeholder="Vendor, e.g. Figma" />
            <input v-model="it.description" type="text" placeholder="What it was for" />
            <input v-model.number="it.amount" type="number" min="0" step="0.01" placeholder="Amount" />
            <button type="button" class="x" @click="form.items.splice(i, 1)">×</button>
          </div>
          <button type="button" class="btn-link" @click="form.items.push({ vendor: '', description: '', amount: 0 })">+ Add line</button>
          <div class="totals"><div class="grand">Total <b>{{ peso(expenseTotal) }}</b></div></div>
        </template>

        <div v-if="createDoc.error" class="error-msg">{{ errorText }}</div>
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
import { Dialog, createResource, call } from 'frappe-ui'
import { formatLocalDate, parseLocal } from '../utils/dateRange'

const props = defineProps({
  modelValue: Boolean,
  kind: { type: String, default: 'Invoice' }, // 'Invoice' | 'Expense'
  prefill: { type: Object, default: null }, // invoice only: { client, contract, milestone, items }
})
const emit = defineEmits(['update:modelValue', 'created'])

const isInvoice = props.kind === 'Invoice'
const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => {
  emit('update:modelValue', v)
  if (v) Object.assign(form, blank())
})

const statuses = ['Draft', 'Sent', 'Paid', 'Overdue']
const categories = ["Tools and Subscriptions", "Hardware", "Infrastructure", "Contractors and Freelancers", "Labor", "Other"]

function blank() {
  const t = formatLocalDate(new Date())
  if (isInvoice) {
    const p = props.prefill || {}
    const items = p.items?.length ? p.items : [{ item_name: '', quantity: 1, rate: 0 }]
    return {
      client: p.client || '', contract: p.contract || '', milestone: p.milestone || '',
      issue_date: t, due_date: t, status: 'Draft',
      items: items.map((i) => ({ ...i })), charges: [],
    }
  }
  return { category: '', expense_date: t, project: '', items: [{ vendor: '', description: '', amount: 0 }] }
}
const form = reactive(blank())

const clients = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Client', fields: ['name', 'client_name'], limit_page_length: 500 },
  auto: isInvoice,
})
const contracts = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Service Contract', fields: ['name', 'client', 'deal', 'status'], limit_page_length: 500 },
  auto: isInvoice,
})
const deals = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Deal', fields: ['name', 'deal_title'], limit_page_length: 500 },
  auto: isInvoice,
})
function contractLabel(c) {
  const d = (deals.data || []).find((x) => x.name === c.deal)
  const client = (clients.data || []).find((x) => x.name === c.client)
  return `${d?.deal_title || c.deal} - ${client?.client_name || c.client}`
}
const projects = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Project', fields: ['name', 'contract'], limit_page_length: 500 },
  auto: !isInvoice,
})
const pContracts = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Service Contract', fields: ['name', 'deal'], limit_page_length: 500 },
  auto: !isInvoice,
})
const pDeals = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Deal', fields: ['name', 'deal_title'], limit_page_length: 500 },
  auto: !isInvoice,
})
function projectLabel(p) {
  const c = (pContracts.data || []).find((x) => x.name === p.contract)
  const d = (pDeals.data || []).find((x) => x.name === c?.deal)
  return d?.deal_title ? `${d.deal_title} (${p.name})` : p.name
}

const contractTerms = ref({ days: 30, text: '' })
function applyDue() {
  if (!form.contract || !form.issue_date) return
  const dt = parseLocal(form.issue_date)
  dt.setDate(dt.getDate() + Number(contractTerms.value.days || 0))
  form.due_date = formatLocalDate(dt)
}
watch(() => form.contract, async (c) => {
  contractTerms.value = { days: 30, text: '' }
  if (!isInvoice || !c) return
  try {
    const doc = await call('frappe.client.get', { doctype: 'Service Contract', name: c })
    contractTerms.value = { days: doc.payment_terms_days ?? 30, text: doc.terms_and_conditions || '' }
    applyDue()
  } catch (e) {}
}, { immediate: true })
watch(() => form.issue_date, applyDue)

const milestoneOptions = ref([])
watch(() => form.contract, async (c) => {
  milestoneOptions.value = []
  if (!isInvoice || !c || props.prefill?.milestone) return
  try {
    const [doc, inv] = await Promise.all([
      call('frappe.client.get', { doctype: 'Service Contract', name: c }),
      call('frappe.client.get_list', { doctype: 'Invoice', filters: { contract: c }, fields: ['milestone'], limit_page_length: 100 }),
    ])
    const used = new Set((inv || []).map((i) => i.milestone))
    milestoneOptions.value = (doc.payment_milestones || []).filter((m) => !m.is_paid && !used.has(m.milestone_name))
    if (doc.client) form.client = doc.client
    form.milestone = ''
  } catch (e) {
    milestoneOptions.value = []
  }
})
function pickMilestone(name) {
  form.milestone = name
  const m = milestoneOptions.value.find((x) => x.milestone_name === name)
  if (m) form.items = [{ item_name: name, quantity: 1, rate: Number(m.amount) || 0 }]
}

const peso = (n) => '₱' + Number(n || 0).toLocaleString('en-PH')
const subtotal = computed(() => (form.items || []).reduce((s, i) => s + (Number(i.quantity) || 0) * (Number(i.rate) || 0), 0))
const chargesTotal = computed(() => (form.charges || []).reduce((s, c) => s + (Number(c.amount) || 0), 0))
const total = computed(() => subtotal.value + chargesTotal.value)
const expenseTotal = computed(() => (form.items || []).reduce((s, i) => s + (Number(i.amount) || 0), 0))

const valid = computed(() => {
  if (isInvoice) {
    const goodItems = form.items.filter((i) => i.item_name && Number(i.quantity) > 0)
    return !!form.client && goodItems.length > 0 && total.value > 0 && !!form.issue_date && !!form.due_date && form.due_date >= form.issue_date
  }
  return expenseTotal.value > 0 && form.items.some((i) => i.vendor) && !!form.category && !!form.expense_date && !!form.project
})

const createDoc = createResource({ url: 'frappe.client.insert', method: 'POST' })
const errorText = computed(() =>
  String(createDoc.error?.messages?.[0] || 'Something went wrong').replace(/<[^>]+>/g, '')
)

function submit() {
  const doc = { doctype: props.kind }
  for (const [k, v] of Object.entries(form)) {
    if (k === 'items' || k === 'charges') continue
    if (v !== '' && v !== null) doc[k] = v
  }
  if (isInvoice) {
    doc.items = form.items.filter((i) => i.item_name).map((i) => ({ item_name: i.item_name, quantity: Number(i.quantity) || 0, rate: Number(i.rate) || 0 }))
    doc.charges = form.charges.filter((c) => c.description).map((c) => ({ description: c.description, amount: Number(c.amount) || 0 }))
    doc.amount = total.value
    if (contractTerms.value.text) doc.terms_and_conditions = contractTerms.value.text
  }
  if (!isInvoice) {
    doc.items = form.items.filter((i) => i.vendor).map((i) => ({ vendor: i.vendor, description: i.description || '', amount: Number(i.amount) || 0 }))
    doc.amount = expenseTotal.value
  }
  createDoc.submit(
    { doc },
    {
      onSuccess: (saved) => {
        emit('created', saved)
        show.value = false
      },
    }
  )
}
</script>

<style scoped>
.form-grid { display: flex; flex-direction: column; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 13px; color: #4b5563; font-weight: 500; }
input, select { border: 1px solid #d1d5db; border-radius: 6px; padding: 8px 10px; font-size: 14px; background: #fff; }
input:focus, select:focus { outline: none; border-color: #6366f1; }
input:disabled, select:disabled { background: #f3f4f6; color: #6b7280; }
.section { font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-top: 4px; }
.line { display: grid; gap: 8px; align-items: center; }
.line.items { grid-template-columns: 1fr 70px 110px 110px 24px; }
.line.charges { grid-template-columns: 1fr 120px 24px; }
.amt { font-size: 13px; text-align: right; }
.x { background: none; border: none; color: #dc2626; font-size: 18px; cursor: pointer; }
.btn-link { background: none; border: none; color: #b45309; font-size: 13px; cursor: pointer; width: fit-content; padding: 0; }
.totals { display: flex; gap: 20px; justify-content: flex-end; font-size: 13px; color: #4b5563; border-top: 1px solid #e5e7eb; padding-top: 8px; }
.totals .grand { color: #111827; font-size: 15px; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.error-msg { color: #dc2626; font-size: 13px; }
.btn-primary { background: #111827; color: #fff; border: none; border-radius: 6px; padding: 9px 16px; font-weight: 600; font-size: 14px; cursor: pointer; width: 100%; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.terms-box { background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px 12px; font-size: 12px; color: #92400e; }
.terms-title { font-weight: 600; }
.terms-body { margin-top: 4px; white-space: pre-wrap; color: #78350f; }
.line.exp { grid-template-columns: 1fr 1.2fr 110px 24px; }
</style>
