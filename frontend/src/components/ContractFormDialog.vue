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

        <AppTextInput v-if="form.client" label="Client" :model-value="form.client" disabled />

        <div v-if="form.deal" class="value-box">
          Project value: <b>{{ dealValue > 0 ? peso(dealValue) : 'not set on this deal' }}</b>
        </div>

        <div class="field-row">
          <AppTextInput label="Start Date" type="date" v-model="form.start_date" />
          <AppTextInput label="End Date" type="date" v-model="form.end_date" />
        </div>

        <div class="field">
          <label>Payment Milestones *</label>
          <AppSelect
            v-if="dealValue > 0"
            v-model="templateChoice"
            :options="[{ label: 'Fill from template...', value: '' }, ...TEMPLATES.map((t, i) => ({ label: t.label, value: String(i) }))]"
            @update:model-value="applyTemplate($event)"
            class="tpl"
          />
          <div class="milestone-rows">
            <div v-for="(m, i) in milestones" :key="i" class="milestone-row">
              <AppTextInput v-model="m.milestone_name" placeholder="e.g. Downpayment" class="ms-name" />
              <AppTextInput v-model.number="m.amount" type="number" placeholder="Amount" class="ms-amount" />
              <AppButton variant="ghost" size="sm" :icon="XIcon" @click="milestones.splice(i, 1)" aria-label="Remove milestone" />
            </div>
          </div>
          <AppButton variant="outline" size="sm" class="add-row" @click="milestones.push({ milestone_name: '', amount: 0 })">
            <template #prefix><PlusIcon aria-hidden="true" /></template>
            Add milestone
          </AppButton>
          <div class="total-row">Total: {{ peso(totalValue) }}</div>
          <div v-if="dealValue > 0" class="balance" :class="{ ok: matches, bad: !matches }">
            Milestones {{ peso(totalValue) }} of {{ peso(dealValue) }}:
            {{ matches ? 'fully allocated' : (remaining > 0 ? peso(remaining) + ' left to allocate' : peso(-remaining) + ' over the deal value') }}
          </div>
        </div>

        <div class="field">
          <label>Terms and conditions</label>
          <textarea v-model="form.terms_and_conditions" rows="3" placeholder="e.g. Late payments accrue 2% per month. Work starts after the downpayment clears."></textarea>
        </div>

        <div v-if="createContract.error" class="error-msg">
          <AlertCircleIcon class="btn-icon" aria-hidden="true" />
          {{ createContract.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <AppButton variant="solid" theme="gray" class="w-full" :disabled="!canSubmit" :loading="createContract.loading" @click="submit">
        Save Contract
      </AppButton>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, Autocomplete, createResource, createListResource, call } from 'frappe-ui'
import XIcon from '~icons/lucide/x'
import PlusIcon from '~icons/lucide/plus'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppSelect from '@/components/ui/AppSelect.vue'

const props = defineProps({
  modelValue: Boolean,
  prefillDealName: String,
  prefillClientName: String,
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => {
  emit('update:modelValue', v)
  if (v) {
    dealsResource.reload()
    contractsResource.reload()
    if (props.prefillDealName) {
      form.deal = props.prefillDealName
      form.client = props.prefillClientName || ''
    }
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
  terms_and_conditions: '',
})

function onDealSelect(val) {
  const dealName = val?.value ?? val ?? ''
  form.deal = dealName
  const matched = (dealsResource.data || []).find((d) => d.name === dealName)
  form.client = matched ? matched.client : ''
}

const milestones = ref([{ milestone_name: 'Downpayment', amount: 0 }])
const totalValue = computed(() => milestones.value.reduce((s, m) => s + (Number(m.amount) || 0), 0))

// Real deal value, read from the database (Deal.value, or the sum of its items)
const dealValue = ref(0)
watch(() => form.deal, async (d) => {
  dealValue.value = 0
  if (!d) return
  try {
    const doc = await call('frappe.client.get', { doctype: 'Deal', name: d })
    const fromItems = (doc.items || []).reduce((s, i) => s + (Number(i.amount) || 0), 0)
    dealValue.value = Number(doc.value) || fromItems
  } catch (e) {
    dealValue.value = 0
  }
}, { immediate: true })

const remaining = computed(() => Math.round((dealValue.value - totalValue.value) * 100) / 100)
const matches = computed(() => dealValue.value <= 0 || Math.abs(remaining.value) < 0.01)

const TEMPLATES = [
  { label: '30 / 40 / 30', parts: [['Downpayment', 30], ['Progress payment', 40], ['Final payment', 30]] },
  { label: '40 / 30 / 30', parts: [['Downpayment', 40], ['Progress payment', 30], ['Final payment', 30]] },
  { label: '50 / 50', parts: [['Downpayment', 50], ['Final payment', 50]] },
  { label: '100% upfront', parts: [['Full payment', 100]] },
]
const templateChoice = ref('')
function applyTemplate(i) {
  templateChoice.value = ''
  const t = TEMPLATES[Number(i)]
  if (!t || dealValue.value <= 0) return
  let used = 0
  milestones.value = t.parts.map(([name, pct], idx) => {
    const last = idx === t.parts.length - 1
    const amount = last ? Math.round((dealValue.value - used) * 100) / 100 : Math.round(dealValue.value * pct) / 100
    used += amount
    return { milestone_name: name, amount }
  })
}

const canSubmit = computed(
  () => form.deal && milestones.value.length > 0 && milestones.value.every((m) => m.milestone_name.trim() && m.amount > 0) && matches.value
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
        terms_and_conditions: form.terms_and_conditions || '',
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
        form.terms_and_conditions = ''
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
  gap: var(--space-4);
}
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.field label {
  font-size: var(--fs-sm);
  color: var(--color-gray-600);
  font-weight: 500;
}
.field textarea {
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  font-size: var(--fs-sm);
  font-family: inherit;
  color: var(--color-gray-900);
  background: var(--color-white);
}
.field textarea:focus {
  border-color: var(--color-amber-700);
}
.field-row {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.field-row > * {
  flex: 1;
  min-width: 160px;
}
.hint {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
}
.milestone-rows {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}
.milestone-row {
  display: grid;
  grid-template-columns: 1fr 120px 28px;
  gap: var(--space-2);
  align-items: center;
}
.add-row {
  width: fit-content;
}
.total-row {
  margin-top: var(--space-2);
  font-weight: 600;
  font-size: var(--fs-sm);
  color: var(--color-gray-900);
  font-variant-numeric: tabular-nums;
}

.error-msg {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-red-600);
  font-size: var(--fs-sm);
}
.w-full { width: 100%; }
.value-box {
  background: var(--color-amber-50); border: 1px solid var(--color-amber-200);
  border-radius: var(--radius-md); padding: var(--space-3); font-size: var(--fs-sm);
  color: var(--color-amber-800);
}
.tpl {
  width: fit-content;
  margin-bottom: var(--space-2);
}
.balance { font-size: var(--fs-sm); margin-top: var(--space-1); font-variant-numeric: tabular-nums; }
.balance.ok { color: var(--color-emerald-800); }
.balance.bad { color: var(--color-red-700); }
</style>
