<template>
  <Dialog v-model="show" :options="{ title: 'Add Client' }">
    <template #body-content>
      <div class="form-grid">
        <div class="field">
          <label>Client Name *</label>
          <input v-model="form.client_name" type="text" placeholder="e.g. Acme Corp" />
        </div>
        <div class="field">
          <label>Address</label>
          <input v-model="form.address" type="text" />
        </div>
        <div class="field">
          <label>Contact Person</label>
          <input v-model="form.contact_person" type="text" />
        </div>
        <div class="field">
          <label>Contact Email</label>
          <input v-model="form.contact_email" type="email" />
        </div>
        <div class="field">
          <label>Contact Phone</label>
          <input v-model="form.contact_phone" type="text" />
        </div>
        <div class="field">
          <label>Territory</label>
          <input v-model="form.territory" type="text" placeholder="e.g. Metro Manila" />
        </div>
        <div v-if="createClient.error" class="error-msg">
          <AlertCircleIcon class="btn-icon" aria-hidden="true" />
          {{ createClient.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <button class="btn-primary" :disabled="!form.client_name || createClient.loading" @click="submit">
        {{ createClient.loading ? 'Saving...' : 'Save Client' }}
      </button>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Dialog, createResource } from 'frappe-ui'
import AlertCircleIcon from '~icons/lucide/alert-circle'

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => emit('update:modelValue', v))

const form = reactive({
  client_name: '',
  address: '',
  contact_person: '',
  contact_email: '',
  contact_phone: '',
  territory: '',
})

const createClient = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
})

function submit() {
  createClient.submit(
    {
      doc: {
        doctype: 'Client',
        ...form,
      },
    },
    {
      onSuccess: (doc) => {
        emit('created', doc)
        show.value = false
        Object.keys(form).forEach((k) => (form[k] = ''))
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
.field input {
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  font-size: var(--fs-sm);
  font-family: inherit;
  color: var(--color-gray-900);
}
.field input:focus {
  border-color: var(--color-amber-700);
}
.error-msg {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-red-600);
  font-size: var(--fs-sm);
}
.btn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
.btn-primary { width: 100%; }
</style>
