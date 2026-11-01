import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  Database,
  History,
  LayoutGrid,
  Settings,
  X,
} from 'lucide-react'
import { BrandLogo } from '@/components/common/BrandLogo'
import { ConnectionBadge } from '@/components/common/ConnectionBadge'
import { ThemeToggle } from '@/components/common/ThemeToggle'

interface MobileNavProps {
  isOpen: boolean
  onClose: () => void
  onOpenCapabilities: () => void
}

export function MobileNav({ isOpen, onClose, onOpenCapabilities }: MobileNavProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeyDown)
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const navItems = [
    { to: '/', label: 'Workspace', icon: LayoutGrid },
    { to: '/schemas', label: 'Schema Explorer', icon: Database },
    { to: '/history', label: 'Query History', icon: History },
    { to: '/insights', label: 'Insights', icon: BarChart3 },
    { to: '/settings', label: 'Settings', icon: Settings },
  ]

  return (
    <div
      className="fixed inset-0 z-50 md:hidden flex"
      role="dialog"
      aria-modal="true"
      aria-label="Mobile Navigation Drawer"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div className="relative flex w-4/5 max-w-xs flex-col justify-between bg-slate-950 p-5 shadow-2xl border-r border-slate-800 z-10 light:bg-white light:border-slate-200">
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800 light:border-slate-100">
            <BrandLogo showSubtitle={true} size="sm" />
            <button
              onClick={onClose}
              type="button"
              className="rounded-[8px] p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 light:hover:bg-slate-100"
              aria-label="Close navigation"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Nav Links */}
          <nav className="mt-4 space-y-1" aria-label="Mobile Routes">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-[10px] px-3.5 py-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${
                      isActive
                        ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 light:bg-indigo-50 light:text-indigo-700'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 light:text-slate-600 light:hover:bg-slate-100'
                    }`
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 light:border-slate-100 space-y-3">
          <button
            onClick={() => {
              onClose()
              onOpenCapabilities()
            }}
            type="button"
            className="w-full flex items-center justify-between rounded-[8px] border border-slate-800 bg-slate-900/60 p-2.5 text-xs text-slate-300 hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 light:border-slate-200 light:bg-slate-50 light:text-slate-700"
          >
            <span className="flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-indigo-400" />
              <span>System Capabilities</span>
            </span>
            <span className="text-[10px] font-mono-code text-slate-400">v0.1.0</span>
          </button>

          <div className="flex items-center justify-between">
            <ConnectionBadge onOpenCapabilities={onOpenCapabilities} />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </div>
  )
}
