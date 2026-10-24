<template>
  <Dialog v-model="show" :options="{ title: 'Add Client' }">
    <template #body-content>
      <div class="form-grid">
        <AppTextInput v-model="form.client_name" label="Client Name" required placeholder="e.g. Acme Corp" />
        <AppTextInput v-model="form.address" label="Address" />
        <AppTextInput v-model="form.contact_person" label="Contact Person" />
        <AppTextInput v-model="form.contact_email" type="email" label="Contact Email" />
        <AppTextInput v-model="form.contact_phone" label="Contact Phone" />
        <AppTextInput v-model="form.territory" label="Territory" placeholder="e.g. Metro Manila" />
        <div v-if="createClient.error" class="error-msg">
          <AlertCircleIcon class="btn-icon" aria-hidden="true" />
          {{ createClient.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <AppButton
        variant="solid"
        theme="gray"
        :disabled="!form.client_name || createClient.loading"
        :loading="createClient.loading"
        @click="submit"
      >
        Save Client
      </AppButton>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Dialog, createResource } from 'frappe-ui'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppButton from '@/components/ui/AppButton.vue'

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
</style>
