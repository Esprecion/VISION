<script setup>
import { computed, ref } from 'vue'
import { createResource, useCall } from 'frappe-ui'
import PageHeader from '@/components/ui/PageHeader.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
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
      <SearchIcon class="search-icon" aria-hidden="true" />
      <input
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
                  <AppBadge
                    v-if="user.has_extra_roles"
                    label="Extra roles"
                    color="neutral"
                  />
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
                    variant="ghost"
                    size="sm"
                    :disabled="!user.enabled"
                    @click="askDeactivate(user)"
                  >
                    Deactivate
                  </AppButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
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
  gap: var(--space-1);
}
.row-actions {
  display: flex;
  gap: var(--space-1);
  justify-content: flex-end;
}
.actions-head {
  text-align: right;
}
@media (max-width: 640px) {
  .search-input {
    max-width: none;
  }
}
</style>
