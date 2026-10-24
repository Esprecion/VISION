<template>
  <Dialog v-model="show" :options="{ title: 'Contract Detail', size: 'xl' }">
    <template #body-content>
      <div v-if="loading" class="loading-state">
        <AppSkeleton variant="text" :rows="3" />
        <AppSkeleton variant="table" :rows="3" :cols="4" />
      </div>
      <div v-else-if="doc" class="contract-detail">
        <div class="cd-header">
          <div>
            <div class="cd-title">{{ dealInfo?.deal_title || doc.deal }}</div>
            <div class="cd-sub">{{ doc.client }}</div>
          </div>
          <div class="cd-header-actions">
            <select
              :value="doc.status"
              class="status-select"
              :class="statusClass(doc.status)"
              @change="updateStatus($event.target.value)"
            >
              <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
            </select>
            <AppButton v-if="!editing" variant="outline" size="sm" @click="startEdit">Edit</AppButton>
          </div>
        </div>

        <div v-if="dealInfo" class="dd-section">
          <div class="section-label">Won Deal Reference</div>
          <div class="table-scroll">
            <table class="items-table">
              <thead>
                <tr><th>Product</th><th>Qty</th><th>Price</th><th>Amount</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in dealInfo.items" :key="item.name">
                  <td>{{ item.product }}</td>
                  <td>{{ item.quantity }}</td>
                  <td>{{ peso(item.price) }}</td>
                  <td>{{ peso(item.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="deal-total">Deal Value: {{ peso(dealInfo.value) }}</div>
        </div>

        <div class="dd-section">
          <div class="section-label">Payment Milestones</div>
          <div v-if="!editing">
            <div class="table-scroll">
              <table class="items-table">
                <thead>
                  <tr><th>Milestone</th><th>Amount</th><th>Paid</th><th>Invoice</th></tr>
                </thead>
                <tbody>
                  <tr v-for="(m, i) in doc.payment_milestones" :key="i">
                    <td>{{ m.milestone_name }}</td>
                    <td>{{ peso(m.amount) }}</td>
                    <td>{{ m.is_paid ? 'Yes' : 'No' }}</td>
                    <td>
                      <template v-if="invoiceFor(m)">{{ invoiceFor(m).name }}</template>
                      <AppButton v-else-if="canInvoice && !m.is_paid" variant="outline" size="sm" @click="startInvoice(m)">Create Invoice</AppButton>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="deal-total">Milestones total: {{ peso(viewTotal) }}</div>
            <div v-if="viewMismatch" class="warn">
              <AlertCircleIcon class="warn-icon" aria-hidden="true" />
              Does not match the deal value of {{ peso(dealVal) }} (difference {{ peso(Math.abs(viewTotal - dealVal)) }}). Click Edit to correct it.
            </div>
          </div>
          <div v-else class="milestone-rows">
            <div v-for="(m, i) in form.payment_milestones" :key="i" class="milestone-row">
              <AppTextInput v-model="m.milestone_name" placeholder="Milestone name" class="ms-name" />
              <AppTextInput v-model.number="m.amount" type="number" placeholder="Amount" class="ms-amount" />
              <label class="paid-check"><input type="checkbox" v-model="m.is_paid" /> Paid</label>
              <AppButton variant="ghost" size="sm" :icon="XIcon" @click="form.payment_milestones.splice(i, 1)" aria-label="Remove milestone" />
            </div>
            <AppButton variant="outline" size="sm" class="add-row" @click="form.payment_milestones.push({ milestone_name: '', amount: 0, is_paid: 0 })">
              <template #prefix><PlusIcon aria-hidden="true" /></template>
              Add milestone
            </AppButton>
            <div class="deal-total">Total: {{ peso(editTotal) }}</div>
            <div v-if="editMismatch" class="warn">
              <AlertCircleIcon class="warn-icon" aria-hidden="true" />
              Deal value is {{ peso(dealVal) }}; milestones are off by {{ peso(Math.abs(editTotal - dealVal)) }}.
            </div>
          </div>
        </div>

        <div class="dd-section">
          <div class="section-label">Dates</div>
          <div v-if="!editing" class="dates-row">
            <span>Start: {{ doc.start_date || '—' }}</span>
            <span>End: {{ doc.end_date || '—' }}</span>
          </div>
          <div v-else class="dates-row">
            <AppTextInput label="Start Date" type="date" v-model="form.start_date" />
            <AppTextInput label="End Date" type="date" v-model="form.end_date" />
          </div>
        </div>

        <div class="dd-section">
          <div class="section-label">Payment Terms &amp; Conditions</div>
          <div v-if="!editing">
            <div class="terms-text">{{ doc.terms_and_conditions || 'No terms written yet. Click Edit to add them.' }}</div>
          </div>
          <div v-else class="milestone-rows">
            <div class="field">
              <label>Terms and conditions</label>
              <textarea v-model="form.terms_and_conditions" rows="4" placeholder="e.g. Late payments accrue 2% per month. Work starts after the downpayment clears."></textarea>
            </div>
          </div>
        </div>

        <div v-if="editing" class="edit-actions">
          <AppButton variant="outline" size="sm" @click="cancelEdit">Cancel</AppButton>
          <AppButton variant="solid" theme="gray" size="sm" :loading="saving" @click="saveChanges">Save Changes</AppButton>
        </div>

        <div class="dd-section comments-section">
          <button class="dd-section-toggle" @click="showComments = !showComments">
            Comments ({{ comments.length }})
            <ChevronDownIcon class="dd-toggle-icon" :class="{ 'dd-toggle-icon--open': showComments }" aria-hidden="true" />
          </button>
          <div v-if="showComments" class="comments-body">
            <AppSkeleton v-if="commentsLoading" variant="text" :rows="2" />
            <template v-else>
              <div v-for="c in comments" :key="c.name" class="comment-item">
                <div class="comment-meta">{{ c.comment_by || c.owner }} · {{ formatRelative(c.creation) }}</div>
                <div class="comment-content">{{ c.content }}</div>
              </div>
              <div v-if="!comments.length" class="no-comments">No comments yet.</div>
            </template>
            <div class="comment-input-row">
              <textarea v-model="newComment" placeholder="e.g. Client pushed back on downpayment %, proposed 40/30/30 split..." rows="2"></textarea>
              <button :disabled="postingComment" @click="postComment">Post</button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
  <FinanceFormDialog
    v-if="canInvoice"
    v-model="showInvoice"
    kind="Invoice"
    :prefill="invoicePrefill"
    @created="loadInvoices(); emit('updated')"
  />
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, call } from 'frappe-ui'
import FinanceFormDialog from './FinanceFormDialog.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import ChevronDownIcon from '~icons/lucide/chevron-down'
import PlusIcon from '~icons/lucide/plus'
import XIcon from '~icons/lucide/x'
import AlertCircleIcon from '~icons/lucide/alert-circle'

const props = defineProps({
  modelValue: Boolean,
  contractName: String,
})
const emit = defineEmits(['update:modelValue', 'updated'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => {
  emit('update:modelValue', v)
  if (v && props.contractName) loadAll()
})

const loading = ref(false)
const doc = ref(null)
const dealInfo = ref(null)
const editing = ref(false)
const saving = ref(false)
const form = reactive({ start_date: '', end_date: '', payment_terms_days: 30, terms_and_conditions: '', payment_milestones: [] })

const statusOptions = ['Draft', 'Under Negotiation', 'Finalized', 'Sent to Finance']

const canInvoice = ref(false)
const invoices = ref([])
const showInvoice = ref(false)
const invoicePrefill = ref(null)

async function loadInvoices() {
  try {
    canInvoice.value = (await call('my_custom_app.api.can_create', { doctype: 'Invoice' })) === true
    invoices.value =
      (await call('frappe.client.get_list', {
        doctype: 'Invoice',
        filters: { contract: props.contractName },
        fields: ['name', 'milestone', 'status'],
        limit_page_length: 100,
      })) || []
  } catch (e) {
    invoices.value = []
  }
}
function invoiceFor(m) {
  return invoices.value.find((i) => i.milestone === m.milestone_name)
}
function startInvoice(m) {
  invoicePrefill.value = {
    client: doc.value.client,
    contract: props.contractName,
    milestone: m.milestone_name,
    items: [{ item_name: `${m.milestone_name} - ${dealInfo.value?.deal_title || doc.value.deal}`, quantity: 1, rate: Number(m.amount) || 0 }],
  }
  showInvoice.value = true
}

async function loadAll() {
  loading.value = true
  try {
    doc.value = await call('frappe.client.get', { doctype: 'Service Contract', name: props.contractName })
    if (doc.value?.deal) {
      dealInfo.value = await call('frappe.client.get', { doctype: 'Deal', name: doc.value.deal })
    }
    await loadInvoices()
    await loadComments()
  } finally {
    loading.value = false
  }
}

function startEdit() {
  form.start_date = doc.value.start_date || ''
  form.end_date = doc.value.end_date || ''
  form.payment_terms_days = doc.value.payment_terms_days ?? 30
  form.terms_and_conditions = doc.value.terms_and_conditions || ''
  form.payment_milestones = (doc.value.payment_milestones || []).map((m) => ({
    milestone_name: m.milestone_name,
    amount: m.amount,
    is_paid: m.is_paid,
  }))
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

const viewTotal = computed(() => (doc.value?.payment_milestones || []).reduce((s, m) => s + (Number(m.amount) || 0), 0))
const dealVal = computed(() => Number(dealInfo.value?.value) || 0)
const viewMismatch = computed(() => dealVal.value > 0 && Math.abs(viewTotal.value - dealVal.value) >= 0.01)
const editMismatch = computed(() => dealVal.value > 0 && Math.abs(editTotal.value - dealVal.value) >= 0.01)
const editTotal = computed(() => form.payment_milestones.reduce((s, m) => s + (Number(m.amount) || 0), 0))

async function saveChanges() {
  saving.value = true
  try {
    const updatedDoc = {
      ...doc.value,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      terms_and_conditions: form.terms_and_conditions || '',
      payment_milestones: form.payment_milestones,
    }
    const saved = await call('frappe.client.save', { doc: updatedDoc })
    doc.value = saved
    editing.value = false
    emit('updated')
  } finally {
    saving.value = false
  }
}

async function updateStatus(newStatus) {
  await call('frappe.client.set_value', {
    doctype: 'Service Contract',
    name: props.contractName,
    fieldname: 'status',
    value: newStatus,
  })
  doc.value.status = newStatus
  emit('updated')
}

function statusClass(status) {
  return {
    'status-draft': status === 'Draft',
    'status-negotiation': status === 'Under Negotiation',
    'status-finalized': status === 'Finalized',
    'status-sent': status === 'Sent to Finance',
  }
}

// --- Comments ---
const comments = ref([])
const commentsLoading = ref(false)
const showComments = ref(false)
const newComment = ref('')
const postingComment = ref(false)

async function loadComments() {
  commentsLoading.value = true
  try {
    const res = await call('frappe.client.get_list', {
      doctype: 'Comment',
      filters: { reference_doctype: 'Service Contract', reference_name: props.contractName },
      fields: ['name', 'content', 'comment_by', 'creation', 'owner'],
      order_by: 'creation desc',
      limit_page_length: 100,
    })
    comments.value = res || []
  } finally {
    commentsLoading.value = false
  }
}

async function postComment() {
  if (!newComment.value.trim()) return
  postingComment.value = true
  try {
    await call('frappe.client.insert', {
      doc: {
        doctype: 'Comment',
        comment_type: 'Comment',
        reference_doctype: 'Service Contract',
        reference_name: props.contractName,
        content: newComment.value.trim(),
      },
    })
    newComment.value = ''
    await loadComments()
  } finally {
    postingComment.value = false
  }
}

function formatRelative(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function peso(n) {
  return '₱' + Number(n || 0).toLocaleString('en-PH')
}
</script>

<style scoped>
.loading-state { display: flex; flex-direction: column; gap: var(--space-4); }
.contract-detail { display: flex; flex-direction: column; gap: var(--space-4); }
.cd-header { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--space-3); flex-wrap: wrap; }
.cd-title { font-size: var(--fs-lg); font-weight: 700; color: var(--color-gray-900); }
.cd-sub { font-size: var(--fs-sm); color: var(--color-gray-600); margin-top: var(--space-1); }
.cd-header-actions { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
.dd-section { border-top: 1px solid var(--color-gray-200); padding-top: var(--space-4); }
.section-label { font-size: var(--fs-xs); font-weight: 600; color: var(--color-gray-600); text-transform: uppercase; margin-bottom: var(--space-2); letter-spacing: 0.03em; }
.table-scroll { overflow-x: auto; }
.items-table { width: 100%; border-collapse: collapse; min-width: 420px; }
.items-table th, .items-table td { text-align: left; padding: var(--space-2); font-size: var(--fs-sm); border-bottom: 1px solid var(--color-gray-100); white-space: nowrap; }
.items-table th { color: var(--color-gray-600); font-weight: 600; }
.deal-total { margin-top: var(--space-2); font-weight: 600; font-size: var(--fs-sm); color: var(--color-gray-900); font-variant-numeric: tabular-nums; }
.milestone-rows { display: flex; flex-direction: column; gap: var(--space-2); }
.milestone-row { display: grid; grid-template-columns: 1fr 110px 80px 28px; gap: var(--space-2); align-items: center; }
.paid-check { font-size: var(--fs-xs); color: var(--color-gray-600); display: flex; align-items: center; gap: var(--space-1); cursor: pointer; }
.add-row { width: fit-content; margin-top: var(--space-1); }
.dates-row { display: flex; gap: var(--space-6); font-size: var(--fs-sm); color: var(--color-gray-900); flex-wrap: wrap; }
.field { display: flex; flex-direction: column; gap: var(--space-1); }
.field label { font-size: var(--fs-xs); color: var(--color-gray-600); font-weight: 500; }
.field textarea {
  border: 1px solid var(--color-gray-300); border-radius: var(--radius-sm);
  padding: var(--space-2); font-size: var(--fs-sm); font-family: inherit;
  color: var(--color-gray-900); background: var(--color-white);
}
.field textarea:focus { border-color: var(--color-amber-700); }
.edit-actions { display: flex; justify-content: flex-end; gap: var(--space-2); }
.status-select {
  border: 1px solid var(--color-gray-200); border-radius: var(--radius-full);
  padding: var(--space-1) var(--space-3); font-size: var(--fs-xs);
  font-weight: 600; cursor: pointer; font-family: inherit;
}
.status-draft { background: var(--color-gray-100); color: var(--color-gray-600); }
.status-negotiation { background: var(--color-amber-100); color: var(--color-amber-700); }
.status-finalized { background: var(--color-blue-100); color: var(--color-blue-700); }
.status-sent { background: var(--color-emerald-100); color: var(--color-emerald-800); }
.dd-section-toggle {
  display: inline-flex; align-items: center; gap: var(--space-1);
  background: none; border: none; cursor: pointer; font-weight: 600;
  color: var(--color-gray-900); font-size: var(--fs-sm); padding: 0; font-family: inherit;
}
.dd-toggle-icon {
  width: 14px; height: 14px; color: var(--color-gray-500);
  transition: transform 150ms ease;
}
.dd-toggle-icon--open { transform: rotate(180deg); }
.comments-body { margin-top: var(--space-3); }
.comment-item { padding: var(--space-3) 0; border-bottom: 1px solid var(--color-gray-100); }
.comment-meta { font-size: var(--fs-xs); color: var(--color-gray-600); margin-bottom: var(--space-1); }
.comment-content { font-size: var(--fs-sm); color: var(--color-gray-900); white-space: pre-wrap; }
.no-comments { color: var(--color-gray-600); font-size: var(--fs-sm); padding: var(--space-2) 0; }
.comment-input-row { display: flex; gap: var(--space-2); margin-top: var(--space-3); align-items: flex-start; }
.comment-input-row textarea {
  flex: 1; border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm);
  padding: var(--space-2); font-family: inherit; resize: vertical; font-size: var(--fs-sm);
  color: var(--color-gray-900);
}
.comment-input-row textarea:focus { border-color: var(--color-amber-700); }
.comment-input-row button {
  background: var(--color-amber-700); color: white; border: none;
  border-radius: var(--radius-sm); padding: var(--space-2) var(--space-4);
  cursor: pointer; font-family: inherit; font-size: var(--fs-sm); font-weight: 500;
}
.comment-input-row button:hover:not(:disabled) { background: var(--color-amber-800); }
.comment-input-row button:disabled { opacity: 0.5; cursor: not-allowed; }
.terms-text { white-space: pre-wrap; font-size: var(--fs-sm); color: var(--color-gray-700); margin-top: var(--space-2); }
.warn {
  display: flex; align-items: flex-start; gap: var(--space-1);
  margin-top: var(--space-2); font-size: var(--fs-xs); color: var(--color-red-700);
}
.warn-icon { width: 14px; height: 14px; flex-shrink: 0; margin-top: 1px; }
@media (max-width: 640px) {
  .milestone-row { grid-template-columns: 1fr 110px; }
  .milestone-row .remove-row { justify-self: start; }
}
</style>
