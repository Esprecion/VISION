<script setup>
import { computed, ref } from 'vue'
import { createResource, useCall } from 'frappe-ui'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTextInput from '@/components/ui/AppTextInput.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ErrorState from '@/components/ui/ErrorState.vue'
import AppConfirmDialog from '@/components/ui/AppConfirmDialog.vue'
import UserFormDialog from '@/components/UserFormDialog.vue'
import { useToast } from '@/composables/useToast'
import PlusIcon from '~icons/lucide/plus'
import SearchIcon from '~icons/lucide/search'

const { showToast } = useToast()

const search = ref('')
const users = ref([])
const roles = ref([])
const showForm = ref(false)
const editingUser = ref(null)
const showDeactivate = ref(false)
const deactivateTarget = ref(null)
const reactivatingAccount = ref('')

const usersCall = useCall({
  url: '/api/method/my_custom_app.admin.list_users',
  immediate: true,
  onSuccess(data) {
    users.value = data?.message || data || []
  },
  onError() {
    users.value = []
  },
})

const rolesCall = useCall({
  url: '/api/method/my_custom_app.admin.get_managed_roles',
  immediate: true,
  onSuccess(data) {
    roles.value = data?.message || data || []
  },
  onError() {
    roles.value = []
  },
})

const deactivateUser = createResource({
  url: '/api/method/my_custom_app.admin.deactivate_user',
  method: 'POST',
})

const reactivateUser = createResource({
  url: '/api/method/my_custom_app.admin.reactivate_user',
  method: 'POST',
})

const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return users.value

  return users.value.filter((user) => {
    const accountName = (user.account_name || '').toLowerCase()
    const userRoles = roleList(user).map((role) => role.toLowerCase())
    return accountName.includes(query) || userRoles.some((role) => role.includes(query))
  })
})

const loading = computed(() => usersCall.loading && !users.value.length)
const loadError = computed(() => usersCall.error)

const roleColors = {
  'System Admin': 'danger',
  CBO: 'success',
  CFO: 'warning',
  COO: 'info',
  CTO: 'neutral',
}

function roleList(user) {
  const list = user.roles?.length ? user.roles : [user.role]
  return list.filter(Boolean)
}

function openCreate() {
  editingUser.value = null
  showForm.value = true
}

function openEdit(user) {
  editingUser.value = user
  showForm.value = true
}

function onSaved(user) {
  const wasEdit = Boolean(editingUser.value)
  showForm.value = false
  editingUser.value = null
  showToast(`${wasEdit ? 'Updated' : 'Created'} ${user.account_name}`)
  usersCall.reload()
}

function askDeactivate(user) {
  if (!user.enabled) return
  deactivateTarget.value = user
  showDeactivate.value = true
}

function confirmDeactivate() {
  const user = deactivateTarget.value
  if (!user) return

  deactivateUser.submit(
    { account_name: user.account_name },
    {
      onSuccess(response) {
        const result = response?.message || response
        showDeactivate.value = false
        if (!result?.ok) {
          showToast(result?.message || 'Unable to deactivate the user.', 'error')
          return
        }
        deactivateTarget.value = null
        showToast(`${user.account_name} was deactivated`)
        usersCall.reload()
      },
      onError(error) {
        showDeactivate.value = false
        showToast(error?.messages?.[0] || error?.message || 'Unable to deactivate the user.', 'error')
      },
    }
  )
}

function confirmReactivate(user) {
  if (!user || user.enabled || reactivateUser.loading) return

  reactivatingAccount.value = user.account_name
  reactivateUser.submit(
    { account_name: user.account_name },
    {
      onSuccess(response) {
        const result = response?.message || response
        reactivatingAccount.value = ''
        if (!result?.ok) {
          showToast(result?.message || 'Unable to reactivate the user.', 'error')
          return
        }
        showToast(`${user.account_name} was reactivated`)
        usersCall.reload()
      },
      onError(error) {
        reactivatingAccount.value = ''
        showToast(error?.messages?.[0] || error?.message || 'Unable to reactivate the user.', 'error')
      },
    }
  )
}
</script>

<template>
  <div class="admin-page">
    <PageHeader
      title="Administration · Users"
      subtitle="Create accounts, assign roles, and deactivate access."
    >
      <template #actions>
        <AppButton variant="solid" theme="gray" @click="openCreate">
          <template #prefix>
            <PlusIcon class="btn-icon" aria-hidden="true" />
          </template>
          Add User
        </AppButton>
      </template>
    </PageHeader>

    <div class="search-wrap">
      <SearchIcon aria-hidden="true" />
      <AppTextInput
        v-model="search"
        class="search-input"
        type="search"
        placeholder="Search by account name or role..."
        aria-label="Search users"
      />
    </div>

    <div class="table-wrap">
      <AppSkeleton v-if="loading" variant="table" :rows="6" :cols="4" />
      <ErrorState
        v-else-if="loadError && !users.length"
        title="Couldn't load users"
        :message="loadError?.messages?.[0] || loadError?.message || 'Please try again.'"
        :on-retry="() => usersCall.reload()"
      />
      <EmptyState
        v-else-if="!users.length"
        title="No users yet"
        description="Create the first account and assign a role to give access to VISION."
      >
        <template #action>
          <AppButton variant="solid" theme="gray" @click="openCreate">
            <template #prefix>
              <PlusIcon class="btn-icon" aria-hidden="true" />
            </template>
            Add User
          </AppButton>
        </template>
      </EmptyState>
      <EmptyState
        v-else-if="!filteredUsers.length"
        :icon="SearchIcon"
        title="No matching users"
        description="No accounts match your search. Try a different name or role."
      >
        <template #action>
          <AppButton variant="outline" @click="search = ''">Clear search</AppButton>
        </template>
      </EmptyState>
      <div v-else class="table-scroll">
        <table class="users-table">
          <thead>
            <tr>
              <th>Account</th>
              <th>Roles</th>
              <th>Status</th>
              <th class="actions-head">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in filteredUsers" :key="user.account_name">
              <td class="account-name">{{ user.account_name }}</td>
              <td>
                <div class="role-list">
                  <AppBadge
                    v-for="role in roleList(user)"
                    :key="role"
                    :label="role"
                    :color="roleColors[role] || 'neutral'"
                  />
                  <span
                    v-if="user.has_extra_roles"
                    class="extra-roles-note"
                    title="This account has roles outside the selected managed role."
                  >
                    Extra roles
                  </span>
                </div>
              </td>
              <td>
                <AppBadge
                  :label="user.enabled ? 'Active' : 'Inactive'"
                  :color="user.enabled ? 'success' : 'neutral'"
                />
              </td>
              <td>
                <div class="row-actions">
                  <AppButton variant="ghost" size="sm" @click="openEdit(user)">
                    Edit
                  </AppButton>
                  <AppButton
                    v-if="user.enabled"
                    variant="ghost"
                    size="sm"
                    :disabled="deactivateUser.loading"
                    @click="askDeactivate(user)"
                  >
                    Deactivate
                  </AppButton>
                  <AppButton
                    v-else
                    variant="ghost"
                    size="sm"
                    :loading="reactivatingAccount === user.account_name"
                    :disabled="reactivateUser.loading && reactivatingAccount !== user.account_name"
                    @click="confirmReactivate(user)"
                  >
                    Reactivate
                  </AppButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="user-cards">
        <article v-for="user in filteredUsers" :key="user.account_name" class="user-card">
          <div class="user-card__head">
            <span class="account-name">{{ user.account_name }}</span>
            <AppBadge
              :label="user.enabled ? 'Active' : 'Inactive'"
              :color="user.enabled ? 'success' : 'neutral'"
            />
          </div>
          <div class="role-list">
            <AppBadge
              v-for="role in roleList(user)"
              :key="role"
              :label="role"
              :color="roleColors[role] || 'neutral'"
            />
            <span
              v-if="user.has_extra_roles"
              class="extra-roles-note"
              title="This account has roles outside the selected managed role."
            >
              Extra roles
            </span>
          </div>
          <div class="row-actions">
            <AppButton variant="ghost" size="sm" @click="openEdit(user)">
              Edit
            </AppButton>
            <AppButton
              v-if="user.enabled"
              variant="ghost"
              size="sm"
              :disabled="deactivateUser.loading"
              @click="askDeactivate(user)"
            >
              Deactivate
            </AppButton>
            <AppButton
              v-else
              variant="ghost"
              size="sm"
              :loading="reactivatingAccount === user.account_name"
              :disabled="reactivateUser.loading && reactivatingAccount !== user.account_name"
              @click="confirmReactivate(user)"
            >
              Reactivate
            </AppButton>
          </div>
        </article>
      </div>
    </div>

    <UserFormDialog
      v-model="showForm"
      :user="editingUser"
      :roles="roles"
      @saved="onSaved"
    />

    <AppConfirmDialog
      v-model="showDeactivate"
      title="Deactivate user?"
      :message="deactivateTarget
        ? `${deactivateTarget.account_name} will no longer be able to sign in. The user record will be kept.`
        : ''"
      confirm-label="Deactivate"
      destructive
      :loading="deactivateUser.loading"
      @confirm="confirmDeactivate"
    />
  </div>
</template>

<style scoped>
.admin-page {
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
.search-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}
.search-wrap svg {
  width: 16px;
  height: 16px;
  color: var(--color-gray-500);
  flex: none;
}
.search-wrap:focus-within svg {
  color: var(--color-gray-700);
}
.search-wrap :deep(.app-field) {
  flex: 1;
  min-width: 0;
}
.search-input {
  width: 100%;
  max-width: 360px;
}
.table-wrap {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.table-scroll {
  overflow-x: auto;
}
.users-table {
  width: 100%;
  border-collapse: collapse;
}
.users-table th,
.users-table td {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--fs-sm);
  border-bottom: 1px solid var(--color-gray-200);
  white-space: nowrap;
}
.users-table th {
  color: var(--color-gray-600);
  font-weight: 600;
  font-size: var(--fs-xs);
  text-transform: uppercase;
  background: var(--color-gray-50);
}
.users-table tr:last-child td {
  border-bottom: none;
}
.account-name {
  font-weight: 600;
}
.role-list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1);
}
.extra-roles-note {
  font-size: var(--fs-xs);
  color: var(--color-gray-500);
  white-space: nowrap;
}
.row-actions {
  display: flex;
  gap: var(--space-1);
  justify-content: flex-end;
}
.actions-head {
  text-align: right;
}
.user-cards {
  display: none;
}
@media (max-width: 640px) {
  .search-input {
    max-width: none;
  }
  .table-scroll {
    display: none;
  }
  .user-cards {
    display: flex;
    flex-direction: column;
  }
  .user-card {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    padding: var(--space-4);
    border-bottom: 1px solid var(--color-gray-200);
  }
  .user-card:last-child {
    border-bottom: none;
  }
  .user-card__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-2);
  }
  .user-card .row-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
