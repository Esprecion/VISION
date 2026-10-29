<template>
  <div class="page">
    <PageHeader :title="title">
      <template #actions>
        <div class="head-right">
          <div class="search-wrap">
            <SearchIcon aria-hidden="true" />
            <AppTextInput
              v-model="search"
              class="search-input"
              type="search"
              :placeholder="'Search ' + title.toLowerCase() + '...'"
              :aria-label="'Search ' + title"
            />
          </div>
          <AppButton v-if="canCreate" variant="solid" theme="gray" @click="openNew">
            <template #prefix><PlusIcon aria-hidden="true" /></template>
            New {{ kindLabel }}
          </AppButton>
        </div>
      </template>
    </PageHeader>

    <div class="toolbar">
      <span>{{ rows.length }} {{ rows.length === 1 ? 'record' : 'records' }}</span>
      <AppButton v-if="search" variant="ghost" size="sm" @click="search = ''">Clear search</AppButton>
    </div>

    <div v-if="msg" class="err" role="alert">
      <AlertCircleIcon aria-hidden="true" />
      <span>{{ msg }}</span>
    </div>

    <div class="card">
      <ErrorState
        v-if="list.error"
        title="Couldn't load this list"
        :message="listError"
        :on-retry="() => list.reload()"
      />
      <AppSkeleton v-else-if="list.loading" variant="table" :rows="6" :cols="columns.length + 1" />
      <EmptyState
        v-else-if="!rows.length"
        :title="search ? 'No matches' : 'No ' + title.toLowerCase() + ' yet'"
        :description="search ? 'Try a different search term.' : 'Create your first ' + kindLabel.toLowerCase() + ' to get started.'"
      >
        <template v-if="search" #action>
          <AppButton variant="outline" size="sm" @click="search = ''">Clear search</AppButton>
        </template>
      </EmptyState>

      <template v-else>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
                <th v-if="hasActions"><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
                <td v-for="column in columns" :key="column.key">
                  <span v-if="column.type === 'status'" class="status" :class="statusClass(row[column.key])">
                    {{ display(row, column) }}
                  </span>
                  <span v-else :class="{ strong: column.key === 'name' }">{{ display(row, column) }}</span>
                </td>
                <td v-if="hasActions" class="actions">
                  <AppButton v-if="canEdit" variant="outline" size="sm" @click="openEdit(row)">Edit</AppButton>
                  <AppButton v-if="canDelete" variant="outline" size="sm" theme="red" @click="askDelete(row)">Delete</AppButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="mobile-cards">
          <article v-for="row in rows" :key="row.name" class="mobile-card">
            <div class="mobile-card__head">
              <strong>{{ display(row, columns[0]) }}</strong>
              <div v-if="hasActions" class="mobile-card__actions">
                <AppButton v-if="canEdit" variant="outline" size="sm" @click="openEdit(row)">Edit</AppButton>
                <AppButton v-if="canDelete" variant="outline" size="sm" theme="red" @click="askDelete(row)">Delete</AppButton>
              </div>
            </div>
            <dl>
              <template v-for="column in columns.slice(1)" :key="column.key">
                <dt>{{ column.label }}</dt>
                <dd>
                  <span v-if="column.type === 'status'" class="status" :class="statusClass(row[column.key])">
                    {{ display(row, column) }}
                  </span>
                  <template v-else>{{ display(row, column) }}</template>
                </dd>
              </template>
            </dl>
          </article>
        </div>
      </template>
    </div>

    <OperationsFormDialog
      v-if="canCreate"
      v-model="showForm"
      :kind="kind"
      :edit-name="editName"
      @created="onSaved"
    />
    <AppConfirmDialog
      v-model="showConfirm"
      :title="'Delete ' + kindLabel"
      :message="pendingDelete ? 'Delete ' + kindLabel + ' ' + pendingDelete.name + '? This cannot be undone.' : ''"
      confirm-label="Delete"
      destructive
      :loading="deleting"
      @confirm="doDelete"
      @cancel="pendingDelete = null"
    />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { createResource, call } from 'frappe-ui'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import OperationsFormDialog from '@/components/OperationsFormDialog.vue'
import SearchIcon from '~icons/lucide/search'
import PlusIcon from '~icons/lucide/plus'
import AlertCircleIcon from '~icons/lucide/alert-circle'

const props = defineProps({
  title: { type: String, required: true },
  doctype: { type: String, required: true },
  kind: { type: String, required: true },
  orderBy: { type: String, default: 'modified desc' },
  columns: { type: Array, required: true },
})

const KIND_LABELS = {
  Project: 'Project',
  Tool: 'Tool',
  Engagement: 'Engagement Log',
}
const kindLabel = computed(() => KIND_LABELS[props.kind] || 'Record')

const search = ref('')
const showForm = ref(false)
const editName = ref(null)
const msg = ref('')

const list = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: props.doctype,
    fields: ['name', ...props.columns.map((column) => column.key)],
    order_by: props.orderBy,
    limit_page_length: 200,
  },
  auto: true,
})

const perms = createResource({
  url: 'my_custom_app.api.get_perms',
  params: { doctype: props.doctype },
  auto: true,
})
const canCreate = computed(() => perms.data?.create === true)
const canEdit = computed(() => perms.data?.write === true)
const canDelete = computed(() => perms.data?.delete === true)
const hasActions = computed(() => canEdit.value || canDelete.value)

const rows = computed(() => {
  const query = search.value.trim().toLowerCase()
  const data = list.data || []
  if (!query) return data
  return data.filter((row) =>
    Object.values(row).some((value) => String(value ?? '').toLowerCase().includes(query))
  )
})

const listError = computed(() =>
  String(list.error?.messages?.[0] || list.error?.message || 'Something went wrong').replace(/<[^>]+>/g, '')
)

const money = (value) => '₱' + Number(value || 0).toLocaleString('en-PH')

function display(row, column) {
  const value = row[column.key]
  if (value == null || value === '') return '—'
  if (column.type === 'money') return money(value)
  return value
}

const STATUS_CLASSES = {
  Kickoff: 'is-neutral',
  Development: 'is-sent',
  Testing: 'is-sent',
  Deployed: 'is-paid',
  Email: 'is-sent',
  Call: 'is-neutral',
  Meeting: 'is-paid',
  Chat: 'is-neutral',
}
const statusClass = (value) => STATUS_CLASSES[value] || 'is-neutral'

function openNew() {
  editName.value = null
  showForm.value = true
}
function openEdit(row) {
  editName.value = row.name
  showForm.value = true
}
function onSaved() {
  list.reload()
  msg.value = ''
}

const showConfirm = ref(false)
const pendingDelete = ref(null)
const deleting = ref(false)
function askDelete(row) {
  pendingDelete.value = row
  showConfirm.value = true
}
async function doDelete() {
  if (!pendingDelete.value) return
  deleting.value = true
  msg.value = ''
  try {
    await call('frappe.client.delete', {
      doctype: props.doctype,
      name: pendingDelete.value.name,
    })
    showConfirm.value = false
    list.reload()
  } catch (error) {
    msg.value = String(error?.messages?.[0] || error?.message || 'Could not delete').replace(/<[^>]+>/g, '')
    showConfirm.value = false
  } finally {
    deleting.value = false
    pendingDelete.value = null
  }
}
</script>

<style scoped>
.page {
  background: var(--color-gray-50);
  min-height: 100vh;
  padding: var(--page-pad);
  color: var(--color-gray-900);
}
.head-right {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  flex-wrap: wrap;
}
.search-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.search-wrap svg {
  width: 16px;
  height: 16px;
  color: var(--color-gray-500);
  flex: none;
}
.search-input {
  width: 220px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 36px;
  margin-bottom: var(--space-3);
  color: var(--color-gray-600);
  font-size: var(--fs-sm);
}
.card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-5);
  box-shadow: var(--shadow-xs);
}
.table-scroll {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-sm);
}
th {
  text-align: left;
  color: var(--color-gray-600);
  font-weight: 500;
  padding: var(--space-2) var(--space-1);
  border-bottom: 1px solid var(--color-gray-200);
  white-space: nowrap;
}
td {
  padding: var(--space-3) var(--space-1);
  border-bottom: 1px solid var(--color-gray-100);
  max-width: 360px;
}
tbody tr:last-child td {
  border-bottom: none;
}
.strong {
  font-weight: 600;
}
.status {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: 999px;
  font-size: var(--fs-xs);
  font-weight: 600;
  white-space: nowrap;
}
.status.is-neutral {
  background: var(--color-gray-100);
  color: var(--color-gray-700);
}
.status.is-sent {
  background: var(--color-blue-100);
  color: var(--color-blue-700);
}
.status.is-paid {
  background: var(--color-emerald-100);
  color: var(--color-emerald-800);
}
.err {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  background: var(--color-red-100);
  border: 1px solid var(--color-red-200);
  color: var(--color-red-700);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  font-size: var(--fs-sm);
  margin-bottom: var(--space-3);
}
.err svg {
  width: 16px;
  height: 16px;
  flex: none;
  margin-top: 2px;
}
.actions {
  white-space: nowrap;
  text-align: right;
}
.actions :deep(button) + :deep(button) {
  margin-left: var(--space-2);
}
.mobile-cards {
  display: none;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
@media (max-width: 767px) {
  .search-input {
    width: 160px;
  }
  .table-scroll {
    display: none;
  }
  .mobile-cards {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }
  .card {
    padding: var(--space-3);
  }
  .mobile-card {
    border: 1px solid var(--color-gray-200);
    border-radius: var(--radius-md);
    padding: var(--space-3);
  }
  .mobile-card__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-2);
    margin-bottom: var(--space-2);
  }
  .mobile-card__actions {
    display: flex;
    gap: var(--space-1);
    flex: none;
  }
  .mobile-card dl {
    display: grid;
    grid-template-columns: minmax(90px, auto) 1fr;
    gap: var(--space-1) var(--space-3);
    margin: 0;
    font-size: var(--fs-sm);
  }
  .mobile-card dt {
    color: var(--color-gray-600);
  }
  .mobile-card dd {
    margin: 0;
    min-width: 0;
    overflow-wrap: anywhere;
  }
}
</style>
