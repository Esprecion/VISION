<template>
  <Dialog v-model="show" :options="{ title: 'Manage Stages', size: 'lg' }">
    <template #body-content>
      <div class="stages-list">
        <div v-for="stage in sortedStages" :key="stage.name" class="stage-row">
          <span class="dot" :style="{ background: stage.color || 'var(--color-gray-400)' }"></span>

          <AppTextInput
            v-if="editingName === stage.name"
            v-model="editValue"
            class="rename-input-wrap"
            @keyup.enter="confirmRename(stage)"
          />
          <span v-else class="stage-label">{{ stage.stage_name }}</span>

          <span v-if="stage.is_locked" class="locked-badge">locked</span>

          <div class="row-actions">
            <template v-if="!stage.is_locked">
              <template v-if="editingName !== stage.name">
                <AppButton
                  variant="ghost"
                  size="sm"
                  :icon="PencilIcon"
                  @click="startRename(stage)"
                  aria-label="Rename stage"
                />
                <AppButton
                  variant="ghost"
                  size="sm"
                  theme="red"
                  :icon="XIcon"
                  @click="startDelete(stage)"
                  aria-label="Delete stage"
                />
              </template>
              <template v-else>
                <AppButton
                  variant="ghost"
                  size="sm"
                  theme="green"
                  :icon="CheckIcon"
                  :disabled="renaming"
                  @click="confirmRename(stage)"
                  aria-label="Save rename"
                />
                <AppButton
                  variant="ghost"
                  size="sm"
                  :icon="XIcon"
                  @click="editingName = null"
                  aria-label="Cancel rename"
                />
              </template>
            </template>
          </div>
        </div>
      </div>

      <div class="add-row">
        <AppTextInput v-model="newStageName" placeholder="New stage name" class="add-input" />
        <div class="color-swatches">
          <button
            v-for="c in colorPresets"
            :key="c"
            type="button"
            class="swatch"
            :class="{ selected: newStageColor === c }"
            :style="{ background: c }"
            @click="newStageColor = c"
          ></button>
        </div>
        <AppButton
          variant="outline"
          size="md"
          :disabled="!newStageName.trim() || adding"
          :loading="adding"
          @click="addStage"
        >
          <template #prefix><PlusIcon aria-hidden="true" /></template>
          Add
        </AppButton>
      </div>

      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
    </template>
  </Dialog>
  <AppConfirmDialog
    v-model="showDeleteConfirm"
    title="Delete stage"
    :message="pendingDelete ? 'Delete stage &quot;' + pendingDelete.stage_name + '&quot;? This cannot be undone.' : ''"
    confirm-label="Delete"
    destructive
    :loading="deleting"
    @confirm="confirmDeleteAction"
    @cancel="cancelDelete"
  />
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Dialog, createResource, createListResource, call } from 'frappe-ui'
import CheckIcon from '~icons/lucide/check'
import XIcon from '~icons/lucide/x'
import PencilIcon from '~icons/lucide/pencil'
import PlusIcon from '~icons/lucide/plus'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'

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
const pendingDelete = ref(null)
const showDeleteConfirm = ref(false)
const deleting = ref(false)

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
  pendingDelete.value = stage
  showDeleteConfirm.value = true
}

function cancelDelete() {
  pendingDelete.value = null
  showDeleteConfirm.value = false
}

async function confirmDeleteAction() {
  if (!pendingDelete.value) return
  deleting.value = true
  errorMsg.value = ''
  try {
    await call('frappe.client.delete', {
      doctype: 'Pipeline Stage',
      name: pendingDelete.value.name,
    })
    showDeleteConfirm.value = false
    pendingDelete.value = null
    await stagesResource.reload()
    emit('updated')
  } catch (e) {
    errorMsg.value = e?.messages?.[0] || 'Delete failed.'
    showDeleteConfirm.value = false
  } finally {
    deleting.value = false
  }
}

// --- Add ---
const colorPresets = ['var(--color-blue-500)', 'var(--color-emerald-500)', 'var(--color-amber-500)', 'var(--color-purple-500)', 'var(--color-green-600)', 'var(--color-red-500)', 'var(--color-pink-500)', 'var(--color-gray-500)']
const newStageName = ref('')
const newStageColor = ref(colorPresets[0])
const adding = ref(false)

async function addStage() {
  const name = newStageName.value.trim()
  if (!name) return
  adding.value = true
  errorMsg.value = ''
  try {
    const maxSeq = Math.max(0, ...sortedStages.value.filter((s) => !s.is_locked).map((s) => s.sequence || 0))
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
    newStageColor.value = colorPresets[0]
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
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
.stage-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stage-label {
  flex: 1;
  font-size: var(--fs-sm);
  color: var(--color-gray-900);
}
.rename-input-wrap {
  flex: 1;
}
.locked-badge {
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
  background: var(--color-gray-100);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
}
.row-actions {
  display: flex;
  gap: var(--space-1);
}
.add-row {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  border-top: 1px solid var(--color-gray-200);
  padding-top: var(--space-3);
  flex-wrap: wrap;
}
.add-input {
  flex: 1;
  min-width: 160px;
}
.color-swatches {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  flex-wrap: wrap;
}
.swatch {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-full);
  border: 2px solid transparent;
  cursor: pointer;
  padding: 0;
}
.swatch.selected {
  border-color: var(--color-gray-900);
  box-shadow: 0 0 0 2px var(--color-white), 0 0 0 3px var(--color-gray-900);
}

.error-msg {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  color: var(--color-red-600);
  font-size: var(--fs-sm);
  margin-top: var(--space-3);
}
</style>
