<script setup>
import { ref, computed } from 'vue'
import { createListResource, call } from 'frappe-ui'
import ContractFormDialog from '@/components/ContractFormDialog.vue'
import ContractDetailDialog from '@/components/ContractDetailDialog.vue'
import { useToast } from '@/composables/useToast'
import { session } from '@/data/session'
import { displayValue, formatCurrency } from '@/utils/format'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppSearchInput from '@/components/ui/AppSearchInput.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import PlusIcon from '~icons/lucide/plus'
import SearchIcon from '~icons/lucide/search'

const { showToast } = useToast()
const canWrite = computed(() => session.canWrite('Service Contract'))
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

function clearSearch() {
  search.value = ''
}
</script>

<template>
  <div class="contracts-page">
    <PageHeader title="Business Development · Contracts">
      <template v-if="canWrite" #actions>
        <button class="btn-secondary" @click="showContractDialog = true">
          <PlusIcon class="btn-icon" aria-hidden="true" />
          Add Contract
        </button>
      </template>
    </PageHeader>

    <AppSearchInput
      v-model="search"
      class="page-search"
      label="Search contracts"
      placeholder="Search by client or deal..."
    />

    <div class="table-wrap">
      <AppSkeleton v-if="contractsResource.loading && !contractsResource.data" variant="table" :rows="5" :cols="6" />
      <ErrorState
        v-else-if="contractsResource.error && !contractsResource.data"
        title="Couldn't load contracts"
        :message="contractsResource.error?.messages?.[0] || contractsResource.error?.message || ''"
        :on-retry="() => contractsResource.reload()"
      />
      <EmptyState
        v-else-if="!contractsResource.data?.length"
        title="No contracts yet"
        :description="canWrite ? 'Won deals can be turned into contracts with payment milestones.' : 'Contracts will appear here once the Business Development team creates them.'"
      >
        <template v-if="canWrite" #action>
          <button class="btn-secondary" @click="showContractDialog = true">
            <PlusIcon class="btn-icon" aria-hidden="true" />
            Add Contract
          </button>
        </template>
      </EmptyState>
      <EmptyState
        v-else-if="filteredContracts.length === 0"
        :icon="SearchIcon"
        title="No matching contracts"
        description="No contracts match your search. Try a different client or deal name."
      >
        <template #action>
          <button class="btn-secondary" @click="clearSearch">Clear search</button>
        </template>
      </EmptyState>
      <div v-else class="table-scroll">
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
            <tr
              v-for="c in filteredContracts"
              :key="c.name"
              class="clickable-row"
              tabindex="0"
              :aria-label="'Open contract for ' + dealTitle(c.deal)"
              @click="openContractDetail(c.name)"
              @keydown.enter="openContractDetail(c.name)"
              @keydown.space.prevent="openContractDetail(c.name)"
            >
              <td class="strong">{{ dealTitle(c.deal) }}</td>
              <td>{{ c.client }}</td>
              <td class="num">{{ formatCurrency(c.value) }}</td>
              <td @click.stop @keydown.stop>
                <select
                  v-if="canWrite"
                  :value="c.status"
                  class="status-select"
                  :class="statusClass(c.status)"
                  :aria-label="'Status for ' + dealTitle(c.deal)"
                  @change="updateStatus(c, $event.target.value)"
                >
                  <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
                </select>
                <StatusBadge v-else :value="c.status" />
              </td>
              <td>{{ displayValue(c.start_date) }}</td>
              <td>{{ displayValue(c.end_date) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <ContractFormDialog v-model="showContractDialog" @created="onContractCreated" />
    <ContractDetailDialog
      v-model="showContractDetail"
      :contract-name="selectedContractName"
      @updated="contractsResource.reload()"
    />
  </div>
</template>

<style scoped>
.contracts-page {
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
.page-search {
  max-width: 360px;
  margin-bottom: var(--space-4);
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
.contracts-table {
  width: 100%;
  border-collapse: collapse;
}
.contracts-table th,
.contracts-table td {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-sm);
  border-bottom: 1px solid var(--color-gray-200);
  white-space: nowrap;
}
.contracts-table th {
  color: var(--color-gray-600);
  font-weight: 600;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  background: var(--color-gray-50);
}
.contracts-table tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
.num {
  font-variant-numeric: tabular-nums;
}
.clickable-row {
  cursor: pointer;
}
.clickable-row:hover {
  background: var(--color-gray-50);
}
.status-select {
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-full);
  padding: var(--space-1) var(--space-3);
  font-size: var(--fs-xs);
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}
.status-draft {
  background: var(--color-gray-100);
  color: var(--color-gray-600);
}
.status-negotiation {
  background: var(--color-amber-100);
  color: var(--color-amber-700);
}
.status-finalized {
  background: var(--color-blue-100);
  color: var(--color-blue-700);
}
.status-sent {
  background: var(--color-emerald-100);
  color: var(--color-emerald-800);
}
@media (max-width: 640px) {
  .search-input {
    max-width: none;
  }
}
</style>
