<template>
  <div class="pipeline">
    <header class="pipeline-header">
      <h1>Business Dev · Pipeline</h1>
      <RouterLink to="/business-dev/dashboard" class="dash-link">← Dashboard</RouterLink>
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
          >
            <div class="org">{{ deal.deal_title }}</div>
            <div class="value">{{ peso(deal.value) }}</div>
            <div class="card-foot">
              <div class="owner">{{ deal.client }}</div>
            </div>
          </div>
        </div>

        <button class="add-card-btn">+ Add deal</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createListResource, createResource } from 'frappe-ui'

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
    deal.stage = stageId // optimistic update
    updateStage.submit(
      {
        doctype: 'Deal',
        name: deal.name,
        fieldname: 'stage',
        value: stageId,
      },
      {
        onError: () => {
          deal.stage = previousStage // revert on failure
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
  background: radial-gradient(1200px 600px at 10% -10%, #101b33 0%, #0a0f1d 55%);
  min-height: 100vh;
  padding: 32px;
  color: #edeff5;
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
}
.dash-link {
  color: #7c87a3;
  text-decoration: none;
  font-size: 13px;
}
.dash-link:hover {
  color: #c9a227;
}
.summary-row {
  display: flex;
  gap: 28px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.summary-item .label {
  font-size: 12px;
  color: #7c87a3;
  font-weight: 500;
  margin-bottom: 4px;
}
.summary-item .value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.summary-item.hero .value {
  color: #c9a227;
  font-size: 28px;
}
.board {
  display: flex;
  gap: 16px;
  overflow-x: auto;
}
.column {
  width: 260px;
  background: #101728;
  border: 1px solid #1a2338;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}
.column.drag-over {
  border-color: #c9a227;
  background: #131c33;
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
}
.col-count {
  font-size: 11px;
  color: #4e5876;
  background: #1a2338;
  border-radius: 999px;
  padding: 1px 7px;
}
.col-total {
  font-size: 13px;
  font-weight: 600;
  color: #7c87a3;
  font-variant-numeric: tabular-nums;
}
.cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 30px;
}
.card {
  background: #16203a;
  border: 1px solid #232d47;
  border-left: 3px solid var(--stage-color, #c9a227);
  border-radius: 10px;
  padding: 12px 13px;
  cursor: grab;
}
.card:hover {
  background: #1b274a;
}
.card .org {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}
.card .value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  margin-bottom: 8px;
}
.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card .owner {
  font-size: 11px;
  color: #7c87a3;
}
.add-card-btn {
  background: transparent;
  border: 1px dashed #232d47;
  border-radius: 10px;
  color: #4e5876;
  font-size: 12px;
  font-weight: 500;
  padding: 9px;
  cursor: pointer;
  text-align: left;
}
.add-card-btn:hover {
  color: #7c87a3;
  border-color: #4e5876;
}
</style>
