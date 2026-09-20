<!--
  Pipeline.vue

  Business Dev Kanban board — mock data for now, since the Deal doctype
  doesn't exist in my_custom_app yet. Once it does, swap MOCK_DEALS for
  a createListResource call against your own Deal doctype and wire the
  drag-drop handler to update the deal's status via frappe-ui.

  Drop into: src/pages/
  Register route: { path: '/business-dev-pipeline', name: 'Pipeline',
                     component: () => import('@/pages/Pipeline.vue') }
-->
<template>
  <div class="pipeline">
    <header class="pipeline-header">
      <h1>Business Dev · Pipeline</h1>
      <RouterLink to="/business-dev" class="dash-link">← Dashboard</RouterLink>
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
            :key="deal.id"
            class="card"
            :style="{ '--stage-color': stage.color }"
            draggable="true"
            @dragstart="draggedDealId = deal.id"
          >
            <div class="org">{{ deal.org }}</div>
            <div class="value">{{ peso(deal.value) }}</div>
            <div class="card-foot">
              <div class="owner">{{ deal.owner }}</div>
              <div class="age" :class="{ stale: deal.days >= 14 }">
                {{ deal.days }}d in stage
              </div>
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

const stages = [
  { id: 'lead', name: 'Demo/Making', color: '#4c8dff' },
  { id: 'prop', name: 'Proposal/Quotation', color: '#e0a93e' },
  { id: 'neg', name: 'Negotiation', color: '#9d7bff' },
  { id: 'ready', name: 'Ready to Close', color: '#37c9a6' },
  { id: 'won', name: 'Won', color: '#3fbf7f' },
  { id: 'lost', name: 'Lost', color: '#e5636b' },
]

const deals = ref([
  { id: 1, org: 'Acme Corp', value: 5000000, owner: 'SC', stage: 'lead', days: 2 },
  { id: 2, org: 'Forge Digital', value: 4000000, owner: 'SC', stage: 'lost', days: 30 },
  { id: 3, org: 'Meridian Systems', value: 25000000, owner: 'SC', stage: 'won', days: 18 },
  { id: 4, org: 'PivotTech Solutions', value: 6000000, owner: 'SC', stage: 'neg', days: 9 },
  { id: 5, org: 'ScaleUp Labs', value: 1200000, owner: 'SC', stage: 'ready', days: 4 },
  { id: 6, org: 'TechStart Inc', value: 500000, owner: 'SC', stage: 'prop', days: 14 },
  { id: 7, org: 'Vertex Analytics', value: 9000000, owner: 'JP', stage: 'lost', days: 22 },
])

const draggedDealId = ref(null)
const dragOverStage = ref(null)

function dealsByStage(stageId) {
  return deals.value.filter((d) => d.stage === stageId)
}

function stageTotal(stageId) {
  return peso(dealsByStage(stageId).reduce((sum, d) => sum + d.value, 0))
}

function onDrop(stageId) {
  dragOverStage.value = null
  const deal = deals.value.find((d) => d.id === draggedDealId.value)
  if (deal) {
    deal.stage = stageId
    deal.days = 0
  }
  draggedDealId.value = null
}

const totalValue = computed(() => deals.value.reduce((s, d) => s + d.value, 0))
const wonValue = computed(() =>
  deals.value.filter((d) => d.stage === 'won').reduce((s, d) => s + d.value, 0)
)
const activeCount = computed(
  () => deals.value.filter((d) => d.stage !== 'won' && d.stage !== 'lost').length
)

function peso(n) {
  return '₱' + Number(n).toLocaleString('en-PH')
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
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2a3556;
  color: #7c87a3;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  font-weight: 700;
}
.card .age {
  font-size: 11px;
  color: #4e5876;
}
.card .age.stale {
  color: #e5636b;
  font-weight: 600;
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
