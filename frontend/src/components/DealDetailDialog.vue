<template>
  <Dialog v-model="show" :options="{ title: dialogTitle, size: 'xl' }">
    <template #body-content>
      <div class="deal-detail" v-if="doc">
        <div class="dd-header">
          <span class="dd-stage-badge">{{ doc.stage }}</span>
          <button v-if="!editing" class="dd-btn-secondary" @click="startEdit">Edit</button>
        </div>

        <!-- VIEW MODE -->
        <div v-if="!editing" class="dd-view">
          <h2 class="dd-view-title">{{ doc.deal_title }}</h2>
          <div class="dd-grid">
            <div class="dd-field">
              <label>Client</label>
              <div class="dd-view-value">{{ clientDisplayName }}</div>
            </div>
            <div class="dd-field">
              <label>Expected Close Date</label>
              <div class="dd-view-value">{{ doc.expected_close_date || '—' }}</div>
            </div>
            <div class="dd-field">
              <label>Total Value</label>
              <div class="dd-view-value dd-value-readout">{{ formattedTotal }}</div>
            </div>
          </div>

          <div class="dd-items">
            <div class="dd-items-header"><span>Line Items</span></div>
            <div class="dd-item-row dd-item-row-head">
              <span>Product</span><span>Qty</span><span>Price</span><span>Amount</span>
            </div>
            <div v-for="item in form.items" :key="item._key" class="dd-item-row dd-item-row-view">
              <span>{{ productDisplayName(item.product) }}</span>
              <span>{{ item.quantity }}</span>
              <span>{{ formatCurrency(item.price) }}</span>
              <span>{{ formatCurrency(item.quantity * item.price) }}</span>
            </div>
          </div>
        </div>

        <!-- EDIT MODE -->
        <div v-else class="dd-edit">
          <div class="dd-field dd-field-title">
            <label>Title</label>
            <input class="dd-input" v-model="form.deal_title" placeholder="Deal title" />
          </div>

          <div class="dd-grid">
            <div class="dd-field">
              <label>Client</label>
              <Autocomplete
                :options="clientOptions"
                :model-value="form.client"
                @update:modelValue="(val) => (form.client = val?.value ?? val ?? '')"
                placeholder="Select client"
              />
            </div>
            <div class="dd-field">
              <label>Expected Close Date</label>
              <input type="date" v-model="form.expected_close_date" class="dd-input" />
            </div>
            <div class="dd-field">
              <label>Total Value</label>
              <div class="dd-value-readout">{{ formattedTotal }}</div>
            </div>
          </div>

          <div class="dd-items">
            <div class="dd-items-header">
              <span>Line Items</span>
              <button class="dd-link-btn" @click="addItemRow">+ Add line</button>
            </div>
            <div class="dd-item-row dd-item-row-head">
              <span>Product</span><span>Qty</span><span>Price</span><span>Amount</span><span></span>
            </div>
            <div v-for="(item, idx) in form.items" :key="item._key" class="dd-item-row">
              <div class="product-cell">
                <Autocomplete
                  :options="productOptions"
                  :model-value="item.product"
                  @update:modelValue="(val) => (item.product = val?.value ?? val ?? '')"
                  placeholder="Product"
                />
              </div>
              <input type="number" min="1" v-model.number="item.quantity" class="dd-input dd-qty" />
              <input
                type="number"
                min="0"
                v-model.number="item.price"
                class="dd-input dd-price"
                @input="clampPrice(item)"
              />
              <span class="dd-amount">{{ formatCurrency(item.quantity * item.price) }}</span>
              <button class="dd-remove-btn" @click="removeItemRow(idx)">×</button>
            </div>
          </div>

          <div class="dd-actions">
            <button class="dd-btn-secondary" @click="cancelEdit">Cancel</button>
            <button class="dd-btn-primary" :disabled="saving || !isDirty" @click="saveChanges">
              {{ saving ? 'Saving…' : 'Save Changes' }}
            </button>
          </div>
        </div>

        <!-- Comments -->
        <div class="dd-section">
          <button class="dd-section-toggle" @click="showComments = !showComments">
            Comments ({{ comments.length }}) {{ showComments ? '▴' : '▾' }}
          </button>
          <div v-if="showComments" class="dd-section-body">
            <div class="dd-comment-form">
              <textarea
                v-model="newComment"
                placeholder="Add a comment…"
                rows="2"
                class="dd-textarea"
              ></textarea>
              <button
                class="dd-btn-primary"
                :disabled="!newComment.trim() || postingComment"
                @click="postComment"
              >
                {{ postingComment ? 'Posting…' : 'Post' }}
              </button>
            </div>
            <div v-if="comments.length === 0" class="dd-empty">No comments yet.</div>
            <div v-for="c in comments" :key="c.name" class="dd-comment">
              <div class="dd-comment-meta">
                <strong>{{ formatUser(c.owner) }}</strong>
                <span class="dd-timestamp">{{ formatRelative(c.creation) }}</span>
              </div>
              <div class="dd-comment-content">{{ c.content }}</div>
            </div>
          </div>
        </div>

        <!-- History -->
        <div class="dd-section">
          <button class="dd-section-toggle" @click="showHistory = !showHistory">
            History ({{ filteredHistory.length }}) {{ showHistory ? '▴' : '▾' }}
          </button>
          <div v-if="showHistory" class="dd-section-body">
            <div v-if="filteredHistory.length === 0" class="dd-empty">No changes recorded.</div>
            <div v-for="h in filteredHistory" :key="h.name" class="dd-history-entry">
              <div v-for="(c, i) in h.changes" :key="i" class="dd-history-line">
                <strong>{{ formatUser(h.owner) }}</strong>
                changed <em>{{ fieldLabel(c.field) }}</em>
                from <span class="dd-old">{{ displayVal(c.old) }}</span>
                to <span class="dd-new">{{ displayVal(c.new) }}</span>
                <span class="dd-timestamp">— {{ formatRelative(h.creation) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, Autocomplete, createListResource, call } from 'frappe-ui'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  dealName: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'updated'])

const show = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const doc = ref(null)
const editing = ref(false)
const form = reactive({
  deal_title: '',
  client: '',
  expected_close_date: '',
  items: [],
})
const saving = ref(false)
const showComments = ref(false)
const showHistory = ref(false)
const comments = ref([])
const history = ref([])
const newComment = ref('')
const postingComment = ref(false)

const dialogTitle = computed(() => doc.value?.deal_title || 'Deal')

const FIELD_LABELS = {
  deal_title: 'Title',
  client: 'Client',
  expected_close_date: 'Expected Close Date',
  value: 'Total Value',
  quantity: 'Qty',
  price: 'Price',
  product: 'Product',
}
function fieldLabel(f) {
  return FIELD_LABELS[f] || f
}
function displayVal(v) {
  return v === null || v === undefined || v === '' ? '(empty)' : v
}
function formatUser(email) {
  if (!email) return 'Unknown'
  const namePart = email.split('@')[0]
  return namePart.charAt(0).toUpperCase() + namePart.slice(1)
}
function formatRelative(dt) {
  if (!dt) return ''
  const diffMs = Date.now() - new Date(dt.replace(' ', 'T'))
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
function formatCurrency(n) {
  return '₱' + (Number(n) || 0).toLocaleString('en-PH', { maximumFractionDigits: 2 })
}
function clampPrice(item) {
  const s = String(item.price)
  if (s.replace(/\D/g, '').length > 12) {
    item.price = Number(s.slice(0, 12))
  }
}

const clientsResource = createListResource({
  doctype: 'Client',
  fields: ['name', 'client_name'],
  pageLength: 200,
  auto: false,
})
const productsResource = createListResource({
  doctype: 'Product',
  fields: ['name', 'product_name'],
  pageLength: 200,
  auto: false,
})
const clientOptions = computed(() =>
  (clientsResource.data || []).map((c) => ({ label: c.client_name, value: c.name }))
)
const productOptions = computed(() =>
  (productsResource.data || []).map((p) => ({ label: p.product_name, value: p.name }))
)
const clientDisplayName = computed(() => {
  const match = clientOptions.value.find((c) => c.value === form.client)
  return match ? match.label : form.client || '—'
})
function productDisplayName(productId) {
  const match = productOptions.value.find((p) => p.value === productId)
  return match ? match.label : productId || '—'
}

const formattedTotal = computed(() =>
  formatCurrency(form.items.reduce((sum, i) => sum + (i.quantity || 0) * (i.price || 0), 0))
)

let loadedSnapshot = ''
function snapshotForm() {
  return JSON.stringify({
    deal_title: form.deal_title,
    client: form.client,
    expected_close_date: form.expected_close_date,
    items: form.items.map((i) => ({ product: i.product, quantity: i.quantity, price: i.price })),
  })
}
const isDirty = computed(() => snapshotForm() !== loadedSnapshot)

function addItemRow() {
  form.items.push({ product: '', quantity: 1, price: 0, _key: Math.random().toString(36).slice(2) })
}
function removeItemRow(idx) {
  form.items.splice(idx, 1)
}

function startEdit() {
  clientsResource.reload()
  productsResource.reload()
  editing.value = true
}
function cancelEdit() {
  form.deal_title = doc.value.deal_title
  form.client = doc.value.client
  form.expected_close_date = doc.value.expected_close_date
  form.items = (doc.value.items || []).map((i) => ({
    product: i.product,
    quantity: i.quantity,
    price: i.price,
    _key: i.name || Math.random().toString(36).slice(2),
  }))
  editing.value = false
}

async function loadDeal() {
  if (!props.dealName) return
  const d = await call('frappe.client.get', { doctype: 'Deal', name: props.dealName })
  doc.value = d
  form.deal_title = d.deal_title
  form.client = d.client
  form.expected_close_date = d.expected_close_date
  form.items = (d.items || []).map((i) => ({
    product: i.product,
    quantity: i.quantity,
    price: i.price,
    _key: i.name || Math.random().toString(36).slice(2),
  }))
  loadedSnapshot = snapshotForm()
}

async function loadComments() {
  const res = await call('frappe.client.get_list', {
    doctype: 'Comment',
    filters: {
      reference_doctype: 'Deal',
      reference_name: props.dealName,
      comment_type: 'Comment',
    },
    fields: ['name', 'content', 'owner', 'creation'],
    order_by: 'creation desc',
    limit_page_length: 100,
  })
  comments.value = res || []
}

function extractRowChanges(rowChanged) {
  if (!Array.isArray(rowChanged)) return []
  const out = []
  for (const entry of rowChanged) {
    const fieldDiffs = entry[entry.length - 1]
    if (Array.isArray(fieldDiffs)) {
      for (const fd of fieldDiffs) {
        if (Array.isArray(fd) && fd.length >= 3) {
          out.push({ field: fd[0], old: fd[1], new: fd[2] })
        }
      }
    }
  }
  return out
}

async function loadHistory() {
  const res = await call('frappe.client.get_list', {
    doctype: 'Version',
    filters: { ref_doctype: 'Deal', docname: props.dealName },
    fields: ['name', 'data', 'owner', 'creation'],
    order_by: 'creation desc',
    limit_page_length: 100,
  })
  history.value = (res || [])
    .map((v) => {
      let changed = []
      let rowChanged = []
      try {
        const parsed = JSON.parse(v.data)
        changed = (parsed.changed || [])
          .filter((c) => c[0] !== 'stage')
          .map((c) => ({ field: c[0], old: c[1], new: c[2] }))
        rowChanged = extractRowChanges(parsed.row_changed)
      } catch (e) {
        changed = []
      }
      return { ...v, changes: [...changed, ...rowChanged] }
    })
    .filter((v) => v.changes.length > 0)
}
const filteredHistory = computed(() => history.value)

async function postComment() {
  if (!newComment.value.trim()) return
  postingComment.value = true
  try {
    await call('frappe.client.insert', {
      doc: {
        doctype: 'Comment',
        comment_type: 'Comment',
        reference_doctype: 'Deal',
        reference_name: props.dealName,
        content: newComment.value.trim(),
      },
    })
    newComment.value = ''
    await loadComments()
  } finally {
    postingComment.value = false
  }
}

async function saveChanges() {
  saving.value = true
  try {
    const recomputedValue = form.items.reduce(
      (sum, i) => sum + (i.quantity || 0) * (i.price || 0),
      0
    )
    const updatedDoc = {
      ...doc.value,
      deal_title: form.deal_title,
      client: form.client,
      expected_close_date: form.expected_close_date,
      value: recomputedValue,
      items: form.items.map((i) => ({
        product: i.product,
        quantity: i.quantity,
        price: i.price,
      })),
    }
    const saved = await call('frappe.client.save', { doc: updatedDoc })
    doc.value = saved
    loadedSnapshot = snapshotForm()
    editing.value = false
    await loadHistory()
    emit('updated')
  } finally {
    saving.value = false
  }
}

watch(show, async (v) => {
  if (v) {
    editing.value = false
    showComments.value = false
    showHistory.value = false
    clientsResource.reload()
    productsResource.reload()
    await loadDeal()
    await Promise.all([loadComments(), loadHistory()])
  }
})
</script>

<style scoped>
.deal-detail { display: flex; flex-direction: column; gap: 16px; }
.dd-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.dd-stage-badge {
  background: #fef3c7; color: #b45309; font-size: 12px; font-weight: 600;
  padding: 4px 10px; border-radius: 999px; white-space: nowrap;
}
.dd-view-title { font-size: 18px; font-weight: 600; color: #111827; margin: 0 0 4px; }
.dd-view-value { font-size: 14px; color: #111827; padding: 4px 0; }
.dd-field-title { margin-bottom: 4px; }
.dd-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.dd-field label { display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.dd-input {
  width: 100%; border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px 8px;
  font-size: 14px; color: #111827;
}
.dd-value-readout { font-size: 15px; font-weight: 600; color: #111827; padding: 6px 0; }
.dd-items-header {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 600; color: #6b7280; margin-bottom: 6px;
}
.dd-link-btn { background: none; border: none; color: #b45309; font-size: 13px; cursor: pointer; }
.dd-item-row {
  display: grid; grid-template-columns: 210px 56px 84px 84px 20px;
  gap: 8px; align-items: center; margin-bottom: 6px;
}
.dd-item-row-view { grid-template-columns: 210px 56px 84px 84px; font-size: 13px; color: #111827; }
.dd-item-row-head { font-size: 11px; color: #6b7280; font-weight: 600; }
.product-cell { width: 210px; overflow: hidden; }
.dd-qty, .dd-price { width: 100%; }
.dd-amount { font-size: 13px; color: #111827; }
.dd-remove-btn { background: none; border: none; color: #9ca3af; cursor: pointer; font-size: 16px; }
.dd-actions {
  display: flex; align-items: center; justify-content: flex-end; gap: 10px; padding: 10px 0;
  border-top: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;
}
.dd-btn-primary {
  background: #b45309; color: #fff; border: none; border-radius: 6px;
  padding: 6px 14px; font-size: 13px; cursor: pointer;
}
.dd-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.dd-btn-secondary {
  background: #fff; color: #6b7280; border: 1px solid #e5e7eb; border-radius: 6px;
  padding: 6px 14px; font-size: 13px; cursor: pointer;
}
.dd-section-toggle {
  background: none; border: none; font-size: 13px; font-weight: 600;
  color: #111827; cursor: pointer; padding: 4px 0;
}
.dd-section-body { margin-top: 8px; display: flex; flex-direction: column; gap: 10px; }
.dd-comment-form { display: flex; gap: 8px; align-items: flex-start; }
.dd-textarea {
  flex: 1; border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px 8px; font-size: 13px;
}
.dd-comment { border-left: 2px solid #fef3c7; padding-left: 10px; }
.dd-comment-meta { display: flex; gap: 8px; align-items: baseline; font-size: 12px; }
.dd-comment-content { font-size: 13px; color: #111827; margin-top: 2px; }
.dd-history-line { font-size: 12px; color: #374151; margin-bottom: 4px; }
.dd-old { color: #b45309; text-decoration: line-through; }
.dd-new { color: #111827; font-weight: 600; }
.dd-timestamp { font-size: 11px; color: #9ca3af; }
.dd-empty { font-size: 12px; color: #9ca3af; }
</style>
