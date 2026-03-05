import { ref, readonly } from 'vue'

const toasts = ref([])
let idCounter = 0

function dismissToast(id) {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

function showToast(options) {
  if (!options || !options.message) return null
  const {
    message,
    type = 'info',
    autoClose,
    duration,
  } = options

  const id = ++idCounter
  const isError = type === 'error'
  const shouldAutoClose = autoClose !== undefined ? autoClose : !isError
  const timeout = duration != null ? duration : shouldAutoClose ? 3500 : null

  const toast = {
    id,
    message,
    type,
    autoClose: shouldAutoClose,
    duration: timeout,
  }

  toasts.value.push(toast)

  if (shouldAutoClose && timeout && typeof window !== 'undefined') {
    window.setTimeout(() => {
      dismissToast(id)
    }, timeout)
  }

  return id
}

export function useToast() {
  return {
    toasts: readonly(toasts),
    showToast,
    dismissToast,
  }
}

