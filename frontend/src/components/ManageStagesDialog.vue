<template>
  <Dialog v-model="show" :options="{ title: 'Manage Stages', size: 'lg' }">
    <template #body-content>
      <div class="stages-list">
        <div v-for="stage in sortedStages" :key="stage.name" class="stage-row">
          <span class="dot" :style="{ background: stage.color || '#9ca3af' }"></span>

          <input
            v-if="editingName === stage.name"
            v-model="editValue"
            class="rename-input"
            type="text"
            @keyup.enter="confirmRename(stage)"
          />
          <span v-else class="stage-label">{{ stage.stage_name }}</span>

          <span v-if="stage.is_locked" class="locked-badge">locked</span>

          <div class="row-actions">
            <template v-if="!stage.is_locked">
              <template v-if="pendingDeleteName === stage.name">
                <span class="confirm-text">Delete?</span>
                <button class="icon-btn confirm-yes" title="Confirm delete" @click="doDelete(stage)">✓</button>
                <button class="icon-btn" title="Cancel" @click="cancelDelete">✕</button>
              </template>
              <template v-else>
                <button
                  v-if="editingName !== stage.name"
                  class="icon-btn"
                  title="Rename"
                  @click="startRename(stage)"
                >
                  ✎
                </button>
                <button
                  v-else
                  class="icon-btn"
                  title="Save"
                  :disabled="renaming"
                  @click="confirmRename(stage)"
                >
                  ✓
                </button>
                <button class="icon-btn danger" title="Delete" @click="startDelete(stage)">
                  ✕
                </button>
              </template>
            </template>
          </div>
        </div>
      </div>

      <div class="add-row">
        <input v-model="newStageName" type="text" placeholder="New stage name" />
        <input v-model="newStageColor" type="color" class="color-input" />
        <button class="btn-secondary" :disabled="!newStageName.trim() || adding" @click="addStage">
          + Add
        </button>
      </div>

      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, createResource, createListResource, call } from 'frappe-ui'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'updated'])

const show = ref(props.modelValue)
watch(() => props.modelValue, (v) => (show.value = v))
watch(show, (v) => {
  emit('update:modelValue', v)
  if (v) stagesResource.reload()
})

const stagesResource = createListResource({
  doctype: 'Pipeline Stage',
  fields: ['name', 'stage_name', 'color', 'is_locked', 'sequence'],
  orderBy: 'sequence asc',
  pageLength: 100,
  auto: true,
})

const sortedStages = computed(() =>
  [...(stagesResource.data || [])].sort((a, b) => (a.sequence || 0) - (b.sequence || 0))
)

const errorMsg = ref('')

// --- Rename ---
const editingName = ref(null)
const editValue = ref('')
const renaming = ref(false)

function startRename(stage) {
  editingName.value = stage.name
  editValue.value = stage.stage_name
  errorMsg.value = ''
}

async function confirmRename(stage) {
  const newName = editValue.value.trim()
  if (!newName || newName === stage.stage_name) {
    editingName.value = null
    return
  }
  renaming.value = true
  errorMsg.value = ''
  try {
    await call('frappe.client.rename_doc', {
      doctype: 'Pipeline Stage',
      old_name: stage.name,
      new_name: newName,
    })
    await call('frappe.client.set_value', {
      doctype: 'Pipeline Stage',
      name: newName,
      fieldname: 'stage_name',
      value: newName,
    })
    editingName.value = null
    await stagesResource.reload()
    emit('updated')
  } catch (e) {
    errorMsg.value = e?.messages?.[0] || 'Rename failed — name may already be in use.'
  } finally {
    renaming.value = false
  }
}

// --- Delete ---
const pendingDeleteName = ref(null)

async function startDelete(stage) {
  errorMsg.value = ''
  const inUse = await call('frappe.client.get_count', {
    doctype: 'Deal',
    filters: { stage: stage.name },
  })
  if (inUse > 0) {
    errorMsg.value = `Can't delete "${stage.stage_name}" — ${inUse} deal(s) are still in this stage.`
    return
  }
  pendingDeleteName.value = stage.name
}

function cancelDelete() {
  pendingDeleteName.value = null
}

async function doDelete(stage) {
  try {
    await call('frappe.client.delete', {
      doctype: 'Pipeline Stage',
      name: stage.name,
    })
    pendingDeleteName.value = null
    await stagesResource.reload()
    emit('updated')
  } catch (e) {
    errorMsg.value = e?.messages?.[0] || 'Delete failed.'
  }
}

// --- Add ---
const newStageName = ref('')
const newStageColor = ref('#9ca3af')
const adding = ref(false)

async function addStage() {
  const name = newStageName.value.trim()
  if (!name) return
  adding.value = true
  errorMsg.value = ''
  try {
    const maxSeq = Math.max(0, ...sortedStages.value.map((s) => s.sequence || 0))
    await call('frappe.client.insert', {
      doc: {
        doctype: 'Pipeline Stage',
        stage_name: name,
        color: newStageColor.value,
        is_locked: 0,
        sequence: maxSeq + 1,
      },
    })
    newStageName.value = ''
    newStageColor.value = '#9ca3af'
    await stagesResource.reload()
    emit('updated')
  } catch (e) {
    errorMsg.value = e?.messages?.[0] || 'Add failed — name may already exist.'
  } finally {
    adding.value = false
  }
}
</script>

<style scoped>
.stages-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.stage-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stage-label {
  flex: 1;
  font-size: 14px;
  color: #111827;
}
.rename-input {
  flex: 1;
  border: 1px solid #6366f1;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 14px;
}
.locked-badge {
  font-size: 11px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 999px;
}
.row-actions {
  display: flex;
  gap: 4px;
}
.icon-btn {
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  width: 26px;
  height: 26px;
  cursor: pointer;
  font-size: 13px;
}
.icon-btn.danger {
  color: #dc2626;
}
.confirm-text {
  font-size: 12px;
  color: #dc2626;
  margin-right: 2px;
}
.icon-btn.confirm-yes {
  color: #059669;
}
.add-row {
  display: flex;
  gap: 8px;
  align-items: center;
  border-top: 1px solid #e5e7eb;
  padding-top: 12px;
}
.add-row input[type='text'] {
  flex: 1;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 14px;
}
.color-input {
  width: 36px;
  height: 34px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 2px;
}
.btn-secondary {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #111827;
  font-size: 13px;
  font-weight: 500;
  padding: 8px 14px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.error-msg {
  color: #dc2626;
  font-size: 13px;
  margin-top: 10px;
}
</style>
