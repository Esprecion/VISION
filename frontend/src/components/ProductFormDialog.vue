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
.field input,
.field select,
.field textarea {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 14px;
  font-family: inherit;
}
.field input:focus,
.field select:focus,
.field textarea:focus {
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
