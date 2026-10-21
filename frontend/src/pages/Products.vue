<script setup>
import { ref, computed } from 'vue'
import { createListResource } from 'frappe-ui'
import ProductFormDialog from '@/components/ProductFormDialog.vue'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import PlusIcon from '~icons/lucide/plus'
import SearchIcon from '~icons/lucide/search'

const { showToast } = useToast()
const showProductDialog = ref(false)
const search = ref('')

const productsResource = createListResource({
  doctype: 'Product',
  fields: ['name', 'product_name', 'type', 'description'],
  orderBy: 'product_name asc',
  pageLength: 200,
  auto: true,
})

function onProductCreated(doc) {
  productsResource.reload()
  showToast(`Product "${doc.product_name}" added`)
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

function clearSearch() {
  search.value = ''
}
</script>

<template>
  <div class="products-page">
    <PageHeader title="Business Development · Products">
      <template #actions>
        <button class="btn-secondary" @click="showProductDialog = true">
          <PlusIcon class="btn-icon" aria-hidden="true" />
          Add Product
        </button>
      </template>
    </PageHeader>

    <div class="search-wrap">
      <SearchIcon class="search-icon" aria-hidden="true" />
      <input
        v-model="search"
        class="search-input"
        type="search"
        placeholder="Search by name or type..."
      />
    </div>

    <div class="table-wrap">
      <AppSkeleton v-if="productsResource.loading && !productsResource.data" variant="table" :rows="6" :cols="3" />
      <ErrorState
        v-else-if="productsResource.error && !productsResource.data"
        title="Couldn't load products"
        :message="productsResource.error?.messages?.[0] || productsResource.error?.message || ''"
        :on-retry="() => productsResource.reload()"
      />
      <EmptyState
        v-else-if="!productsResource.data?.length"
        title="No products yet"
        description="Add your first product so deals can reference it in line items."
      >
        <template #action>
          <button class="btn-secondary" @click="showProductDialog = true">
            <PlusIcon class="btn-icon" aria-hidden="true" />
            Add Product
          </button>
        </template>
      </EmptyState>
      <EmptyState
        v-else-if="filteredProducts.length === 0"
        :icon="SearchIcon"
        title="No matching products"
        description="No products match your search. Try a different name or type."
      >
        <template #action>
          <button class="btn-secondary" @click="clearSearch">Clear search</button>
        </template>
      </EmptyState>
      <div v-else class="table-scroll">
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
              <td class="description-cell">{{ p.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ProductFormDialog v-model="showProductDialog" @created="onProductCreated" />
  </div>
</template>

<style scoped>
.products-page {
  background: var(--color-gray-50);
  min-height: 100vh;
  padding: var(--page-pad);
  color: var(--color-gray-900);
}
.btn-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}
.search-wrap {
  position: relative;
  margin-bottom: var(--space-4);
}
.search-icon {
  position: absolute;
  left: var(--space-3);
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--color-gray-500);
  pointer-events: none;
}
.search-input {
  width: 100%;
  max-width: 360px;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3) var(--space-2) 36px;
  font-size: var(--fs-sm);
  margin-bottom: var(--space-4);
  background: var(--color-white);
  font-family: inherit;
  color: var(--color-gray-900);
  box-sizing: border-box;
}
.table-wrap {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.table-scroll {
  overflow-x: auto;
}
.products-table {
  width: 100%;
  border-collapse: collapse;
}
.products-table th,
.products-table td {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-sm);
  border-bottom: 1px solid var(--color-gray-200);
}
.products-table th {
  color: var(--color-gray-600);
  font-weight: 600;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  background: var(--color-gray-50);
  white-space: nowrap;
}
.products-table tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
.description-cell {
  min-width: 260px;
}
.type-badge {
  display: inline-block;
  background: var(--color-amber-100);
  color: var(--color-amber-700);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--fs-xs);
  font-weight: 600;
  white-space: nowrap;
}
@media (max-width: 640px) {
  .search-input {
    max-width: none;
  }
}
</style>
