<script setup>
import { ref, computed } from 'vue'
import { createListResource } from 'frappe-ui'
import ClientFormDialog from '@/components/ClientFormDialog.vue'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import PlusIcon from '~icons/lucide/plus'
import SearchIcon from '~icons/lucide/search'

const { showToast } = useToast()
const showClientDialog = ref(false)
const search = ref('')

const clientsResource = createListResource({
  doctype: 'Client',
  fields: ['name', 'client_name', 'contact_person', 'contact_email', 'contact_phone', 'territory'],
  orderBy: 'client_name asc',
  pageLength: 200,
  auto: true,
})

function onClientCreated(doc) {
  clientsResource.reload()
  showToast(`Client "${doc.client_name}" added`)
}

const filteredClients = computed(() => {
  const list = clientsResource.data || []
  if (!search.value.trim()) return list
  const q = search.value.toLowerCase()
  return list.filter(
    (c) =>
      (c.client_name || '').toLowerCase().includes(q) ||
      (c.contact_person || '').toLowerCase().includes(q) ||
      (c.territory || '').toLowerCase().includes(q)
  )
})

function clearSearch() {
  search.value = ''
}
</script>

<template>
  <div class="clients-page">
    <PageHeader title="Business Development · Clients">
      <template #actions>
        <button class="btn-secondary" @click="showClientDialog = true">
          <PlusIcon class="btn-icon" aria-hidden="true" />
          Add Client
        </button>
      </template>
    </PageHeader>

    <div class="search-wrap">
      <SearchIcon class="search-icon" aria-hidden="true" />
      <input
        v-model="search"
        class="search-input"
        type="search"
        placeholder="Search by name, contact, or territory..."
      />
    </div>

    <div class="table-wrap">
      <AppSkeleton v-if="clientsResource.loading && !clientsResource.data" variant="table" :rows="6" :cols="5" />
      <ErrorState
        v-else-if="clientsResource.error && !clientsResource.data"
        title="Couldn't load clients"
        :message="clientsResource.error?.messages?.[0] || clientsResource.error?.message || ''"
        :on-retry="() => clientsResource.reload()"
      />
      <EmptyState
        v-else-if="!clientsResource.data?.length"
        title="No clients yet"
        description="Add your first client to start tracking contacts and territory."
      >
        <template #action>
          <button class="btn-secondary" @click="showClientDialog = true">
            <PlusIcon class="btn-icon" aria-hidden="true" />
            Add Client
          </button>
        </template>
      </EmptyState>
      <EmptyState
        v-else-if="filteredClients.length === 0"
        :icon="SearchIcon"
        title="No matching clients"
        description="No clients match your search. Try a different name, contact, or territory."
      >
        <template #action>
          <button class="btn-secondary" @click="clearSearch">Clear search</button>
        </template>
      </EmptyState>
      <div v-else class="table-scroll">
        <table class="clients-table">
          <thead>
            <tr>
              <th>Client Name</th>
              <th>Contact Person</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Territory</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in filteredClients" :key="c.name">
              <td class="strong">{{ c.client_name }}</td>
              <td>{{ c.contact_person || '—' }}</td>
              <td>{{ c.contact_email || '—' }}</td>
              <td>{{ c.contact_phone || '—' }}</td>
              <td>{{ c.territory || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ClientFormDialog v-model="showClientDialog" @created="onClientCreated" />
  </div>
</template>

<style scoped>
.clients-page {
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
.clients-table {
  width: 100%;
  border-collapse: collapse;
}
.clients-table th,
.clients-table td {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-sm);
  border-bottom: 1px solid var(--color-gray-200);
  white-space: nowrap;
}
.clients-table th {
  color: var(--color-gray-600);
  font-weight: 600;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  background: var(--color-gray-50);
}
.clients-table tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
@media (max-width: 640px) {
  .search-input {
    max-width: none;
  }
}
</style>
