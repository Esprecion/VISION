<template>
  <Dialog v-model="show" :options="{ title: isEdit ? 'Edit User' : 'Add User', size: 'sm' }">
    <template #body-content>
      <div class="form-grid">
        <AppTextInput
          v-model="form.account_name"
          label="Account Name"
          required
          :disabled="isEdit"
          :error="fieldErrors.account_name"
          placeholder="e.g. juan.delacruz"
        />
        <AppSelect
          v-model="form.role"
          label="Role"
          required
          :options="roleOptions"
          :error="fieldErrors.role"
          placeholder="Choose a role"
        />
        <AppTextInput
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          :label="isEdit ? 'New Password' : 'Password'"
          :required="!isEdit"
          :error="fieldErrors.password"
          :placeholder="isEdit ? 'Leave blank to keep the current password' : 'Set a strong password'"
          autocomplete="new-password"
        >
          <template #suffix>
            <button
              type="button"
              class="password-toggle"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            >
              <EyeOffIcon v-if="showPassword" class="password-toggle__icon" aria-hidden="true" />
              <EyeIcon v-else class="password-toggle__icon" aria-hidden="true" />
            </button>
          </template>
        </AppTextInput>
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
import EyeIcon from '~icons/lucide/eye'
import EyeOffIcon from '~icons/lucide/eye-off'
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
const showPassword = ref(false)

const form = reactive({
  account_name: '',
  role: '',
  password: '',
})

const fieldErrors = reactive({
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

watch(
  () => form.account_name,
  () => clearFieldError('account_name')
)
watch(
  () => form.role,
  () => clearFieldError('role')
)
watch(
  () => form.password,
  () => clearFieldError('password')
)

function clearFieldErrors() {
  fieldErrors.account_name = ''
  fieldErrors.role = ''
  fieldErrors.password = ''
}

function clearFieldError(field) {
  if (fieldErrors[field]) fieldErrors[field] = ''
}

function showResultError(result) {
  clearFieldErrors()
  const message = result?.message || 'Unable to save the user.'
  const fields = Array.isArray(result?.fields)
    ? result.fields
    : result?.field
      ? [result.field]
      : []
  const knownFields = fields.filter((field) =>
    Object.prototype.hasOwnProperty.call(fieldErrors, field)
  )

  if (!knownFields.length) {
    errorMessage.value = message
    return
  }

  for (const field of knownFields) {
    fieldErrors[field] = message
  }
}

function resetForm() {
  form.account_name = props.user?.account_name || ''
  form.role = props.user?.role || props.roles[0] || ''
  form.password = ''
  errorMessage.value = ''
  showPassword.value = false
  clearFieldErrors()
  createUser.reset()
  editUser.reset()
}

function submit() {
  if (!isValid.value || saving.value) return
  errorMessage.value = ''
  clearFieldErrors()
  showPassword.value = false

  const payload = {
    account_name: form.account_name.trim(),
    role: form.role,
  }
  if (form.password) payload.password = form.password

  activeResource.value.submit(payload, {
    onSuccess(response) {
      const result = response?.message || response
      if (!result?.ok) {
        showResultError(result)
        return
      }
      emit('saved', result.user)
      show.value = false
    },
    onError(error) {
      clearFieldErrors()
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
.password-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-gray-500);
  cursor: pointer;
}
.password-toggle:hover {
  color: var(--color-gray-900);
  background: var(--color-gray-100);
}
.password-toggle:focus-visible {
  outline: var(--focus-ring);
  outline-offset: var(--focus-ring-offset);
}
.password-toggle__icon {
  width: 16px;
  height: 16px;
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
