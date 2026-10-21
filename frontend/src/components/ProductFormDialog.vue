<template>
  <Dialog v-model="show" :options="{ title: 'Add Product' }">
    <template #body-content>
      <div class="form-grid">
        <div class="field">
          <label>Product Name *</label>
          <input v-model="form.product_name" type="text" placeholder="e.g. Clinic Software License" />
        </div>
        <div class="field">
          <label>Type *</label>
          <select v-model="form.type">
            <option value="">Select type</option>
            <option value="Software">Software</option>
            <option value="Hardware">Hardware</option>
            <option value="Consulting">Consulting</option>
            <option value="Support">Support</option>
          </select>
        </div>
        <div class="field">
          <label>Description</label>
          <textarea v-model="form.description" rows="3"></textarea>
        </div>
        <div v-if="createProduct.error" class="error-msg">
          <AlertCircleIcon class="btn-icon" aria-hidden="true" />
          {{ createProduct.error.messages?.[0] || 'Something went wrong' }}
        </div>
      </div>
    </template>
    <template #actions>
      <button
        class="btn-primary"
        :disabled="!form.product_name || !form.type || createProduct.loading"
        @click="submit"
      >
        {{ createProduct.loading ? 'Saving...' : 'Save Product' }}
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
  product_name: '',
  type: '',
  description: '',
})

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
.field input,
.field select,
.field textarea {
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  font-size: var(--fs-sm);
  font-family: inherit;
  color: var(--color-gray-900);
  background: var(--color-white);
}
.field input:focus,
.field select:focus,
.field textarea:focus {
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
