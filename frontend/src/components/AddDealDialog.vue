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
          <div class="label-row">
            <label>Client *</label>
            <button class="btn-link" @click="newClient = !newClient">
              {{ newClient ? 'Pick existing client' : '+ New client' }}
            </button>
          </div>
          <Autocomplete
            v-if="!newClient"
            :options="clientOptions"
            :model-value="form.client"
            @update:modelValue="(val) => (form.client = val?.value ?? val ?? '')"
            placeholder="Search clients..."
          />
          <div v-else class="new-box">
            <input v-model="clientForm.client_name" type="text" placeholder="Client name *" />
            <input v-model="clientForm.contact_person" type="text" placeholder="Contact person" />
            <input v-model="clientForm.contact_email" type="email" placeholder="Contact email" />
            <input v-model="clientForm.contact_phone" type="text" placeholder="Contact phone" />
            <input v-model="clientForm.territory" type="text" placeholder="Territory" />
            <input v-model="clientForm.address" type="text" placeholder="Address" />
          </div>
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
                    v-if="!item.isNew"
                    :options="productOptions"
                    :model-value="item.product"
                    @update:modelValue="(val) => (item.product = val?.value ?? val ?? '')"
                    placeholder="Select product"
                  />
                  <div v-else class="new-product">
                    <input v-model="item.newName" type="text" placeholder="New product name *" />
                    <select v-model="item.newType">
                      <option value="">Type *</option>
                      <option v-for="t in productTypes" :key="t" :value="t">{{ t }}</option>
                    </select>
                  </div>
                  <button class="btn-link small" @click="item.isNew = !item.isNew">
                    {{ item.isNew ? 'Pick existing' : '+ New product' }}
                  </button>
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
    clientsResource.reload()
    productsResource.reload()
  }
})

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

const productTypes = ['Software', 'Hardware', 'Consulting', 'Support']
const newClient = ref(false)
const clientForm = reactive({
  client_name: '', contact_person: '', contact_email: '',
  contact_phone: '', territory: '', address: '',
})

const form = reactive({
  deal_title: '',
  client: '',
  expected_close_date: '',
})

const blankItem = () => ({ product: '', isNew: false, newName: '', newType: '', quantity: 1, price: 0 })
const items = ref([blankItem()])
const expandedRows = reactive({})
const totalExpanded = ref(false)

const MAX_PESO_DIGITS = 12
const AMOUNT_TRUNCATE_LEN = 14

function addItem() {
  items.value.push(blankItem())
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
  items.value.filter(
    (i) =>
      (i.isNew ? i.newName.trim() && i.newType : i.product) &&
      Number(i.quantity) > 0 &&
      Number(i.price) >= 0
  )
)

const clientOk = computed(() =>
  newClient.value ? !!clientForm.client_name.trim() : !!form.client
)
const canSubmit = computed(
  () => form.deal_title && clientOk.value && validItems.value.length > 0
)

const createDeal = createResource({
  url: 'my_custom_app.api.create_deal_with_details',
  method: 'POST',
})

function resetForm() {
  form.deal_title = ''
  form.client = ''
  form.expected_close_date = ''
  Object.keys(clientForm).forEach((k) => (clientForm[k] = ''))
  newClient.value = false
  items.value = [blankItem()]
}

function submit() {
  createDeal.submit(
    {
      deal: {
        deal_title: form.deal_title,
        stage: props.stage,
        expected_close_date: form.expected_close_date || null,
      },
      client: newClient.value ? { new: { ...clientForm } } : { existing: form.client },
      items: validItems.value.map((i) => ({
        ...(i.isNew
          ? { new_product: { product_name: i.newName, type: i.newType } }
          : { product: i.product }),
        quantity: i.quantity,
        price: i.price,
      })),
    },
    {
      onSuccess: (doc) => {
        emit('created', doc)
        show.value = false
        resetForm()
        clientsResource.reload()
        productsResource.reload()
      },
    }
  )
}

function peso(n) {
  return '₱' + Number(n || 0).toLocaleString('en-PH')
}
</script>

<style scoped>
.form-grid { display: flex; flex-direction: column; gap: 14px; }
.stage-badge {
  font-size: 13px; color: #6b7280; background: #fef3c7;
  border-radius: 6px; padding: 6px 10px; width: fit-content;
}
.stage-badge strong { color: #b45309; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 13px; color: #4b5563; font-weight: 500; }
.field input {
  border: 1px solid #d1d5db; border-radius: 6px; padding: 8px 10px;
  font-size: 14px; font-family: inherit;
}
.field input:focus { outline: none; border-color: #6366f1; }
.label-row { display: flex; justify-content: space-between; align-items: center; }
.new-box { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.new-box input, .new-product input, .new-product select {
  border: 1px solid #d1d5db; border-radius: 6px; padding: 6px 8px;
  font-size: 13px; font-family: inherit; width: 100%; box-sizing: border-box;
}
.new-product { display: flex; flex-direction: column; gap: 4px; }
.items-table-wrap { overflow-x: auto; margin-top: 4px; }
.items-table { display: flex; flex-direction: column; gap: 6px; min-width: 480px; }
.items-head, .items-row {
  display: grid; grid-template-columns: 210px 56px 84px 84px 20px;
  gap: 8px; align-items: center;
}
.items-head { font-size: 11px; color: #9ca3af; font-weight: 500; text-transform: uppercase; }
.product-cell { width: 210px; overflow: hidden; }
.items-row input {
  width: 100%; box-sizing: border-box; border: 1px solid #d1d5db;
  border-radius: 6px; padding: 6px 8px; font-size: 13px; font-family: inherit;
}
.row-amount {
  background: transparent; border: none; font-size: 13px; font-weight: 600;
  color: #111827; padding: 0; text-align: left; cursor: pointer;
  white-space: nowrap; overflow: hidden; max-width: 100%;
}
.row-amount:hover { color: #b45309; }
.remove-row {
  background: transparent; border: none; color: #9ca3af;
  font-size: 16px; cursor: pointer; padding: 0;
}
.remove-row:hover { color: #dc2626; }
.btn-link {
  background: transparent; border: none; color: #6366f1; font-size: 13px;
  font-weight: 500; cursor: pointer; padding: 0; text-align: left; width: fit-content;
}
.btn-link.small { font-size: 11px; }
.total-row {
  display: flex; justify-content: space-between; align-items: center;
  border-top: 1px solid #e5e7eb; padding-top: 10px; font-size: 15px; gap: 12px;
}
.total-row span { flex-shrink: 0; }
.total-value {
  background: transparent; border: none; cursor: pointer;
  font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #b45309;
  padding: 0; overflow: hidden; white-space: nowrap; max-width: 100%; text-align: right;
}
.total-value:hover { text-decoration: underline; }
.error-msg { color: #dc2626; font-size: 13px; }
.btn-primary {
  background: #111827; color: #ffffff; border: none; border-radius: 6px;
  padding: 9px 16px; font-weight: 600; font-size: 14px; cursor: pointer; width: 100%;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
