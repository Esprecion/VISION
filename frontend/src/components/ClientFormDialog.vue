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
  gap: 12px;
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
.field input:focus {
  outline: none;
  border-color: #6366f1;
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
