import { Menu, Search } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { ConnectionBadge } from '@/components/common/ConnectionBadge'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { Badge } from '@/components/ui/Badge'
import { useBackendHealth } from '@/hooks/useBackendHealth'

interface TopNavProps {
  onOpenMobileMenu: () => void
  onOpenCapabilities: () => void
  onFocusComposer?: () => void
}

export function TopNav({
  onOpenMobileMenu,
  onOpenCapabilities,
  onFocusComposer,
}: TopNavProps) {
  const location = useLocation()
  const { state, latencyMs } = useBackendHealth()

  const getPageInfo = (path: string) => {
    switch (path) {
      case '/':
        return { title: 'Workspace', subtitle: 'Natural Language to SQL Studio' }
      case '/schemas':
        return { title: 'Schema Explorer', subtitle: 'Database Metadata & Catalog' }
      case '/history':
        return { title: 'Query History', subtitle: 'Audit Log & Execution Archive' }
      case '/insights':
        return { title: 'Insights', subtitle: 'Performance & Optimization Telemetry' }
      case '/settings':
        return { title: 'Settings', subtitle: 'System Preferences & API Config' }
      default:
        return { title: 'SchemaSense AI', subtitle: 'Precision SQL Engine' }
    }
  }

  const { title, subtitle } = getPageInfo(location.pathname)

  return (
    <header
      className="flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/60 px-4 sm:px-6 backdrop-blur-md select-none light:border-slate-200 light:bg-white/80"
      role="banner"
    >
      {/* Screen reader live announcement for connection state changes */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {state === 'connected'
          ? `Backend API connected, latency ${latencyMs ?? 0} milliseconds`
          : state === 'checking'
            ? 'Connecting to backend API'
            : 'Backend API disconnected'}
      </div>

      {/* Left: Mobile trigger & Page Breadcrumbs */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileMenu}
          type="button"
          className="flex md:hidden h-9 w-9 items-center justify-center rounded-[8px] border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 light:border-slate-200 light:hover:bg-slate-100"
          aria-label="Open navigation menu"
        >
          <Menu className="h-4 w-4" />
        </button>

        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold tracking-tight text-slate-100 light:text-slate-900">
              {title}
            </span>
            <span className="text-slate-600 light:text-slate-300">/</span>
            <span className="text-xs text-slate-400 light:text-slate-500 hidden sm:inline">
              {subtitle}
            </span>
          </div>
        </div>
      </div>

      {/* Right: Actions, Health Badge, Theme Toggle */}
      <div className="flex items-center gap-2.5">
        {/* Command palette hint button */}
        <button
          onClick={onFocusComposer}
          type="button"
          className="hidden lg:flex items-center gap-1.5 rounded-[8px] border border-slate-800 bg-slate-900/60 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 light:border-slate-200 light:bg-slate-100 light:text-slate-600"
          title="Focus prompt composer (Ctrl+K)"
        >
          <Search className="h-3 w-3" />
          <span>Quick Ask</span>
          <kbd className="ml-1 rounded border border-slate-700 bg-slate-800 px-1 py-0.2 text-[10px] font-mono-code text-slate-300 light:border-slate-300 light:bg-white light:text-slate-700">
            Ctrl+K
          </kbd>
        </button>

        {/* Academic Edition Suite Badge */}
        <Badge variant="cyan" size="xs" className="hidden sm:inline-flex border border-cyan-500/30 bg-cyan-500/10 text-cyan-300">
          Academic Suite
        </Badge>

        {/* Live Backend Connection Indicator */}
        <ConnectionBadge onOpenCapabilities={onOpenCapabilities} />

        {/* Theme Toggle */}
        <ThemeToggle compact />
      </div>
    </header>
  )
}
