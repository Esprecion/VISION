<template>
  <Dialog v-model="show" :options="{ title: isEdit ? 'Edit User' : 'Add User', size: 'sm' }">
    <template #body-content>
      <div class="form-grid">
        <AppTextInput
          v-model="form.account_name"
          label="Account Name"
          required
          :disabled="isEdit"
          placeholder="e.g. juan.delacruz"
        />
        <AppSelect
          v-model="form.role"
          label="Role"
          required
          :options="roleOptions"
          placeholder="Choose a role"
        />
        <AppTextInput
          v-model="form.password"
          type="password"
          :label="isEdit ? 'New Password' : 'Password'"
          :required="!isEdit"
          :placeholder="isEdit ? 'Leave blank to keep the current password' : 'Set a strong password'"
        />
        <p v-if="isEdit" class="hint">
          Account names cannot be changed. Leave the password blank to keep the current one.
        </p>
        <p v-if="errorMessage" class="error-msg" role="alert">
          <AlertCircleIcon class="error-icon" aria-hidden="true" />
          {{ errorMessage }}
        </p>
      </div>
    </template>
    <template #actions>
      <AppButton
        variant="solid"
        theme="gray"
        :disabled="!isValid || saving"
        :loading="saving"
        @click="submit"
      >
        {{ isEdit ? 'Save Changes' : 'Create User' }}
      </AppButton>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Dialog, createResource } from 'frappe-ui'
import AlertCircleIcon from '~icons/lucide/alert-circle'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  user: { type: Object, default: null },
  roles: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue', 'saved'])

const isEdit = computed(() => Boolean(props.user))
const show = ref(props.modelValue)
const errorMessage = ref('')

const form = reactive({
  account_name: '',
  role: '',
  password: '',
})

const roleOptions = computed(() =>
  props.roles.map((role) => ({ label: role, value: role }))
)

const createUser = createResource({
  url: '/api/method/my_custom_app.admin.create_user',
  method: 'POST',
})

const editUser = createResource({
  url: '/api/method/my_custom_app.admin.edit_user',
  method: 'POST',
})

const activeResource = computed(() => (isEdit.value ? editUser : createUser))
const saving = computed(() => Boolean(activeResource.value.loading))

const isValid = computed(() => {
  if (!form.account_name.trim() || !form.role) return false
  return isEdit.value || Boolean(form.password)
})

watch(
  () => props.modelValue,
  (open) => {
    show.value = open
    if (open) resetForm()
  }
)

watch(show, (open) => emit('update:modelValue', open))

watch(
  () => props.roles,
  (roles) => {
    if (!form.role && roles.length) form.role = roles[0]
  }
)

function resetForm() {
  form.account_name = props.user?.account_name || ''
  form.role = props.user?.role || props.roles[0] || ''
  form.password = ''
  errorMessage.value = ''
  createUser.reset()
  editUser.reset()
}

function submit() {
  if (!isValid.value || saving.value) return
  errorMessage.value = ''

  const payload = {
    account_name: form.account_name.trim(),
    role: form.role,
  }
  if (form.password) payload.password = form.password

  activeResource.value.submit(payload, {
    onSuccess(response) {
      const result = response?.message || response
      if (!result?.ok) {
        errorMessage.value = result?.message || 'Unable to save the user.'
        return
      }
      emit('saved', result.user)
      show.value = false
    },
    onError(error) {
      errorMessage.value =
        error?.messages?.[0] || error?.message || 'Unable to save the user.'
    },
  })
}
</script>

<style scoped>
.form-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.hint {
  margin: 0;
  font-size: var(--fs-xs);
  color: var(--color-gray-600);
}
.error-msg {
  display: flex;
  align-items: flex-start;
  gap: var(--space-1);
  margin: 0;
  color: var(--color-red-600);
  font-size: var(--fs-sm);
}
.error-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  margin-top: 2px;
}
</style>
