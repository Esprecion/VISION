<script setup>
import { ref, computed } from 'vue'
import { createListResource } from 'frappe-ui'
import ProductFormDialog from '@/components/ProductFormDialog.vue'

const showProductDialog = ref(false)
const search = ref('')

const productsResource = createListResource({
  doctype: 'Product',
  fields: ['name', 'product_name', 'type', 'description'],
  orderBy: 'product_name asc',
  pageLength: 200,
  auto: true,
})

function onProductCreated() {
  productsResource.reload()
}

const filteredProducts = computed(() => {
  const list = productsResource.data || []
  if (!search.value.trim()) return list
  const q = search.value.toLowerCase()
  return list.filter(
    (p) =>
      (p.product_name || '').toLowerCase().includes(q) ||
      (p.type || '').toLowerCase().includes(q)
  )
})
</script>

<template>
  <div class="products-page">
    <header class="products-header">
      <h1>Business Dev · Products</h1>
      <button class="btn-secondary" @click="showProductDialog = true">+ Add Product</button>
    </header>

    <input
      v-model="search"
      class="search-input"
      type="text"
      placeholder="Search by name or type..."
    />

    <div class="table-wrap">
      <table class="products-table">
        <thead>
          <tr>
            <th>Product Name</th>
            <th>Type</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filteredProducts" :key="p.name">
            <td class="strong">{{ p.product_name }}</td>
            <td><span class="type-badge">{{ p.type || '—' }}</span></td>
            <td>{{ p.description || '—' }}</td>
          </tr>
          <tr v-if="!productsResource.loading && filteredProducts.length === 0">
            <td colspan="3" class="empty-row">No products found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ProductFormDialog v-model="showProductDialog" @created="onProductCreated" />
  </div>
</template>

<style scoped>
.products-page {
  background: #f9fafb;
  min-height: 100vh;
  padding: 32px;
  color: #111827;
  font-family: 'Inter', sans-serif;
}
.products-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.products-header h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #111827;
}
.btn-secondary {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #111827;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 14px;
  cursor: pointer;
}
.search-input {
  width: 100%;
  max-width: 360px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  margin-bottom: 16px;
  background: #ffffff;
}
.table-wrap {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.products-table {
  width: 100%;
  border-collapse: collapse;
}
.products-table th,
.products-table td {
  text-align: left;
  padding: 10px 16px;
  font-size: 14px;
  border-bottom: 1px solid #e5e7eb;
}
.products-table th {
  color: #6b7280;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  background: #f9fafb;
}
.products-table tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
.type-badge {
  background: #fef3c7;
  color: #b45309;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.empty-row {
  text-align: center;
  color: #6b7280;
  padding: 24px;
}
</style>
