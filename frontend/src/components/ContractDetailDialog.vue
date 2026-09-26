<template>
  <Dialog v-model="show" :options="{ title: 'Contract Detail', size: 'xl' }">
    <template #body-content>
      <div v-if="loading" class="loading-state">Loading...</div>
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
            <button v-if="!editing" class="btn-secondary" @click="startEdit">Edit</button>
          </div>
        </div>

        <div v-if="dealInfo" class="dd-section">
          <div class="section-label">Won Deal Reference</div>
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
          <div class="deal-total">Deal Value: {{ peso(dealInfo.value) }}</div>
        </div>

        <div class="dd-section">
          <div class="section-label">Payment Milestones</div>
          <div v-if="!editing">
            <table class="items-table">
              <thead>
                <tr><th>Milestone</th><th>Amount</th><th>Paid</th></tr>
              </thead>
              <tbody>
                <tr v-for="(m, i) in doc.payment_milestones" :key="i">
                  <td>{{ m.milestone_name }}</td>
                  <td>{{ peso(m.amount) }}</td>
                  <td>{{ m.is_paid ? 'Yes' : 'No' }}</td>
                </tr>
              </tbody>
            </table>
            <div class="deal-total">Contract Value: {{ peso(doc.value) }}</div>
          </div>
          <div v-else class="milestone-rows">
            <div v-for="(m, i) in form.payment_milestones" :key="i" class="milestone-row">
              <input v-model="m.milestone_name" type="text" placeholder="Milestone name" class="ms-name" />
              <input v-model.number="m.amount" type="number" placeholder="Amount" class="ms-amount" />
              <label class="paid-check"><input type="checkbox" v-model="m.is_paid" /> Paid</label>
              <button class="remove-row" @click="form.payment_milestones.splice(i, 1)">×</button>
            </div>
            <button class="btn-secondary add-row" @click="form.payment_milestones.push({ milestone_name: '', amount: 0, is_paid: 0 })">
              + Add milestone
            </button>
            <div class="deal-total">Total: {{ peso(editTotal) }}</div>
          </div>
        </div>

        <div class="dd-section">
          <div class="section-label">Dates</div>
          <div v-if="!editing" class="dates-row">
            <span>Start: {{ doc.start_date || '—' }}</span>
            <span>End: {{ doc.end_date || '—' }}</span>
          </div>
          <div v-else class="dates-row">
            <div class="field">
              <label>Start Date</label>
              <input v-model="form.start_date" type="date" />
            </div>
            <div class="field">
              <label>End Date</label>
              <input v-model="form.end_date" type="date" />
            </div>
          </div>
        </div>

        <div v-if="editing" class="edit-actions">
          <button class="btn-secondary" @click="cancelEdit">Cancel</button>
          <button class="btn-primary" :disabled="saving" @click="saveChanges">
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>

        <div class="dd-section comments-section">
          <button class="dd-section-toggle" @click="showComments = !showComments">
            Comments ({{ comments.length }}) {{ showComments ? '▴' : '▾' }}
          </button>
          <div v-if="showComments" class="comments-body">
            <div v-if="commentsLoading">Loading comments...</div>
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
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, call } from 'frappe-ui'

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
const form = reactive({ start_date: '', end_date: '', payment_milestones: [] })

const statusOptions = ['Draft', 'Under Negotiation', 'Finalized', 'Sent to Finance']

async function loadAll() {
  loading.value = true
  try {
    doc.value = await call('frappe.client.get', { doctype: 'Service Contract', name: props.contractName })
    if (doc.value?.deal) {
      dealInfo.value = await call('frappe.client.get', { doctype: 'Deal', name: doc.value.deal })
    }
    await loadComments()
  } finally {
    loading.value = false
  }
}

function startEdit() {
  form.start_date = doc.value.start_date || ''
  form.end_date = doc.value.end_date || ''
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

const editTotal = computed(() => form.payment_milestones.reduce((s, m) => s + (Number(m.amount) || 0), 0))

async function saveChanges() {
  saving.value = true
  try {
    const updatedDoc = {
      ...doc.value,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
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
.loading-state { padding: 24px; color: #6b7280; }
.contract-detail { display: flex; flex-direction: column; gap: 16px; }
.cd-header { display: flex; justify-content: space-between; align-items: flex-start; }
.cd-title { font-size: 18px; font-weight: 700; color: #111827; }
.cd-sub { font-size: 13px; color: #6b7280; margin-top: 2px; }
.cd-header-actions { display: flex; align-items: center; gap: 8px; }
.dd-section { border-top: 1px solid #e5e7eb; padding-top: 14px; }
.section-label { font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-bottom: 8px; }
.items-table { width: 100%; border-collapse: collapse; }
.items-table th, .items-table td { text-align: left; padding: 6px 8px; font-size: 13px; border-bottom: 1px solid #f3f4f6; }
.items-table th { color: #6b7280; font-weight: 600; }
.deal-total { margin-top: 8px; font-weight: 600; font-size: 14px; color: #111827; }
.milestone-rows { display: flex; flex-direction: column; gap: 8px; }
.milestone-row { display: grid; grid-template-columns: 1fr 110px 80px 24px; gap: 8px; align-items: center; }
.ms-name, .ms-amount { border: 1px solid #d1d5db; border-radius: 6px; padding: 6px 8px; font-size: 13px; }
.paid-check { font-size: 12px; color: #4b5563; display: flex; align-items: center; gap: 4px; }
.remove-row { background: none; border: none; color: #dc2626; font-size: 18px; cursor: pointer; }
.add-row { width: fit-content; margin-top: 4px; }
.dates-row { display: flex; gap: 24px; font-size: 13px; color: #111827; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 12px; color: #6b7280; }
.field input { border: 1px solid #d1d5db; border-radius: 6px; padding: 7px 9px; font-size: 13px; }
.edit-actions { display: flex; justify-content: flex-end; gap: 8px; }
.btn-secondary { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px; color: #111827; font-size: 13px; font-weight: 500; padding: 7px 12px; cursor: pointer; }
.btn-primary { background: #111827; color: #ffffff; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.status-select { border: 1px solid #e5e7eb; border-radius: 999px; padding: 5px 12px; font-size: 12px; font-weight: 600; cursor: pointer; }
.status-draft { background: #f3f4f6; color: #6b7280; }
.status-negotiation { background: #fef3c7; color: #b45309; }
.status-finalized { background: #dbeafe; color: #1d4ed8; }
.status-sent { background: #d1fae5; color: #065f46; }
.comments-section { }
.dd-section-toggle { background: none; border: none; cursor: pointer; font-weight: 600; color: #111827; font-size: 14px; padding: 0; }
.comments-body { margin-top: 12px; }
.comment-item { padding: 10px 0; border-bottom: 1px solid #f3f4f6; }
.comment-meta { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.comment-content { font-size: 14px; color: #111827; white-space: pre-wrap; }
.no-comments { color: #6b7280; font-size: 14px; padding: 8px 0; }
.comment-input-row { display: flex; gap: 8px; margin-top: 12px; }
.comment-input-row textarea { flex: 1; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; font-family: inherit; resize: vertical; }
.comment-input-row button { background: #b45309; color: white; border: none; border-radius: 6px; padding: 0 16px; cursor: pointer; }
</style>
