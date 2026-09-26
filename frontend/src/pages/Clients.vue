<script setup>
import { ref, computed } from 'vue'
import { createListResource } from 'frappe-ui'
import ClientFormDialog from '@/components/ClientFormDialog.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import { useToast } from '@/composables/useToast'

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
</script>

<template>
  <div class="clients-page">
    <header class="clients-header">
      <h1>Business Development · Clients</h1>
      <button class="btn-secondary" @click="showClientDialog = true">+ Add Client</button>
    </header>

    <input
      v-model="search"
      class="search-input"
      type="text"
      placeholder="Search by name, contact, or territory..."
    />

    <div class="table-wrap">
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
          <tr v-if="!clientsResource.loading && filteredClients.length === 0">
            <td colspan="5" class="empty-row">No clients found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ClientFormDialog v-model="showClientDialog" @created="onClientCreated" />
    <ToastContainer />
  </div>
</template>

<style scoped>
.clients-page {
  background: #f9fafb;
  min-height: 100vh;
  padding: 32px;
  color: #111827;
  font-family: 'Inter', sans-serif;
}
.clients-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.clients-header h1 {
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
.clients-table {
  width: 100%;
  border-collapse: collapse;
}
.clients-table th,
.clients-table td {
  text-align: left;
  padding: 10px 16px;
  font-size: 14px;
  border-bottom: 1px solid #e5e7eb;
}
.clients-table th {
  color: #6b7280;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  background: #f9fafb;
}
.clients-table tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
.empty-row {
  text-align: center;
  color: #6b7280;
  padding: 24px;
}
</style>
