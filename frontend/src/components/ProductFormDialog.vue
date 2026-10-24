<template>
  <Dialog v-model="show" :options="{ title: 'Add Product' }">
    <template #body-content>
      <div class="form-grid">
        <AppTextInput v-model="form.product_name" label="Product Name" required placeholder="e.g. Clinic Software License" />
        <AppSelect v-model="form.type" label="Type" required :options="typeOptions" placeholder="Select type" />
        <AppTextInput v-model="form.description" label="Description" type="text" />
        <div v-if="createProduct.error" class="error-msg">
          <AlertCircleIcon class="btn-icon" aria-hidden="true" />
          {{ createProduct.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <AppButton
        variant="solid"
        theme="gray"
        :disabled="!form.product_name || !form.type || createProduct.loading"
        :loading="createProduct.loading"
        @click="submit"
      >
        Save Product
      </AppButton>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Dialog, createResource } from 'frappe-ui'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'

const props = defineProps({
  modelValue: Boolean,
})
const emit = defineEmits(['update:modelValue', 'created'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => emit('update:modelValue', v))

const form = reactive({
  product_name: '',
  type: '',
  description: '',
})

const typeOptions = [
  { label: 'Software', value: 'Software' },
  { label: 'Hardware', value: 'Hardware' },
  { label: 'Consulting', value: 'Consulting' },
  { label: 'Support', value: 'Support' },
]

const createProduct = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
})

function submit() {
  createProduct.submit(
    {
      doc: {
        doctype: 'Product',
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
