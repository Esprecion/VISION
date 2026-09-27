import { reactive } from 'vue'

const toasts = reactive([])
let idCounter = 0

export function useToast() {
  function showToast(message, type = 'success', action = null) {
    const id = idCounter++
    toasts.push({ id, message, type, action })
    setTimeout(() => dismissToast(id), action ? 8000 : 3000)
    return id
  }
  function dismissToast(id) {
    const idx = toasts.findIndex((t) => t.id === id)
    if (idx !== -1) toasts.splice(idx, 1)
  }
  return { toasts, showToast, dismissToast }
}
