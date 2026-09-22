<template>
  <Dialog v-model="show" :options="{ title: 'Add Deal', size: '2xl' }">
    <template #body-content>
      <div class="form-grid">
        <div class="stage-badge">Adding to: <strong>{{ stage }}</strong></div>

        <div class="field">
          <label>Deal Title *</label>
          <input v-model="form.deal_title" type="text" placeholder="e.g. Clinic Rollout - Phase 1" />
        </div>

        <div class="field">
          <label>Client *</label>
          <Autocomplete
            :options="clientOptions"
            :model-value="form.client"
            @update:modelValue="(val) => (form.client = val?.value ?? val ?? '')"
            placeholder="Search clients..."
          />
        </div>

        <div class="field">
          <label>Expected Close Date</label>
          <input v-model="form.expected_close_date" type="date" />
        </div>

        <div class="field">
          <label>Line Items</label>
          <div class="items-table-wrap">
            <div class="items-table">
              <div class="items-head">
                <span>Product</span>
                <span>Qty</span>
                <span>Price</span>
                <span>Amount</span>
                <span></span>
              </div>
              <div v-for="(item, idx) in items" :key="idx" class="items-row">
                <div class="product-cell">
                  <Autocomplete
                    :options="productOptions"
                    :model-value="item.product"
                    @update:modelValue="(val) => (item.product = val?.value ?? val ?? '')"
                    placeholder="Select product"
                  />
                </div>
                <input v-model.number="item.quantity" type="number" min="0" />
                <input v-model.number="item.price" type="number" min="0" step="0.01" @input="clampPrice(item)" />
                <button
                  class="row-amount"
                  :title="peso(rowAmount(item))"
                  @click="toggleRowExpanded(idx)"
                >
                  {{ displayAmount(peso(rowAmount(item)), expandedRows[idx]) }}
                </button>
                <button class="remove-row" @click="removeItem(idx)">×</button>
              </div>
            </div>
          </div>
          <button class="btn-link" @click="addItem">+ Add line</button>
        </div>

        <div class="total-row">
          <span>Total Value</span>
          <button
            class="total-value"
            :title="peso(totalValue)"
            @click="totalExpanded = !totalExpanded"
          >
            {{ displayAmount(peso(totalValue), totalExpanded) }}
          </button>
        </div>

        <div v-if="createDeal.error" class="error-msg">
          {{ createDeal.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <button
        class="btn-primary"
        :disabled="!canSubmit || createDeal.loading"
        @click="submit"
      >
        {{ createDeal.loading ? 'Saving...' : 'Save Deal' }}
      </button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, Autocomplete, createResource, createListResource } from 'frappe-ui'

const props = defineProps({
  modelValue: Boolean,
  stage: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => {
  emit('update:modelValue', v)
  if (v) {
    // refetch on every open — Clients/Products may have been added since last load
    clientsResource.reload()
    productsResource.reload()
  }
})

// --- Client + Product option lists (fetched once, filtered client-side by Autocomplete) ---
const clientsResource = createListResource({
  doctype: 'Client',
  fields: ['name', 'client_name'],
  pageLength: 100,
  auto: true,
})
const clientOptions = computed(() =>
  (clientsResource.data || []).map((c) => ({
    label: c.client_name || c.name,
    value: c.name,
  }))
)

const productsResource = createListResource({
  doctype: 'Product',
  fields: ['name', 'product_name'],
  pageLength: 100,
  auto: true,
})
const productOptions = computed(() =>
  (productsResource.data || []).map((p) => ({
    label: p.product_name || p.name,
    value: p.name,
  }))
)

const form = reactive({
  deal_title: '',
  client: '',
  expected_close_date: '',
})

const items = ref([{ product: '', quantity: 1, price: 0 }])
const expandedRows = reactive({})
const totalExpanded = ref(false)

const MAX_PESO_DIGITS = 12 // caps price entry at a realistic ceiling (~₱999B)
const AMOUNT_TRUNCATE_LEN = 14 // characters shown before "..." kicks in

function addItem() {
  items.value.push({ product: '', quantity: 1, price: 0 })
}
function removeItem(idx) {
  items.value.splice(idx, 1)
  delete expandedRows[idx]
}
function toggleRowExpanded(idx) {
  expandedRows[idx] = !expandedRows[idx]
}
function displayAmount(text, expanded) {
  if (expanded || text.length <= AMOUNT_TRUNCATE_LEN) return text
  return text.slice(0, AMOUNT_TRUNCATE_LEN) + '...'
}
function clampPrice(item) {
  const digits = String(Math.trunc(Number(item.price) || 0)).length
  if (digits > MAX_PESO_DIGITS) {
    item.price = Number(String(item.price).slice(0, MAX_PESO_DIGITS))
  }
}
function rowAmount(item) {
  return (Number(item.quantity) || 0) * (Number(item.price) || 0)
}
const totalValue = computed(() =>
  items.value.reduce((sum, item) => sum + rowAmount(item), 0)
)

const validItems = computed(() =>
  items.value.filter((i) => i.product && Number(i.quantity) > 0 && Number(i.price) >= 0)
)

const canSubmit = computed(
  () => form.deal_title && form.client && validItems.value.length > 0
)

const createDeal = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
})

function submit() {
  createDeal.submit(
    {
      doc: {
        doctype: 'Deal',
        deal_title: form.deal_title,
        client: form.client,
        stage: props.stage,
        expected_close_date: form.expected_close_date || null,
        value: totalValue.value,
        items: validItems.value.map((i) => ({
          product: i.product,
          quantity: i.quantity,
          price: i.price,
        })),
      },
    },
    {
      onSuccess: (doc) => {
        emit('created', doc)
        show.value = false
        form.deal_title = ''
        form.client = ''
        form.expected_close_date = ''
        items.value = [{ product: '', quantity: 1, price: 0 }]
      },
    }
  )
}

function peso(n) {
  return '₱' + Number(n || 0).toLocaleString('en-PH')
}
</script>

<style scoped>
.form-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.stage-badge {
  font-size: 13px;
  color: #6b7280;
  background: #fef3c7;
  border-radius: 6px;
  padding: 6px 10px;
  width: fit-content;
}
.stage-badge strong {
  color: #b45309;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.field label {
  font-size: 13px;
  color: #4b5563;
  font-weight: 500;
}
.field input {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 14px;
  font-family: inherit;
}
.field input:focus {
  outline: none;
  border-color: #6366f1;
}
.items-table-wrap {
  overflow-x: auto;
  margin-top: 4px;
}
.items-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 480px;
}
.items-head,
.items-row {
  display: grid;
  grid-template-columns: 210px 56px 84px 84px 20px;
  gap: 8px;
  align-items: center;
}
.items-head {
  font-size: 11px;
  color: #9ca3af;
  font-weight: 500;
  text-transform: uppercase;
}
.product-cell {
  width: 210px;
  overflow: hidden;
}
.items-row input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 13px;
  font-family: inherit;
}
.row-amount {
  background: transparent;
  border: none;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  padding: 0;
  text-align: left;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
}
.row-amount:hover {
  color: #b45309;
}
.remove-row {
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
}
.remove-row:hover {
  color: #dc2626;
}
.btn-link {
  background: transparent;
  border: none;
  color: #6366f1;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  text-align: left;
  width: fit-content;
}
.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e5e7eb;
  padding-top: 10px;
  font-size: 15px;
  gap: 12px;
}
.total-row span {
  flex-shrink: 0;
}
.total-value {
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  color: #b45309;
  padding: 0;
  overflow: hidden;
  white-space: nowrap;
  max-width: 100%;
  text-align: right;
}
.total-value:hover {
  text-decoration: underline;
}
.error-msg {
  color: #dc2626;
  font-size: 13px;
}
.btn-primary {
  background: #111827;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 9px 16px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  width: 100%;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
