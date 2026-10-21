<template>
  <Dialog v-model="show" :options="{ title: editName ? 'Edit ' + kind + ' ' + editName : 'New ' + kind, size: '2xl' }">
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

          <div v-if="contractTerms.text" class="terms-box">
            <div class="terms-title">Contract terms and conditions</div>
            <div v-if="contractTerms.text" class="terms-body">{{ contractTerms.text }}</div>
          </div>

          <div class="section">Products / services</div>
          <div v-for="(it, i) in form.items" :key="'i' + i" class="line items">
            <input v-model="it.item_name" type="text" placeholder="Item" />
            <input v-model.number="it.quantity" type="number" min="0" step="any" placeholder="Qty" />
            <input v-model.number="it.rate" type="number" min="0" step="0.01" placeholder="Rate" />
            <span class="amt">{{ peso((Number(it.quantity) || 0) * (Number(it.rate) || 0)) }}</span>
            <button type="button" class="x" :aria-label="'Remove item ' + (i + 1)" @click="form.items.splice(i, 1)">
              <XIcon aria-hidden="true" />
            </button>
          </div>
          <button type="button" class="btn-link" @click="form.items.push({ item_name: '', quantity: 1, rate: 0 })">
            <PlusIcon aria-hidden="true" /> Add item
          </button>

          <div class="section">Additional charges</div>
          <div v-for="(c, i) in form.charges" :key="'c' + i" class="line charges">
            <input v-model="c.description" type="text" placeholder="e.g. Rush fee, Hosting setup" />
            <input v-model.number="c.amount" type="number" step="0.01" placeholder="Amount" />
            <button type="button" class="x" :aria-label="'Remove charge ' + (i + 1)" @click="form.charges.splice(i, 1)">
              <XIcon aria-hidden="true" />
            </button>
          </div>
          <button type="button" class="btn-link" @click="form.charges.push({ description: '', amount: 0 })">
            <PlusIcon aria-hidden="true" /> Add charge
          </button>

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
              <div class="due-row">
                <select v-model="netDays" @change="applyDue()">
                  <option value="15">Net 15</option>
                  <option value="30">Net 30</option>
                  <option value="45">Net 45</option>
                  <option value="60">Net 60</option>
                  <option value="">Custom date</option>
                </select>
                <input v-model="form.due_date" type="date" :min="form.issue_date" @input="netDays = ''" />
              </div>
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
            <button type="button" class="x" :aria-label="'Remove line ' + (i + 1)" @click="form.items.splice(i, 1)">
              <XIcon aria-hidden="true" />
            </button>
          </div>
          <button type="button" class="btn-link" @click="form.items.push({ vendor: '', description: '', amount: 0 })">
            <PlusIcon aria-hidden="true" /> Add line
          </button>
          <div class="totals"><div class="grand">Total <b>{{ peso(expenseTotal) }}</b></div></div>
        </template>

        <div v-if="activeRes.error" class="error-msg">
          <AlertCircleIcon aria-hidden="true" />
          <span>{{ errorText }}</span>
        </div>
      </div>
    </template>
    <template #actions>
      <button class="btn-primary" :disabled="!valid || activeRes.loading" @click="submit">
        {{ activeRes.loading ? 'Saving...' : (editName ? 'Update ' : 'Save ') + kind }}
      </button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, createResource, call } from 'frappe-ui'
import { formatLocalDate, parseLocal } from '../utils/dateRange'
import XIcon from '~icons/lucide/x'
import PlusIcon from '~icons/lucide/plus'
import AlertCircleIcon from '~icons/lucide/alert-circle'

const props = defineProps({
  modelValue: Boolean,
  kind: { type: String, default: 'Invoice' }, // 'Invoice' | 'Expense'
  prefill: { type: Object, default: null }, // invoice only: { client, contract, milestone, items }
  editName: { type: String, default: null }, // when set, the dialog edits this record
})
const emit = defineEmits(['update:modelValue', 'created'])

const isInvoice = props.kind === 'Invoice'
const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, async (v) => {
  emit('update:modelValue', v)
  if (v) {
    Object.assign(form, blank())
    loaded.value = null
    netDays.value = props.editName ? '' : '30'
    applyDue()
    if (!isInvoice) { projects.reload(); pContracts.reload(); pDeals.reload() }
    if (props.editName) await loadForEdit()
  }
})

const statuses = ['Draft', 'Sent', 'Paid', 'Overdue']
const categories = ["Tools and Subscriptions", "Hardware", "Contractors and Freelancers", "Labor", "Other"]

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
const netDays = ref('30')
function applyDue() {
  if (props.editName || netDays.value === '' || !form.issue_date) return
  const dt = parseLocal(form.issue_date)
  dt.setDate(dt.getDate() + Number(netDays.value))
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
  if (!isInvoice || !c || props.prefill?.milestone || props.editName) return
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
const saveDoc = createResource({ url: 'frappe.client.save', method: 'POST' })
const activeRes = computed(() => (props.editName ? saveDoc : createDoc))
const loaded = ref(null)
const errorText = computed(() =>
  String(activeRes.value.error?.messages?.[0] || 'Something went wrong').replace(/<[^>]+>/g, '')
)

async function loadForEdit() {
  try {
    const d = await call('frappe.client.get', { doctype: props.kind, name: props.editName })
    loaded.value = d
    if (isInvoice) {
      Object.assign(form, {
        client: d.client || '', contract: d.contract || '', milestone: d.milestone || '',
        issue_date: d.issue_date, due_date: d.due_date, status: d.status || 'Draft',
        items: (d.items || []).map((i) => ({ item_name: i.item_name, quantity: i.quantity, rate: i.rate })),
        charges: (d.charges || []).map((c) => ({ description: c.description, amount: c.amount })),
      })
    } else {
      Object.assign(form, {
        category: d.category || '', expense_date: d.expense_date, project: d.project || '',
        items: (d.items || []).map((i) => ({ vendor: i.vendor, description: i.description || '', amount: i.amount })),
      })
    }
  } catch (e) {
    saveDoc.error = e
  }
}

function submit() {
  const editing = !!props.editName
  if (editing && !loaded.value) return
  const doc = editing ? { ...loaded.value } : { doctype: props.kind }
  for (const [k, v] of Object.entries(form)) {
    if (k === 'items' || k === 'charges') continue
    if (editing) doc[k] = v === '' ? null : v
    else if (v !== '' && v !== null) doc[k] = v
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
  (props.editName ? saveDoc : createDoc).submit(
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
.form-grid { display: flex; flex-direction: column; gap: var(--space-3); }
.field { display: flex; flex-direction: column; gap: var(--space-1); }
.field label { font-size: var(--fs-sm); color: var(--color-gray-600); font-weight: 500; }
input, select { border: 1px solid var(--color-gray-300); border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3); font-size: var(--fs-sm); background: var(--color-white); color: var(--color-gray-900); font-family: inherit; }
input:focus, select:focus { border-color: var(--color-amber-700); }
input:disabled, select:disabled { background: var(--color-gray-100); color: var(--color-gray-600); }
.section { font-size: var(--fs-xs); font-weight: 600; color: var(--color-gray-600); text-transform: uppercase; margin-top: var(--space-1); }
.line { display: grid; gap: var(--space-2); align-items: center; }
.line.items { grid-template-columns: 1fr 70px 110px 110px 28px; }
.line.charges { grid-template-columns: 1fr 120px 28px; }
.amt { font-size: var(--fs-sm); text-align: right; font-variant-numeric: tabular-nums; }
.x {
  display: inline-flex; align-items: center; justify-content: center;
  background: none; border: none; color: var(--color-gray-500);
  cursor: pointer; padding: var(--space-1); border-radius: var(--radius-sm);
}
.x svg { width: 16px; height: 16px; }
.x:hover { background: var(--color-red-100); color: var(--color-red-600); }
.btn-link {
  display: inline-flex; align-items: center; gap: var(--space-1);
  background: none; border: none; color: var(--color-amber-700);
  font-size: var(--fs-sm); cursor: pointer; width: fit-content; padding: 0; font-family: inherit; font-weight: 500;
}
.btn-link svg { width: 14px; height: 14px; }
.btn-link:hover { color: var(--color-amber-800); text-decoration: underline; }
.totals { display: flex; gap: var(--space-5); justify-content: flex-end; font-size: var(--fs-sm); color: var(--color-gray-600); border-top: 1px solid var(--color-gray-200); padding-top: var(--space-2); }
.totals .grand { color: var(--color-gray-900); font-size: var(--fs-md); }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.error-msg {
  display: flex; align-items: flex-start; gap: var(--space-2);
  color: var(--color-red-600); font-size: var(--fs-sm);
}
.error-msg svg { width: 16px; height: 16px; flex: none; margin-top: 2px; }
.btn-primary { width: 100%; }
.terms-box { background: var(--color-amber-50); border: 1px solid var(--color-amber-200); border-radius: var(--radius-md); padding: var(--space-3); font-size: var(--fs-xs); color: var(--color-amber-800); }
.terms-title { font-weight: 600; }
.terms-body { margin-top: var(--space-1); white-space: pre-wrap; color: var(--color-amber-800); }
.line.exp { grid-template-columns: 1fr 1.2fr 110px 28px; }
.due-row { display: grid; grid-template-columns: 120px 1fr; gap: var(--space-2); }
@media (max-width: 640px) {
  .line.items, .line.exp { grid-template-columns: 1fr 64px 90px 90px 28px; }
  .two { grid-template-columns: 1fr; }
}
</style>
