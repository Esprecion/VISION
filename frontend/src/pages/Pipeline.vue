<template>
  <div class="pipeline">
    <PageHeader title="Business Development · Pipeline">
      <template #actions>
        <div class="period-picker">
          <input type="date" class="date-input" v-model="fromInput" :max="toInput" aria-label="From date" />
          <span class="range-label">to</span>
          <input type="date" class="date-input" v-model="toInput" :min="fromInput" aria-label="To date" />
          <button class="btn-secondary" @click="setRange(quarterRange(0))">This quarter</button>
          <button class="btn-secondary" @click="setRange(quarterRange(-1))">Last quarter</button>
          <button class="btn-secondary" @click="setRange(yearRange())">This year</button>
        </div>
        <div class="manage-dropdown">
          <button
            class="btn-secondary manage-trigger"
            :aria-expanded="showManageMenu"
            @click.stop="showManageMenu = !showManageMenu"
          >
            <SettingsIcon class="btn-icon" aria-hidden="true" />
            Manage
            <ChevronDownIcon class="btn-icon btn-chevron" :class="{ 'btn-chevron--open': showManageMenu }" aria-hidden="true" />
          </button>
          <div v-if="showManageMenu" class="manage-menu">
            <button @click="showClientDialog = true; showManageMenu = false">
              <PlusIcon class="btn-icon" aria-hidden="true" />
              Add Client
            </button>
            <button @click="showProductDialog = true; showManageMenu = false">
              <PlusIcon class="btn-icon" aria-hidden="true" />
              Add Product
            </button>
            <button @click="showManageStages = true; showManageMenu = false">
              <SettingsIcon class="btn-icon" aria-hidden="true" />
              Manage Stages
            </button>
          </div>
        </div>
      </template>
    </PageHeader>

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

    <div class="search-wrap">
      <SearchIcon class="search-icon" aria-hidden="true" />
      <input
        v-model="searchQuery"
        class="search-input"
        type="search"
        placeholder="Search deals by title or client..."
      />
    </div>

    <div class="board-wrap">
      <ErrorState
        v-if="boardError"
        title="Couldn't load the pipeline"
        :message="dealsResource.error?.messages?.[0] || dealsResource.error?.message || ''"
        :on-retry="retryBoard"
      />
      <EmptyState
        v-else-if="!boardLoading && dealsCount === 0"
        title="No deals yet"
        description="Add your first deal to a stage to start building the pipeline."
      >
        <template #action>
          <AppButton :disabled="!stages.length" @click="addFirstDeal">
            <template #prefix><PlusIcon aria-hidden="true" /></template>
            Add deal
          </AppButton>
        </template>
      </EmptyState>
      <EmptyState
        v-else-if="searchActive"
        :icon="SearchIcon"
        title="No matching deals"
        description="No deals match your search. Try a different title or client name."
      >
        <template #action>
          <AppButton @click="clearSearch">Clear search</AppButton>
        </template>
      </EmptyState>
      <div v-else class="board" ref="boardEl">
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
            <div class="col-total">
              {{ stageTotal(stage.id) }}
              <span v-if="stage.isLocked" class="period-note">in this period</span>
            </div>
          </div>

          <div class="cards">
            <template v-if="boardLoading">
              <AppSkeleton variant="card" class="deal-skeleton" />
              <AppSkeleton variant="card" class="deal-skeleton" />
            </template>
            <template v-else>
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
            </template>
          </div>

          <button v-if="!boardLoading" class="add-card-btn" @click="openAddDeal(stage.id)">
            <PlusIcon class="btn-icon" aria-hidden="true" />
            Add deal
          </button>
        </div>
      </div>
      <div v-if="showScrollHint" class="scroll-hint">
        <ArrowRightIcon aria-hidden="true" />
      </div>
    </div>

    <ClientFormDialog v-model="showClientDialog" @created="onClientCreated" />
    <ProductFormDialog v-model="showProductDialog" @created="onProductCreated" />
    <AddDealDialog v-model="showDealDialog" :stage="dealDialogStage" @created="onDealCreated" />
    <DealDetailDialog v-model="showDealDetail" :deal-name="selectedDealName" @updated="dealsResource.reload(); stageLogsResource.reload()" />
    <ManageStagesDialog v-model="showManageStages" @updated="stagesResource.reload(); dealsResource.reload()" />
    <ContractFormDialog
      v-model="showContractSuggestDialog"
      :prefill-deal-name="suggestDealName"
      :prefill-client-name="suggestClientName"
      @created="showToast('Contract created')"
    />
  </div>
</template>

<script setup>
import { parseLocal, startOfDayMs, endOfDayMs, quarterRange, yearRange } from "../utils/dateRange"
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { createListResource, createResource } from 'frappe-ui'
import ClientFormDialog from '@/components/ClientFormDialog.vue'
import ProductFormDialog from '@/components/ProductFormDialog.vue'
import AddDealDialog from '@/components/AddDealDialog.vue'
import DealDetailDialog from '@/components/DealDetailDialog.vue'
import ManageStagesDialog from '@/components/ManageStagesDialog.vue'
import ContractFormDialog from '@/components/ContractFormDialog.vue'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import AppButton from '@/components/ui/AppButton.vue'
import SettingsIcon from '~icons/lucide/settings'
import ChevronDownIcon from '~icons/lucide/chevron-down'
import PlusIcon from '~icons/lucide/plus'
import SearchIcon from '~icons/lucide/search'
import ArrowRightIcon from '~icons/lucide/arrow-right'

const { showToast } = useToast()
const showClientDialog = ref(false)
const showProductDialog = ref(false)
const showManageStages = ref(false)
const showContractSuggestDialog = ref(false)
const suggestDealName = ref('')
const suggestClientName = ref('')
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
    color: s.color || 'var(--color-gray-400)',
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

const boardLoading = computed(
  () =>
    (stagesResource.loading && !stagesResource.data) ||
    (dealsResource.loading && !dealsResource.data)
)
const boardError = computed(() => dealsResource.error && !dealsResource.data)
const dealsCount = computed(() => (dealsResource.data || []).length)

function retryBoard() {
  stagesResource.reload()
  dealsResource.reload()
  stageLogsResource.reload()
}

function addFirstDeal() {
  if (stages.value.length) openAddDeal(stages.value[0].id)
}

function clearSearch() {
  searchQuery.value = ''
}

function daysInStage(dealName, currentStage) {
  const logs = stageLogsResource.data || []
  const latest = logs.find((l) => l.deal === dealName && l.to_stage === currentStage)
  if (!latest) return null
  const diffMs = Date.now() - parseLocal(latest.changed_on).getTime()
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
  const d = parseLocal(isoStr)
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

const searchActive = computed(() => {
  if (!searchQuery.value.trim()) return false
  return stages.value.every((s) => dealsByStage(s.id).length === 0)
})

function dealsByStage(stageId) {
  let list = (dealsResource.data || []).filter((d) => d.stage === stageId)

  const stageObj = stages.value.find((s) => s.id === stageId)
  if (stageObj?.isLocked) {
    const logs = stageLogsResource.data || []
    const fromMs = startOfDayMs(fromDate.value)
    const toMs = endOfDayMs(toDate.value)
    list = list.filter((d) => {
      const latest = logs.find((l) => l.deal === d.name && l.to_stage === stageId)
      if (!latest) return false
      const t = parseLocal(latest.changed_on).getTime()
      return t >= fromMs && t <= toMs
    })
  }

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
          if (stageId === 'Won') {
            showToast(`"${deal.deal_title}" marked Won`, 'success', {
              label: 'Create Contract',
              onClick: () => {
                suggestDealName.value = deal.name
                suggestClientName.value = deal.client
                showContractSuggestDialog.value = true
              },
            })
          }
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
  stages.value.reduce((s, stage) => s + dealsByStage(stage.id).reduce((sum, d) => sum + (d.value || 0), 0), 0)
)
const initialRange = quarterRange(0)
const fromInput = ref(initialRange.from)
const toInput = ref(initialRange.to)
const fromDate = computed(() => fromInput.value || '1970-01-01')
const toDate = computed(() => `${toInput.value || '2100-12-31'}T23:59:59`)
function setRange(r) {
  fromInput.value = r.from
  toInput.value = r.to
}

const wonValue = computed(() => {
  const deals = dealsResource.data || []
  const logs = stageLogsResource.data || []
  const fromMs = startOfDayMs(fromDate.value)
  const toMs = endOfDayMs(toDate.value)
  return deals
    .filter((d) => {
      if (d.stage !== 'Won') return false
      const latestWon = logs.find((l) => l.deal === d.name && l.to_stage === 'Won')
      if (!latestWon) return false
      const t = parseLocal(latestWon.changed_on).getTime()
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
.period-picker .btn-secondary:hover:not(:disabled) {
  border-color: var(--color-amber-700);
}
.btn-chevron {
  transition: transform 150ms ease;
}
.btn-chevron--open {
  transform: rotate(180deg);
}
.manage-trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}
.summary-row {
  display: flex;
  gap: var(--space-6);
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
}
.summary-item .label {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  font-weight: 500;
  margin-bottom: var(--space-1);
}
.summary-item .value {
  font-size: var(--fs-lg);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-gray-900);
}
.summary-item.hero .value {
  color: var(--color-gray-900);
  font-size: var(--fs-xl);
}
.board {
  display: flex;
  gap: var(--space-4);
  overflow-x: auto;
}
.column {
  width: 260px;
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
}
.column.drag-over {
  border-color: var(--color-amber-700);
  background: var(--color-amber-50);
}
.col-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.col-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  flex: 1;
  color: var(--color-gray-900);
}
.col-count {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  background: var(--color-gray-100);
  border-radius: var(--radius-full);
  padding: 1px var(--space-2);
}
.col-total {
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--color-gray-600);
  font-variant-numeric: tabular-nums;
}
.cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-height: 30px;
}
.deal-skeleton {
  padding: var(--space-3);
  border-radius: var(--radius-md);
}
.card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-left: 3px solid var(--stage-color, var(--color-amber-700));
  border-radius: var(--radius-md);
  padding: var(--space-3);
  cursor: grab;
}
.card:hover {
  background: var(--color-gray-50);
}
.card .org {
  font-size: var(--fs-sm);
  font-weight: 600;
  margin-bottom: var(--space-1);
  color: var(--color-gray-900);
}
.card .value {
  font-size: var(--fs-md);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  margin-bottom: var(--space-2);
  color: var(--color-gray-900);
}
.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.card .owner {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
}
.add-card-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  background: transparent;
  border: 1px dashed var(--color-gray-300);
  border-radius: var(--radius-md);
  color: var(--color-gray-600);
  font-size: var(--fs-xs);
  font-weight: 500;
  padding: var(--space-2);
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.add-card-btn:hover {
  color: var(--color-amber-700);
  border-color: var(--color-amber-700);
}
.card-dates {
  font-size: var(--fs-xs);
  color: var(--color-gray-500);
  margin-top: var(--space-1);
}
.manage-dropdown {
  position: relative;
}
.manage-menu {
  position: absolute;
  top: calc(100% + var(--space-1));
  right: 0;
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  min-width: 180px;
  z-index: 20;
  overflow: hidden;
}
.manage-menu button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: none;
  border: none;
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-sm);
  color: var(--color-gray-900);
  cursor: pointer;
  font-family: inherit;
}
.manage-menu button:hover {
  background: var(--color-gray-50);
}
.period-note {
  font-size: var(--fs-xs);
  color: var(--color-gray-500);
  margin-left: var(--space-1);
}
.period-picker {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.period-picker input {
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-sm);
  padding: 6px var(--space-2);
  font-size: var(--fs-sm);
  background: var(--color-white);
  color: var(--color-gray-900);
  font-family: inherit;
}
.range-label {
  color: var(--color-gray-600);
  font-size: var(--fs-xs);
  white-space: nowrap;
}
.days-badge {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  background: var(--color-gray-100);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
}
.days-badge.severity-warning {
  background: var(--color-amber-100);
  color: var(--color-amber-700);
}
.days-badge.severity-danger {
  background: var(--color-red-100);
  color: var(--color-red-600);
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
  background: var(--color-white);
  font-family: inherit;
  color: var(--color-gray-900);
  box-sizing: border-box;
}
.board-wrap {
  position: relative;
}
.scroll-hint {
  position: absolute;
  right: 0;
  top: 45%;
  background: linear-gradient(to right, transparent, var(--color-gray-50) 60%);
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-5);
  color: var(--color-amber-700);
  font-weight: 700;
  pointer-events: none;
}
.scroll-hint svg {
  width: 20px;
  height: 20px;
}
@media (max-width: 640px) {
  .summary-row {
    gap: var(--space-4);
  }
  .search-input {
    max-width: none;
  }
}
</style>
