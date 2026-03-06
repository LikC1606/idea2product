const prefersReducedMotion = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  try {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  } catch {
    return false
  }
}

function isScrollableStyle(value) {
  return value === 'auto' || value === 'scroll' || value === 'overlay'
}

function findScrollRoot(el) {
  if (typeof window === 'undefined') return null
  let cur = el?.parentElement
  while (cur && cur !== document.body) {
    const style = window.getComputedStyle(cur)
    const overflowY = style?.overflowY
    const overflow = style?.overflow
    if (isScrollableStyle(overflowY) || isScrollableStyle(overflow)) {
      return cur
    }
    cur = cur.parentElement
  }
  return null
}

function setupObserver(el) {
  if (prefersReducedMotion()) {
    el.classList.add('reveal-in')
    el.classList.remove('reveal-base')
    return
  }

  if (typeof IntersectionObserver === 'undefined') {
    el.classList.add('reveal-in')
    el.classList.remove('reveal-base')
    return
  }

  el.classList.add('reveal-base')

  const root = findScrollRoot(el)
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
      root,
      threshold: 0,
      rootMargin: '64px 0px 64px 0px',
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

