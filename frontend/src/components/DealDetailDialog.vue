<template>
  <Dialog v-model="show" :options="{ title: dialogTitle, size: 'xl' }">
    <template #body-content>
      <div v-if="dealLoading" class="dd-loading">
        <AppSkeleton variant="text" :rows="3" />
        <AppSkeleton variant="table" :rows="3" :cols="4" />
      </div>
      <ErrorState
        v-else-if="dealError"
        title="Couldn't load this deal"
        :message="dealError"
        :on-retry="loadDeal"
      />
      <div class="deal-detail" v-else-if="doc">
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
            <div class="dd-items-scroll">
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
              <button class="dd-link-btn" @click="addItemRow"><PlusIcon class="dd-icon" aria-hidden="true" /> Add line</button>
            </div>
            <div class="dd-items-scroll">
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
                <button class="dd-remove-btn" aria-label="Remove line" @click="removeItemRow(idx)">
                  <XIcon aria-hidden="true" />
                </button>
              </div>
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
            Comments ({{ comments.length }})
            <ChevronDownIcon class="dd-toggle-icon" :class="{ 'dd-toggle-icon--open': showComments }" aria-hidden="true" />
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
            History ({{ filteredHistory.length }})
            <ChevronDownIcon class="dd-toggle-icon" :class="{ 'dd-toggle-icon--open': showHistory }" aria-hidden="true" />
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
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import ChevronDownIcon from '~icons/lucide/chevron-down'
import PlusIcon from '~icons/lucide/plus'
import XIcon from '~icons/lucide/x'

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
const dealLoading = ref(false)
const dealError = ref('')
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
  dealLoading.value = true
  dealError.value = ''
  try {
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
  } catch (e) {
    doc.value = null
    dealError.value = e?.messages?.[0] || e?.message || 'Something went wrong'
  } finally {
    dealLoading.value = false
  }
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
    doc.value = null
    dealError.value = ''
    clientsResource.reload()
    productsResource.reload()
    await loadDeal()
    if (doc.value) await Promise.all([loadComments(), loadHistory()])
  }
})
</script>

<style scoped>
.deal-detail { display: flex; flex-direction: column; gap: var(--space-4); }
.dd-loading { display: flex; flex-direction: column; gap: var(--space-4); }
.dd-icon { width: 14px; height: 14px; vertical-align: -2px; }
.dd-header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); }
.dd-stage-badge {
  background: var(--color-amber-100); color: var(--color-amber-700); font-size: var(--fs-xs); font-weight: 600;
  padding: var(--space-1) var(--space-3); border-radius: var(--radius-full); white-space: nowrap;
}
.dd-view-title { font-size: var(--fs-md); font-weight: 600; color: var(--color-gray-900); margin: 0 0 var(--space-1); }
.dd-view-value { font-size: var(--fs-sm); color: var(--color-gray-900); padding: var(--space-1) 0; }
.dd-field-title { margin-bottom: var(--space-1); }
.dd-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-3); }
.dd-field label { display: block; font-size: var(--fs-xs); color: var(--color-gray-600); margin-bottom: var(--space-1); font-weight: 500; }
.dd-input {
  width: 100%; border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm); padding: var(--space-2);
  font-size: var(--fs-sm); color: var(--color-gray-900); font-family: inherit; background: var(--color-white);
}
.dd-input:focus { border-color: var(--color-amber-700); }
.dd-value-readout { font-size: var(--fs-md); font-weight: 600; color: var(--color-gray-900); padding: var(--space-2) 0; }
.dd-items-header {
  display: flex; justify-content: space-between; align-items: center;
  font-size: var(--fs-sm); font-weight: 600; color: var(--color-gray-600); margin-bottom: var(--space-2);
}
.dd-link-btn {
  display: inline-flex; align-items: center; gap: var(--space-1);
  background: none; border: none; color: var(--color-amber-700); font-size: var(--fs-sm);
  cursor: pointer; font-family: inherit; font-weight: 500; padding: 0;
}
.dd-link-btn:hover { text-decoration: underline; }
.dd-items-scroll { overflow-x: auto; }
.dd-item-row {
  display: grid; grid-template-columns: 210px 56px 84px 84px 24px;
  gap: var(--space-2); align-items: center; margin-bottom: var(--space-2);
}
.dd-item-row-view { grid-template-columns: 210px 56px 84px 84px; font-size: var(--fs-sm); color: var(--color-gray-900); }
.dd-item-row-head { font-size: var(--fs-xs); color: var(--color-gray-600); font-weight: 600; }
.product-cell { width: 210px; overflow: hidden; }
.dd-qty, .dd-price { width: 100%; }
.dd-amount { font-size: var(--fs-sm); color: var(--color-gray-900); }
.dd-remove-btn {
  display: inline-flex; align-items: center; justify-content: center;
  background: none; border: none; color: var(--color-gray-500); cursor: pointer;
  padding: var(--space-1); border-radius: var(--radius-sm);
}
.dd-remove-btn svg { width: 14px; height: 14px; }
.dd-remove-btn:hover { color: var(--color-red-600); background: var(--color-red-100); }
.dd-actions {
  display: flex; align-items: center; justify-content: flex-end; gap: var(--space-3); padding: var(--space-3) 0;
  border-top: 1px solid var(--color-gray-200); border-bottom: 1px solid var(--color-gray-200);
}
.dd-btn-primary {
  background: var(--color-amber-700); color: var(--color-white); border: none; border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-4); font-size: var(--fs-sm); cursor: pointer; font-family: inherit; font-weight: 500;
}
.dd-btn-primary:hover:not(:disabled) { background: var(--color-amber-800); }
.dd-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.dd-btn-secondary {
  background: var(--color-white); color: var(--color-gray-700); border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-sm); padding: var(--space-2) var(--space-4); font-size: var(--fs-sm);
  cursor: pointer; font-family: inherit; font-weight: 500;
}
.dd-btn-secondary:hover { border-color: var(--color-gray-300); color: var(--color-gray-900); }
.dd-section-toggle {
  display: inline-flex; align-items: center; gap: var(--space-1);
  background: none; border: none; font-size: var(--fs-sm); font-weight: 600;
  color: var(--color-gray-900); cursor: pointer; padding: var(--space-1) 0; font-family: inherit;
}
.dd-toggle-icon {
  width: 14px; height: 14px; color: var(--color-gray-500);
  transition: transform 150ms ease;
}
.dd-toggle-icon--open { transform: rotate(180deg); }
.dd-section-body { margin-top: var(--space-2); display: flex; flex-direction: column; gap: var(--space-3); }
.dd-comment-form { display: flex; gap: var(--space-2); align-items: flex-start; }
.dd-textarea {
  flex: 1; border: 1px solid var(--color-gray-200); border-radius: var(--radius-sm); padding: var(--space-2);
  font-size: var(--fs-sm); font-family: inherit; color: var(--color-gray-900); resize: vertical;
}
.dd-textarea:focus { border-color: var(--color-amber-700); }
.dd-comment { border-left: 2px solid var(--color-amber-100); padding-left: var(--space-3); }
.dd-comment-meta { display: flex; gap: var(--space-2); align-items: baseline; font-size: var(--fs-xs); }
.dd-comment-content { font-size: var(--fs-sm); color: var(--color-gray-900); margin-top: var(--space-1); }
.dd-history-line { font-size: var(--fs-xs); color: var(--color-gray-700); margin-bottom: var(--space-1); }
.dd-old { color: var(--color-amber-700); text-decoration: line-through; }
.dd-new { color: var(--color-gray-900); font-weight: 600; }
.dd-timestamp { font-size: var(--fs-xs); color: var(--color-gray-500); }
.dd-empty { font-size: var(--fs-xs); color: var(--color-gray-600); }
@media (max-width: 640px) {
  .dd-grid { grid-template-columns: 1fr; }
}
</style>
