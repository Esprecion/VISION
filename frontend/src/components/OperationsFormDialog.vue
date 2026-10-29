<template>
  <Dialog
    v-model="show"
    :options="{ title: (editName ? 'Edit ' : 'New ') + label, size: 'lg' }"
  >
    <template #body-content>
      <div class="form-grid">
        <template v-if="kind === 'Project'">
          <AppSelect
            label="Contract *"
            v-model="form.contract"
            :options="contractOptions"
          />
          <AppTextInput label="Project type" v-model="form.project_type" placeholder="e.g. Website build" />
          <div class="two">
            <AppSelect label="Stage *" v-model="form.stage" :options="stageOptions" />
            <AppTextInput label="Committed delivery *" type="date" v-model="form.committed_date" />
          </div>
          <div class="two">
            <AppTextInput label="Start date" type="date" v-model="form.start_date" />
            <AppTextInput label="Actual delivery" type="date" v-model="form.actual_delivery_date" />
          </div>
        </template>

        <template v-else-if="kind === 'Tool'">
          <AppTextInput label="Tool name *" v-model="form.tool_name" placeholder="e.g. Figma" />
          <div class="two">
            <AppSelect label="Billing cycle *" v-model="form.billing_cycle" :options="billingOptions" />
            <AppTextInput label="Current cost *" type="number" min="0" step="0.01" v-model.number="form.current_cost" />
          </div>
          <AppTextInput label="Renewal date" type="date" v-model="form.renewal_date" />
        </template>

        <template v-else>
          <AppSelect label="Client *" v-model="form.client" :options="clientOptions" />
          <div class="two">
            <AppTextInput label="Contact date *" type="date" v-model="form.contact_date" />
            <AppSelect label="Channel *" v-model="form.channel" :options="channelOptions" />
          </div>
          <label class="notes-field">
            <span>Notes</span>
            <textarea v-model="form.notes" rows="4" placeholder="What was discussed?" />
          </label>
        </template>

        <div v-if="activeRes.error" class="error-msg" role="alert">
          <AlertCircleIcon aria-hidden="true" />
          <span>{{ errorText }}</span>
        </div>
      </div>
    </template>
    <template #actions>
      <AppButton
        variant="solid"
        theme="gray"
        class="w-full"
        :disabled="!valid"
        :loading="activeRes.loading"
        @click="submit"
      >
        {{ editName ? 'Update' : 'Save' }} {{ label }}
      </AppButton>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Dialog, createResource, call } from 'frappe-ui'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import { formatLocalDate } from '@/utils/dateRange'

const props = defineProps({
  modelValue: Boolean,
  kind: { type: String, default: 'Project' },
  editName: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue', 'created'])

const DOCTYPES = {
  Project: 'Project',
  Tool: 'Tool Subscription',
  Engagement: 'Client Engagement Log',
}
const LABELS = { Project: 'Project', Tool: 'Tool', Engagement: 'Engagement Log' }
const doctype = computed(() => DOCTYPES[props.kind] || 'Project')
const label = computed(() => LABELS[props.kind] || 'record')

const show = ref(props.modelValue)
watch(() => props.modelValue, (value) => (show.value = value))
watch(show, async (value) => {
  emit('update:modelValue', value)
  if (!value) return
  Object.assign(form, blank())
  loaded.value = null
  if (props.editName) await loadForEdit()
})

const stageOptions = ['Kickoff', 'Development', 'Testing', 'Deployed'].map((value) => ({
  label: value,
  value,
}))
const billingOptions = ['Monthly', 'Annual'].map((value) => ({ label: value, value }))
const channelOptions = ['Email', 'Call', 'Meeting', 'Chat'].map((value) => ({ label: value, value }))

const contracts = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Service Contract',
    fields: ['name', 'client', 'deal'],
    limit_page_length: 500,
    order_by: 'modified desc',
  },
  auto: true,
})
const deals = createResource({
  url: 'frappe.client.get_list',
  params: { doctype: 'Deal', fields: ['name', 'deal_title'], limit_page_length: 500 },
  auto: true,
})
const clients = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Client',
    fields: ['name', 'client_name'],
    limit_page_length: 500,
    order_by: 'client_name asc',
  },
  auto: true,
})

const contractOptions = computed(() => [
  { label: 'Select contract', value: '' },
  ...((contracts.data || []).map((contract) => {
    const deal = (deals.data || []).find((row) => row.name === contract.deal)
    return {
      label: `${deal?.deal_title || contract.deal || contract.name}${contract.client ? ' · ' + contract.client : ''}`,
      value: contract.name,
    }
  })),
])
const clientOptions = computed(() => [
  { label: 'Select client', value: '' },
  ...((clients.data || []).map((client) => ({
    label: client.client_name || client.name,
    value: client.name,
  }))),
])

function blank() {
  const today = formatLocalDate(new Date())
  if (props.kind === 'Tool') {
    return {
      tool_name: '',
      billing_cycle: 'Monthly',
      current_cost: 0,
      renewal_date: '',
    }
  }
  if (props.kind === 'Engagement') {
    return { client: '', contact_date: today, channel: 'Email', notes: '' }
  }
  return {
    contract: '',
    project_type: '',
    stage: 'Kickoff',
    start_date: '',
    committed_date: '',
    actual_delivery_date: '',
  }
}
const form = reactive(blank())

const valid = computed(() => {
  if (props.kind === 'Project') {
    return !!form.contract && !!form.stage && !!form.committed_date
  }
  if (props.kind === 'Tool') {
    return !!form.tool_name.trim() && !!form.billing_cycle && Number(form.current_cost) >= 0
  }
  return !!form.client && !!form.contact_date && !!form.channel
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
    const doc = await call('frappe.client.get', { doctype: doctype.value, name: props.editName })
    loaded.value = doc
    if (props.kind === 'Project') {
      Object.assign(form, {
        contract: doc.contract || '',
        project_type: doc.project_type || '',
        stage: doc.stage || 'Kickoff',
        start_date: doc.start_date || '',
        committed_date: doc.committed_date || '',
        actual_delivery_date: doc.actual_delivery_date || '',
      })
    } else if (props.kind === 'Tool') {
      Object.assign(form, {
        tool_name: doc.tool_name || '',
        billing_cycle: doc.billing_cycle || 'Monthly',
        current_cost: Number(doc.current_cost || 0),
        renewal_date: doc.renewal_date || '',
      })
    } else {
      Object.assign(form, {
        client: doc.client || '',
        contact_date: doc.contact_date || '',
        channel: doc.channel || 'Email',
        notes: doc.notes || '',
      })
    }
  } catch (error) {
    saveDoc.error = error
  }
}

function submit() {
  const editing = !!props.editName
  if (editing && !loaded.value) return
  const doc = editing ? { ...loaded.value } : { doctype: doctype.value }
  for (const [key, value] of Object.entries(form)) {
    if (editing) doc[key] = value === '' ? null : value
    else if (value !== '' && value !== null) doc[key] = value
  }
  if (props.kind === 'Tool') doc.current_cost = Number(form.current_cost) || 0
  ;(editing ? saveDoc : createDoc).submit(
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
.form-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.notes-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  font-size: var(--fs-xs);
  font-weight: 500;
  color: var(--color-gray-600);
}
.notes-field textarea {
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font: inherit;
  color: var(--color-gray-900);
  resize: vertical;
}
.notes-field textarea:focus {
  outline: 2px solid var(--color-amber-300);
  outline-offset: 1px;
}
.error-msg {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  color: var(--color-red-600);
  font-size: var(--fs-sm);
}
.error-msg svg {
  width: 16px;
  height: 16px;
  flex: none;
  margin-top: 2px;
}
.w-full {
  width: 100%;
}
@media (max-width: 640px) {
  .two {
    grid-template-columns: 1fr;
  }
}
</style>
