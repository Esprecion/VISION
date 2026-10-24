<template>
  <Dialog v-model="show" :options="{ title: 'Add Deal', size: '2xl' }">
    <template #body-content>
      <div class="form-grid">
        <div class="stage-badge">Adding to: <strong>{{ stage }}</strong></div>

        <AppTextInput label="Deal Title *" v-model="form.deal_title" placeholder="e.g. Clinic Rollout - Phase 1" />

        <div class="field">
          <div class="label-row">
            <label>Client *</label>
            <AppButton variant="ghost" size="sm" @click="newClient = !newClient">
              <template #prefix><PlusIcon v-if="!newClient" aria-hidden="true" /></template>
              <template v-if="newClient">Pick existing client</template>
              <template v-else>New client</template>
            </AppButton>
          </div>
          <Autocomplete
            v-if="!newClient"
            :options="clientOptions"
            :model-value="form.client"
            @update:modelValue="(val) => (form.client = val?.value ?? val ?? '')"
            placeholder="Search clients..."
          />
          <div v-else class="new-box">
            <AppTextInput v-model="clientForm.client_name" placeholder="Client name *" />
            <AppTextInput v-model="clientForm.contact_person" placeholder="Contact person" />
            <AppTextInput v-model="clientForm.contact_email" type="email" placeholder="Contact email" />
            <AppTextInput v-model="clientForm.contact_phone" placeholder="Contact phone" />
            <AppTextInput v-model="clientForm.territory" placeholder="Territory" />
            <AppTextInput v-model="clientForm.address" placeholder="Address" />
          </div>
        </div>

        <AppTextInput label="Expected Close Date" type="date" v-model="form.expected_close_date" />

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
                    <AppTextInput v-model="item.newName" placeholder="New product name *" />
                    <AppSelect v-model="item.newType" :options="[{ label: 'Type *', value: '' }, ...productTypes.map(t => ({ label: t, value: t }))]" />
                  </div>
                  <AppButton variant="ghost" size="sm" @click="item.isNew = !item.isNew">
                    <template #prefix><PlusIcon v-if="!item.isNew" aria-hidden="true" /></template>
                    <template v-if="item.isNew">Pick existing</template>
                    <template v-else>New product</template>
                  </AppButton>
                </div>
                <AppTextInput v-model.number="item.quantity" type="number" min="0" />
                <AppTextInput v-model.number="item.price" type="number" min="0" step="0.01" @input="clampPrice(item)" />
                <button
                  class="row-amount"
                  :title="peso(rowAmount(item))"
                  @click="toggleRowExpanded(idx)"
                >
                  {{ displayAmount(peso(rowAmount(item)), expandedRows[idx]) }}
                </button>
                <AppButton variant="ghost" size="sm" :icon="XIcon" @click="removeItem(idx)" aria-label="Remove line" />
              </div>
            </div>
          </div>
          <AppButton variant="ghost" size="sm" @click="addItem">
            <template #prefix><PlusIcon aria-hidden="true" /></template>
            Add line
          </AppButton>
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
          <AlertCircleIcon class="btn-icon" aria-hidden="true" />
          {{ createDeal.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <AppButton variant="solid" theme="gray" class="w-full" :disabled="!canSubmit" :loading="createDeal.loading" @click="submit">
        Save Deal
      </AppButton>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, Autocomplete, createResource, createListResource } from 'frappe-ui'
import PlusIcon from '~icons/lucide/plus'
import XIcon from '~icons/lucide/x'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'

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
.form-grid { display: flex; flex-direction: column; gap: var(--space-4); }
.stage-badge {
  font-size: var(--fs-sm); color: var(--color-amber-700); background: var(--color-amber-100);
  border-radius: var(--radius-sm); padding: var(--space-2) var(--space-3); width: fit-content;
}
.stage-badge strong { color: var(--color-amber-800); }
.field { display: flex; flex-direction: column; gap: var(--space-1); }
.field label { font-size: var(--fs-sm); color: var(--color-gray-600); font-weight: 500; }
.label-row { display: flex; justify-content: space-between; align-items: center; gap: var(--space-3); }
.new-box { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2); }
.new-product { display: flex; flex-direction: column; gap: var(--space-1); }
.items-table-wrap { overflow-x: auto; margin-top: var(--space-1); }
.items-table { display: flex; flex-direction: column; gap: var(--space-2); min-width: 480px; }
.items-head, .items-row {
  display: grid; grid-template-columns: 210px 56px 84px 84px 24px;
  gap: var(--space-2); align-items: center;
}
.items-head { font-size: var(--fs-xs); color: var(--color-gray-600); font-weight: 500; text-transform: uppercase; }
.product-cell { width: 210px; overflow: hidden; }
.row-amount {
  background: transparent; border: none; font-size: var(--fs-sm); font-weight: 600;
  color: var(--color-gray-900); padding: 0; text-align: left; cursor: pointer;
  white-space: nowrap; overflow: hidden; max-width: 100%; font-family: inherit;
}
.row-amount:hover { color: var(--color-amber-700); }
.total-row {
  display: flex; justify-content: space-between; align-items: center;
  border-top: 1px solid var(--color-gray-200); padding-top: var(--space-3); font-size: var(--fs-md); gap: var(--space-3);
}
.total-row span { flex-shrink: 0; }
.total-value {
  background: transparent; border: none; cursor: pointer;
  font-weight: 700; color: var(--color-amber-700); font-family: inherit;
  padding: 0; overflow: hidden; white-space: nowrap; max-width: 100%; text-align: right;
}
.total-value:hover { text-decoration: underline; }
.error-msg { display: flex; align-items: center; gap: var(--space-1); color: var(--color-red-600); font-size: var(--fs-sm); }
.w-full { width: 100%; }
@media (max-width: 640px) {
  .new-box { grid-template-columns: 1fr; }
}
</style>
