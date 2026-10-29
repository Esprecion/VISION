import { computed, reactive, ref, watch } from 'vue'
import { useCall } from 'frappe-ui'
import router from '@/router'

export const sessionUser = ref<string | null>(getSessionUserFromCookie())
export const userRoles = ref<string[]>([])
export const modulePerms = ref<Record<string, { read: boolean; write: boolean }>>({})
export const canManageUsers = ref(false)

const MODULE_BY_DOCTYPE: Record<string, string> = {
  Deal: 'business_dev',
  Client: 'business_dev',
  Product: 'business_dev',
  'Service Contract': 'business_dev',
  Invoice: 'finance',
  Expense: 'finance',
  Project: 'operations',
  'Tool Subscription': 'operations',
  'Client Engagement Log': 'operations',
}

const rolesCall = useCall({
  url: '/api/method/my_custom_app.api.get_my_roles',
  immediate: false,
  onSuccess(data: any) {
    userRoles.value = data?.message?.roles || data?.roles || []
  },
  onError() {
    userRoles.value = []
  },
})

const permsCall = useCall({
  url: '/api/method/my_custom_app.api.get_module_perms',
  immediate: false,
  onSuccess(data: any) {
    modulePerms.value = data?.message || data || {}
  },
  onError() {
    modulePerms.value = {}
  },
})

const adminAccessCall = useCall({
  url: '/api/method/my_custom_app.admin.can_manage_users',
  immediate: false,
  onSuccess(data: any) {
    canManageUsers.value = Boolean(data?.message ?? data)
  },
  onError() {
    canManageUsers.value = false
  },
})

async function ensureCall(call: any) {
  if (call.loading) {
    await call.promise.value
  } else if (!call.isFinished) {
    await call.submit()
  }
}

export async function ensureSessionData() {
  if (!sessionUser.value) return
  await Promise.all([ensureCall(rolesCall), ensureCall(permsCall)])
}

export async function ensureAdminAccess() {
  if (!sessionUser.value) return false
  await ensureCall(adminAccessCall)
  return canManageUsers.value
}

watch(
  sessionUser,
  (user) => {
    if (user) {
      rolesCall.submit ? rolesCall.submit() : rolesCall.reload?.()
      permsCall.submit ? permsCall.submit() : permsCall.reload?.()
      adminAccessCall.submit ? adminAccessCall.submit() : adminAccessCall.reload?.()
    } else {
      userRoles.value = []
      modulePerms.value = {}
      canManageUsers.value = false
    }
  },
  { immediate: true }
)

export const session = reactive({
  login: useCall({
    url: '/api/v2/method/login',
    immediate: false,
    onSuccess(data: any) {
      sessionUser.value = getSessionUserFromCookie()
      session.login.reset()
      router.replace(data.default_route || '/')
    },
  }),
  logout: useCall({
    url: '/api/v2/method/logout',
    method: 'POST',
    immediate: false,
    onSuccess() {
      sessionUser.value = getSessionUserFromCookie()
      window.location.href = '/login?redirect-to=/frontend/dashboard'
    },
  }),
  user: sessionUser,
  roles: userRoles,
  canManageUsers,
  isLoggedIn: computed(() => sessionUser.value != null),
  isAdmin: computed(() => userRoles.value.includes('System Manager') || sessionUser.value === 'Administrator'),
  isSystemAdmin: computed(
    () => userRoles.value.includes('System Admin') || sessionUser.value === 'Administrator'
  ),
  isCBO: computed(() => userRoles.value.includes('CBO')),
  isCOO: computed(() => userRoles.value.includes('COO')),
  isCFO: computed(() => userRoles.value.includes('CFO')),
  isCTO: computed(() => userRoles.value.includes('CTO')),
  primaryRole: computed(() => {
    if (sessionUser.value === 'Administrator') return 'Administrator'
    if (userRoles.value.includes('System Admin')) return 'System Admin'
    return ['CBO', 'COO', 'CFO', 'CTO'].find((role) => userRoles.value.includes(role)) || ''
  }),
  canRead: (module: string) => {
    if (session.isAdmin) return true
    return !!modulePerms.value?.[module]?.read
  },
  canWrite: (doctype: string) => {
    if (session.isAdmin) return true
    const module = MODULE_BY_DOCTYPE[doctype]
    return module ? !!modulePerms.value?.[module]?.write : false
  },
})

function getSessionUserFromCookie(): string | null {
  const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
  let user = cookies.get('user_id')
  if (user === 'Guest') {
    user = null
  }
  return user
}
