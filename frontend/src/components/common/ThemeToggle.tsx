import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'

interface ThemeToggleProps {
  className?: string
  compact?: boolean
}

export function ThemeToggle({ className, compact = false }: ThemeToggleProps) {
  const { theme, toggleTheme, isDark } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      type="button"
      className={`group relative flex items-center justify-center rounded-[8px] p-2 text-slate-400 hover:bg-slate-800/80 hover:text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50 light:hover:bg-slate-200 light:text-slate-600 ${className || ''}`}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode (currently ${theme})`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <div className="relative h-4 w-4">
        <Sun
          className={`h-4 w-4 transition-all duration-300 absolute inset-0 ${
            isDark ? 'rotate-90 scale-0 opacity-0' : 'rotate-0 scale-100 opacity-100 text-amber-500'
          }`}
        />
        <Moon
          className={`h-4 w-4 transition-all duration-300 absolute inset-0 ${
            isDark ? 'rotate-0 scale-100 opacity-100 text-indigo-400' : '-rotate-90 scale-0 opacity-0'
          }`}
        />
      </div>
      {!compact && (
        <span className="sr-only">Toggle theme</span>
      )}
    </button>
  )
}
