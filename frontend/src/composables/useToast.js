import { reactive } from 'vue'

const toasts = reactive([])
let idCounter = 0

export function useToast() {
  function showToast(message, type = 'success') {
    const id = idCounter++
    toasts.push({ id, message, type })
    setTimeout(() => {
      const idx = toasts.findIndex((t) => t.id === id)
      if (idx !== -1) toasts.splice(idx, 1)
    }, 3000)
  }
  return { toasts, showToast }
}
