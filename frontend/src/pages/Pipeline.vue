<template>
  <div class="pipeline">
    <header class="pipeline-header">
      <h1>Business Dev · Pipeline</h1>
      <div class="header-actions">
        <button class="btn-secondary" @click="showClientDialog = true">+ Add Client</button>
        <button class="btn-secondary" @click="showProductDialog = true">+ Add Product</button>
        <RouterLink to="/business-dev/overview" class="dash-link">← Overview</RouterLink>
      </div>
    </header>

    <div class="summary-row">
      <div class="summary-item hero">
        <div class="label">Total pipeline value</div>
        <div class="value">{{ peso(totalValue) }}</div>
      </div>
      <div class="summary-item">
        <div class="label">Won this period</div>
        <div class="value">{{ peso(wonValue) }}</div>
      </div>
      <div class="summary-item">
        <div class="label">Active deals</div>
        <div class="value">{{ activeCount }}</div>
      </div>
    </div>

    <div class="board">
      <div
        v-for="stage in stages"
        :key="stage.id"
        class="column"
        :class="{ 'drag-over': dragOverStage === stage.id }"
        @dragover.prevent="dragOverStage = stage.id"
        @dragleave="dragOverStage = null"
        @drop="onDrop(stage.id)"
      >
        <div class="col-head">
          <div class="col-title-row">
            <span class="dot" :style="{ background: stage.color }"></span>
            <span class="col-title">{{ stage.name }}</span>
            <span class="col-count">{{ dealsByStage(stage.id).length }}</span>
          </div>
          <div class="col-total">{{ stageTotal(stage.id) }}</div>
        </div>

        <div class="cards">
          <div
            v-for="deal in dealsByStage(stage.id)"
            :key="deal.name"
            class="card"
            :style="{ '--stage-color': stage.color }"
            draggable="true"
            @dragstart="draggedDealName = deal.name"
            @click="openDealDetail(deal.name)"
          >
            <div class="org">{{ deal.deal_title }}</div>
            <div class="value">{{ peso(deal.value) }}</div>
            <div class="card-foot">
              <div class="owner">{{ deal.client }}</div>
            </div>
          </div>
        </div>

        <button class="add-card-btn" @click="openAddDeal(stage.id)">+ Add deal</button>
      </div>
    </div>

    <ClientFormDialog v-model="showClientDialog" @created="onClientCreated" />
    <ProductFormDialog v-model="showProductDialog" @created="onProductCreated" />
    <AddDealDialog v-model="showDealDialog" :stage="dealDialogStage" @created="onDealCreated" />
    <DealDetailDialog v-model="showDealDetail" :deal-name="selectedDealName" @updated="dealsResource.reload()" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createListResource, createResource } from 'frappe-ui'
import ClientFormDialog from '@/components/ClientFormDialog.vue'
import ProductFormDialog from '@/components/ProductFormDialog.vue'
import AddDealDialog from '@/components/AddDealDialog.vue'
import DealDetailDialog from '@/components/DealDetailDialog.vue'

const showClientDialog = ref(false)
const showProductDialog = ref(false)

function onClientCreated(doc) {
  console.log('Client created:', doc.name)
}

function onProductCreated(doc) {
  console.log('Product created:', doc.name)
}

const showDealDialog = ref(false)
const dealDialogStage = ref('')

const showDealDetail = ref(false)
const selectedDealName = ref('')

function openDealDetail(dealName) {
  selectedDealName.value = dealName
  showDealDetail.value = true
}

function openAddDeal(stageId) {
  dealDialogStage.value = stageId
  showDealDialog.value = true
}

function onDealCreated(doc) {
  dealsResource.reload()
}

const stages = [
  { id: 'Lead', name: 'Lead', color: '#4c8dff' },
  { id: 'Qualified', name: 'Qualified', color: '#37c9a6' },
  { id: 'Proposal', name: 'Proposal', color: '#e0a93e' },
  { id: 'Negotiation', name: 'Negotiation', color: '#9d7bff' },
  { id: 'Won', name: 'Won', color: '#3fbf7f' },
  { id: 'Lost', name: 'Lost', color: '#e5636b' },
]

const dealsResource = createListResource({
  doctype: 'Deal',
  fields: ['name', 'deal_title', 'client', 'stage', 'value'],
  orderBy: 'modified desc',
  pageLength: 100,
  auto: true,
})

const draggedDealName = ref(null)
const dragOverStage = ref(null)

function dealsByStage(stageId) {
  return (dealsResource.data || []).filter((d) => d.stage === stageId)
}

function stageTotal(stageId) {
  return peso(dealsByStage(stageId).reduce((sum, d) => sum + (d.value || 0), 0))
}

const updateStage = createResource({
  url: 'frappe.client.set_value',
  method: 'POST',
})

function onDrop(stageId) {
  dragOverStage.value = null
  const deal = (dealsResource.data || []).find((d) => d.name === draggedDealName.value)
  if (deal && deal.stage !== stageId) {
    const previousStage = deal.stage
    deal.stage = stageId
    updateStage.submit(
      {
        doctype: 'Deal',
        name: deal.name,
        fieldname: 'stage',
        value: stageId,
      },
      {
        onError: () => {
          deal.stage = previousStage
        },
      }
    )
  }
  draggedDealName.value = null
}

const totalValue = computed(() =>
  (dealsResource.data || []).reduce((s, d) => s + (d.value || 0), 0)
)
const wonValue = computed(() =>
  (dealsResource.data || [])
    .filter((d) => d.stage === 'Won')
    .reduce((s, d) => s + (d.value || 0), 0)
)
const activeCount = computed(
  () =>
    (dealsResource.data || []).filter((d) => d.stage !== 'Won' && d.stage !== 'Lost')
      .length
)

function peso(n) {
  return '₱' + Number(n || 0).toLocaleString('en-PH')
}
</script>

<style scoped>
.pipeline {
  background: #f9fafb;
  min-height: 100vh;
  padding: 32px;
  color: #111827;
  font-family: 'Inter', sans-serif;
}
.pipeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.pipeline-header h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #111827;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.btn-secondary {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #111827;
  font-size: 13px;
  font-weight: 500;
  padding: 7px 14px;
  cursor: pointer;
}
.btn-secondary:hover {
  border-color: #b45309;
  color: #b45309;
}
.dash-link {
  color: #6b7280;
  text-decoration: none;
  font-size: 13px;
}
.dash-link:hover {
  color: #b45309;
}
.summary-row {
  display: flex;
  gap: 28px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.summary-item .label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  margin-bottom: 4px;
}
.summary-item .value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #111827;
}
.summary-item.hero .value {
  color: #b45309;
  font-size: 28px;
}
.board {
  display: flex;
  gap: 16px;
  overflow-x: auto;
}
.column {
  width: 260px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}
.column.drag-over {
  border-color: #b45309;
  background: #fffbeb;
}
.col-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.col-title {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
  color: #111827;
}
.col-count {
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  border-radius: 999px;
  padding: 1px 7px;
}
.col-total {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}
.cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 30px;
}
.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-left: 3px solid var(--stage-color, #b45309);
  border-radius: 10px;
  padding: 12px 13px;
  cursor: grab;
}
.card:hover {
  background: #f9fafb;
}
.card .org {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #111827;
}
.card .value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  margin-bottom: 8px;
  color: #111827;
}
.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card .owner {
  font-size: 11px;
  color: #6b7280;
}
.add-card-btn {
  background: transparent;
  border: 1px dashed #d1d5db;
  border-radius: 10px;
  color: #9ca3af;
  font-size: 12px;
  font-weight: 500;
  padding: 9px;
  cursor: pointer;
  text-align: left;
}
.add-card-btn:hover {
  color: #6b7280;
  border-color: #9ca3af;
}
</style>
