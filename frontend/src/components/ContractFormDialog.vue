<template>
  <Dialog v-model="show" :options="{ title: 'Add Contract', size: 'lg' }">
    <template #body-content>
      <div class="form-grid">
        <div class="field">
          <label>Won Deal *</label>
          <Autocomplete
            :options="dealOptions"
            :model-value="form.deal"
            @update:modelValue="onDealSelect"
            placeholder="Select a Won deal..."
          />
          <div v-if="!dealOptions.length" class="hint">No Won deals available — all are either already under contract or none are Won yet.</div>
        </div>

        <div v-if="form.client" class="field">
          <label>Client</label>
          <input :value="form.client" type="text" disabled />
        </div>

        <div class="field-row">
          <div class="field">
            <label>Start Date</label>
            <input v-model="form.start_date" type="date" />
          </div>
          <div class="field">
            <label>End Date</label>
            <input v-model="form.end_date" type="date" />
          </div>
        </div>

        <div class="field">
          <label>Payment Milestones *</label>
          <div class="milestone-rows">
            <div v-for="(m, i) in milestones" :key="i" class="milestone-row">
              <input v-model="m.milestone_name" type="text" placeholder="e.g. Downpayment" class="ms-name" />
              <input v-model.number="m.amount" type="number" placeholder="Amount" class="ms-amount" />
              <button class="remove-row" @click="milestones.splice(i, 1)">×</button>
            </div>
          </div>
          <button class="btn-secondary add-row" @click="milestones.push({ milestone_name: '', amount: 0 })">
            + Add milestone
          </button>
          <div class="total-row">Total: {{ peso(totalValue) }}</div>
        </div>

        <div v-if="createContract.error" class="error-msg">
          {{ createContract.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <button
        class="btn-primary"
        :disabled="!canSubmit || createContract.loading"
        @click="submit"
      >
        {{ createContract.loading ? 'Saving...' : 'Save Contract' }}
      </button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, Autocomplete, createResource, createListResource } from 'frappe-ui'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'created'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => {
  emit('update:modelValue', v)
  if (v) {
    dealsResource.reload()
    contractsResource.reload()
  }
})

const dealsResource = createListResource({
  doctype: 'Deal',
  fields: ['name', 'deal_title', 'client'],
  filters: { stage: 'Won' },
  pageLength: 100,
  auto: true,
})

const contractsResource = createListResource({
  doctype: 'Service Contract',
  fields: ['deal'],
  pageLength: 200,
  auto: true,
})

const dealOptions = computed(() => {
  const contractedDeals = new Set((contractsResource.data || []).map((c) => c.deal))
  return (dealsResource.data || [])
    .filter((d) => !contractedDeals.has(d.name))
    .map((d) => ({ label: `${d.deal_title} — ${d.client}`, value: d.name }))
})

const form = reactive({
  deal: '',
  client: '',
  start_date: '',
  end_date: '',
})

function onDealSelect(val) {
  const dealName = val?.value ?? val ?? ''
  form.deal = dealName
  const matched = (dealsResource.data || []).find((d) => d.name === dealName)
  form.client = matched ? matched.client : ''
}

const milestones = ref([{ milestone_name: 'Downpayment', amount: 0 }])
const totalValue = computed(() => milestones.value.reduce((s, m) => s + (Number(m.amount) || 0), 0))

const canSubmit = computed(
  () => form.deal && milestones.value.length > 0 && milestones.value.every((m) => m.milestone_name.trim() && m.amount > 0)
)

const createContract = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
})

function submit() {
  createContract.submit(
    {
      doc: {
        doctype: 'Service Contract',
        deal: form.deal,
        client: form.client,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        payment_milestones: milestones.value,
      },
    },
    {
      onSuccess: (doc) => {
        emit('created', doc)
        show.value = false
        form.deal = ''
        form.client = ''
        form.start_date = ''
        form.end_date = ''
        milestones.value = [{ milestone_name: 'Downpayment', amount: 0 }]
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
}
.field input:disabled {
  background: #f3f4f6;
  color: #6b7280;
}
.field-row {
  display: flex;
  gap: 12px;
}
.field-row .field {
  flex: 1;
}
.hint {
  font-size: 12px;
  color: #9ca3af;
}
.milestone-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}
.milestone-row {
  display: grid;
  grid-template-columns: 1fr 120px 24px;
  gap: 8px;
  align-items: center;
}
.ms-name,
.ms-amount {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 7px 9px;
  font-size: 13px;
}
.remove-row {
  background: none;
  border: none;
  color: #dc2626;
  font-size: 18px;
  cursor: pointer;
  line-height: 1;
}
.add-row {
  width: fit-content;
}
.total-row {
  margin-top: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #111827;
}
.btn-secondary {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #111827;
  font-size: 13px;
  font-weight: 500;
  padding: 7px 12px;
  cursor: pointer;
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
