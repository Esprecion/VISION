<template>
  <div class="pipeline">
    <header class="pipeline-header">
      <h1>Business Development · Pipeline</h1>
      <div class="header-actions">
        <div class="period-picker">
          <select v-model.number="selectedQuarter">
            <option :value="1">Q1</option>
            <option :value="2">Q2</option>
            <option :value="3">Q3</option>
            <option :value="4">Q4</option>
          </select>
          <select v-model.number="selectedYear">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <span class="range-label">{{ rangeLabel }}</span>
        <div class="manage-dropdown">
          <button class="btn-secondary" @click.stop="showManageMenu = !showManageMenu">⚙ Manage ▾</button>
          <div v-if="showManageMenu" class="manage-menu">
            <button @click="showClientDialog = true; showManageMenu = false">+ Add Client</button>
            <button @click="showProductDialog = true; showManageMenu = false">+ Add Product</button>
            <button @click="showManageStages = true; showManageMenu = false">Manage Stages</button>
          </div>
        </div>
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

    <input
      v-model="searchQuery"
      class="search-input"
      type="text"
      placeholder="Search deals by title or client..."
    />

    <div class="board-wrap">
    <div class="board" ref="boardEl">
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
              <div
                v-if="daysInStage(deal.name, deal.stage) !== null"
                class="days-badge"
                :class="stageSeverityClass(daysInStage(deal.name, deal.stage))"
              >
                {{ daysInStage(deal.name, deal.stage) }}d in stage
              </div>
            </div>
            <div class="card-dates">
              <span>Created {{ formatShortDate(deal.creation) }}</span>
              <span v-if="closedDate(deal.name, deal.stage)">
                · Closed {{ closedDate(deal.name, deal.stage) }}
              </span>
            </div>
          </div>
        </div>

        <button class="add-card-btn" @click="openAddDeal(stage.id)">+ Add deal</button>
      </div>
    </div>
      <div v-if="showScrollHint" class="scroll-hint">→</div>
    </div>

    <ClientFormDialog v-model="showClientDialog" @created="onClientCreated" />
    <ProductFormDialog v-model="showProductDialog" @created="onProductCreated" />
    <AddDealDialog v-model="showDealDialog" :stage="dealDialogStage" @created="onDealCreated" />
    <DealDetailDialog v-model="showDealDetail" :deal-name="selectedDealName" @updated="dealsResource.reload(); stageLogsResource.reload()" />
    <ManageStagesDialog v-model="showManageStages" @updated="stagesResource.reload(); dealsResource.reload()" />
    <ToastContainer />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { createListResource, createResource } from 'frappe-ui'
import ClientFormDialog from '@/components/ClientFormDialog.vue'
import ProductFormDialog from '@/components/ProductFormDialog.vue'
import AddDealDialog from '@/components/AddDealDialog.vue'
import DealDetailDialog from '@/components/DealDetailDialog.vue'
import ManageStagesDialog from '@/components/ManageStagesDialog.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()
const showClientDialog = ref(false)
const showProductDialog = ref(false)
const showManageStages = ref(false)
const showManageMenu = ref(false)
function closeManageMenu() {
  showManageMenu.value = false
}
onMounted(() => window.addEventListener('click', closeManageMenu))
onUnmounted(() => window.removeEventListener('click', closeManageMenu))

function onClientCreated(doc) {
  showToast(`Client "${doc.client_name}" added`)
}

function onProductCreated(doc) {
  showToast(`Product "${doc.product_name}" added`)
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
  stageLogsResource.reload()
  showToast(`Deal "${doc.deal_title}" added`)
}

const stagesResource = createListResource({
  doctype: 'Pipeline Stage',
  fields: ['name', 'stage_name', 'color', 'is_locked', 'sequence'],
  orderBy: 'sequence asc',
  pageLength: 100,
  auto: true,
})

const stages = computed(() =>
  (stagesResource.data || []).map((s) => ({
    id: s.stage_name,
    name: s.stage_name,
    color: s.color || '#9ca3af',
    isLocked: !!s.is_locked,
  }))
)

const dealsResource = createListResource({
  doctype: 'Deal',
  fields: ['name', 'deal_title', 'client', 'stage', 'value', 'creation'],
  orderBy: 'modified desc',
  pageLength: 100,
  auto: true,
})

const stageLogsResource = createListResource({
  doctype: 'Stage Log',
  fields: ['deal', 'to_stage', 'changed_on'],
  orderBy: 'changed_on desc',
  pageLength: 500,
  auto: true,
})

function daysInStage(dealName, currentStage) {
  const logs = stageLogsResource.data || []
  const latest = logs.find((l) => l.deal === dealName && l.to_stage === currentStage)
  if (!latest) return null
  const diffMs = Date.now() - new Date(latest.changed_on).getTime()
  return Math.max(0, Math.floor(diffMs / 86400000))
}

function stageSeverityClass(days) {
  if (days >= 10) return 'severity-danger'
  if (days >= 5) return 'severity-warning'
  return ''
}

const boardEl = ref(null)
const showScrollHint = ref(false)
function checkOverflow() {
  if (boardEl.value) {
    showScrollHint.value = boardEl.value.scrollWidth > boardEl.value.clientWidth + 4
  }
}
onMounted(() => {
  checkOverflow()
  window.addEventListener('resize', checkOverflow)
})
onUnmounted(() => window.removeEventListener('resize', checkOverflow))
watch(() => dealsResource.data, () => nextTick(checkOverflow))
watch(stages, () => nextTick(checkOverflow))

function formatShortDate(isoStr) {
  if (!isoStr) return null
  const d = new Date(isoStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function closedDate(dealName, currentStage) {
  if (currentStage !== 'Won' && currentStage !== 'Lost') return null
  const logs = stageLogsResource.data || []
  const entry = logs.find((l) => l.deal === dealName && l.to_stage === currentStage)
  return entry ? formatShortDate(entry.changed_on) : null
}

const draggedDealName = ref(null)
const dragOverStage = ref(null)

const searchQuery = ref('')

function dealsByStage(stageId) {
  const list = (dealsResource.data || []).filter((d) => d.stage === stageId)
  if (!searchQuery.value.trim()) return list
  const q = searchQuery.value.toLowerCase()
  return list.filter(
    (d) =>
      (d.deal_title || '').toLowerCase().includes(q) ||
      (d.client || '').toLowerCase().includes(q)
  )
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
        onSuccess: () => {
          stageLogsResource.reload()
        },
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
const today = new Date()
const selectedQuarter = ref(Math.ceil((today.getMonth() + 1) / 3))
const selectedYear = ref(today.getFullYear())
const yearOptions = computed(() => {
  const y = today.getFullYear()
  return [y - 2, y - 1, y, y + 1]
})
const quarterRanges = {
  1: ['01-01', '03-31'],
  2: ['04-01', '06-30'],
  3: ['07-01', '09-30'],
  4: ['10-01', '12-31'],
}
const fromDate = computed(() => `${selectedYear.value}-${quarterRanges[selectedQuarter.value][0]}`)
const toDate = computed(() => `${selectedYear.value}-${quarterRanges[selectedQuarter.value][1]}T23:59:59`)
function formatDisplayDate(isoStr) {
  const d = new Date(isoStr + (isoStr.includes('T') ? '' : 'T00:00:00'))
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
const rangeLabel = computed(
  () => `${formatDisplayDate(fromDate.value)} – ${formatDisplayDate(toDate.value)}, ${selectedYear.value}`
)

const wonValue = computed(() => {
  const deals = dealsResource.data || []
  const logs = stageLogsResource.data || []
  const fromMs = new Date(fromDate.value).getTime()
  const toMs = new Date(toDate.value).getTime()
  return deals
    .filter((d) => {
      if (d.stage !== 'Won') return false
      const latestWon = logs.find((l) => l.deal === d.name && l.to_stage === 'Won')
      if (!latestWon) return false
      const t = new Date(latestWon.changed_on).getTime()
      return t >= fromMs && t <= toMs
    })
    .reduce((s, d) => s + (d.value || 0), 0)
})
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
.card-dates {
  font-size: 10px;
  color: #9ca3af;
  margin-top: 4px;
}
.manage-dropdown {
  position: relative;
}
.manage-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  min-width: 160px;
  z-index: 20;
  overflow: hidden;
}
.manage-menu button {
  background: none;
  border: none;
  text-align: left;
  padding: 10px 14px;
  font-size: 13px;
  color: #111827;
  cursor: pointer;
}
.manage-menu button:hover {
  background: #f9fafb;
}
.period-picker {
  display: flex;
  gap: 6px;
}
.period-picker select {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 13px;
  background: #ffffff;
  color: #111827;
}
.range-label {
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
}
.days-badge {
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 999px;
}
.days-badge.severity-warning {
  background: #fef3c7;
  color: #b45309;
}
.days-badge.severity-danger {
  background: #fee2e2;
  color: #dc2626;
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
.board-wrap {
  position: relative;
}
.scroll-hint {
  position: absolute;
  right: 0;
  top: 45%;
  background: linear-gradient(to right, transparent, #f9fafb 60%);
  padding: 8px 10px 8px 24px;
  color: #b45309;
  font-weight: 700;
  pointer-events: none;
}
</style>
