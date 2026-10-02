import { computed, reactive, ref, watch } from 'vue'
import { useCall } from 'frappe-ui'
import router from '@/router'

export const sessionUser = ref<string | null>(getSessionUserFromCookie())
export const userRoles = ref<string[]>([])

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

watch(
  sessionUser,
  (user) => {
    if (user) {
      rolesCall.submit ? rolesCall.submit() : rolesCall.reload?.()
    } else {
      userRoles.value = []
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
  isLoggedIn: computed(() => sessionUser.value != null),
  isAdmin: computed(() => userRoles.value.includes('System Manager') || sessionUser.value === 'Administrator'),
  isCBO: computed(() => userRoles.value.includes('CBO')),
  isCOO: computed(() => userRoles.value.includes('COO')),
  isCFO: computed(() => userRoles.value.includes('CFO')),
})

function getSessionUserFromCookie(): string | null {
  const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
  let user = cookies.get('user_id')
  if (user === 'Guest') {
    user = null
  }
  return user
}
