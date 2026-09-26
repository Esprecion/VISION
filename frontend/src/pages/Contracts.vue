<script setup>
import { ref, computed } from 'vue'
import { createListResource, call } from 'frappe-ui'
import ContractFormDialog from '@/components/ContractFormDialog.vue'
import ContractDetailDialog from '@/components/ContractDetailDialog.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()
const showContractDialog = ref(false)
const showContractDetail = ref(false)
const selectedContractName = ref('')

function openContractDetail(name) {
  selectedContractName.value = name
  showContractDetail.value = true
}
const search = ref('')

const contractsResource = createListResource({
  doctype: 'Service Contract',
  fields: ['name', 'deal', 'client', 'value', 'status', 'start_date', 'end_date'],
  orderBy: 'modified desc',
  pageLength: 200,
  auto: true,
})

const dealTitles = createListResource({
  doctype: 'Deal',
  fields: ['name', 'deal_title'],
  pageLength: 500,
  auto: true,
})

function dealTitle(dealName) {
  const d = (dealTitles.data || []).find((x) => x.name === dealName)
  return d ? d.deal_title : dealName
}

function onContractCreated(doc) {
  contractsResource.reload()
  showToast(`Contract for "${dealTitle(doc.deal)}" added`)
}

const statusOptions = ['Draft', 'Under Negotiation', 'Finalized', 'Sent to Finance']

async function updateStatus(contract, newStatus) {
  try {
    await call('frappe.client.set_value', {
      doctype: 'Service Contract',
      name: contract.name,
      fieldname: 'status',
      value: newStatus,
    })
    contract.status = newStatus
    showToast(`Status updated to "${newStatus}"`)
  } catch (e) {
    showToast(e?.messages?.[0] || 'Failed to update status', 'error')
  }
}

function statusClass(status) {
  return {
    'status-draft': status === 'Draft',
    'status-negotiation': status === 'Under Negotiation',
    'status-finalized': status === 'Finalized',
    'status-sent': status === 'Sent to Finance',
  }
}

const filteredContracts = computed(() => {
  const list = contractsResource.data || []
  if (!search.value.trim()) return list
  const q = search.value.toLowerCase()
  return list.filter(
    (c) =>
      (c.client || '').toLowerCase().includes(q) ||
      dealTitle(c.deal).toLowerCase().includes(q)
  )
})

function peso(n) {
  return '₱' + Number(n || 0).toLocaleString('en-PH')
}
</script>

<template>
  <div class="contracts-page">
    <header class="contracts-header">
      <h1>Business Development · Contracts</h1>
      <button class="btn-secondary" @click="showContractDialog = true">+ Add Contract</button>
    </header>

    <input
      v-model="search"
      class="search-input"
      type="text"
      placeholder="Search by client or deal..."
    />

    <div class="table-wrap">
      <table class="contracts-table">
        <thead>
          <tr>
            <th>Deal</th>
            <th>Client</th>
            <th>Value</th>
            <th>Status</th>
            <th>Start</th>
            <th>End</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filteredContracts" :key="c.name" class="clickable-row" @click="openContractDetail(c.name)">
            <td class="strong">{{ dealTitle(c.deal) }}</td>
            <td>{{ c.client }}</td>
            <td>{{ peso(c.value) }}</td>
            <td>
              <select
                :value="c.status"
                class="status-select"
                :class="statusClass(c.status)"
                @click.stop
                @change="updateStatus(c, $event.target.value)"
              >
                <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
              </select>
            </td>
            <td>{{ c.start_date || '—' }}</td>
            <td>{{ c.end_date || '—' }}</td>
          </tr>
          <tr v-if="!contractsResource.loading && filteredContracts.length === 0">
            <td colspan="6" class="empty-row">No contracts found.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ContractFormDialog v-model="showContractDialog" @created="onContractCreated" />
    <ContractDetailDialog
      v-model="showContractDetail"
      :contract-name="selectedContractName"
      @updated="contractsResource.reload()"
    />
    <ToastContainer />
  </div>
</template>

<style scoped>
.contracts-page {
  background: #f9fafb;
  min-height: 100vh;
  padding: 32px;
  color: #111827;
  font-family: 'Inter', sans-serif;
}
.contracts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.contracts-header h1 {
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
.contracts-table {
  width: 100%;
  border-collapse: collapse;
}
.contracts-table th,
.contracts-table td {
  text-align: left;
  padding: 10px 16px;
  font-size: 14px;
  border-bottom: 1px solid #e5e7eb;
}
.contracts-table th {
  color: #6b7280;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  background: #f9fafb;
}
.contracts-table tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
.clickable-row {
  cursor: pointer;
}
.clickable-row:hover {
  background: #f9fafb;
}
.status-select {
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.status-draft {
  background: #f3f4f6;
  color: #6b7280;
}
.status-negotiation {
  background: #fef3c7;
  color: #b45309;
}
.status-finalized {
  background: #dbeafe;
  color: #1d4ed8;
}
.status-sent {
  background: #d1fae5;
  color: #065f46;
}
.empty-row {
  text-align: center;
  color: #6b7280;
  padding: 24px;
}
</style>
