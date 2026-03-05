const prefersReducedMotion = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  } catch {
    return false
  }
}

function setupObserver(el) {
  if (prefersReducedMotion()) {
    el.classList.add('reveal-in')
    el.classList.remove('reveal-base')
    return
  }

  el.classList.add('reveal-base')

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting || entry.intersectionRatio > 0) {
          el.classList.add('reveal-in')
          el.classList.remove('reveal-base')
          observer.unobserve(el)
        }
      })
    },
    {
      threshold: 0.2,
    }
  )

  observer.observe(el)
  el._revealObserver = observer
}

function cleanupObserver(el) {
  if (el._revealObserver) {
    try {
      el._revealObserver.unobserve(el)
      el._revealObserver.disconnect()
    } catch {
      // ignore
    }
    delete el._revealObserver
  }
}

export default {
  mounted(el) {
    setupObserver(el)
  },
  updated(el) {
    if (!el.classList.contains('reveal-in')) {
      setupObserver(el)
    }
  },
  unmounted(el) {
    cleanupObserver(el)
  },
}

