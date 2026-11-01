import { useEffect, useState } from 'react'

export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'schemasense_theme'

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'light' || stored === 'dark') {
        return stored
      }
    } catch {
      // Default to dark
    }
    return 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    const metaTheme = document.querySelector('meta[name="color-scheme"]')

    if (theme === 'dark') {
      root.classList.add('dark')
      root.classList.remove('light')
      if (metaTheme) metaTheme.setAttribute('content', 'dark')
    } else {
      root.classList.add('light')
      root.classList.remove('dark')
      if (metaTheme) metaTheme.setAttribute('content', 'light')
    }

    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // Storage unavailable
    }
  }, [theme])

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return { theme, setTheme, toggleTheme, isDark: theme === 'dark' }
}
