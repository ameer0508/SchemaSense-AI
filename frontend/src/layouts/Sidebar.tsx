import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Activity,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Database,
  History,
  LayoutGrid,
  Settings,
} from 'lucide-react'
import { BrandLogo } from '@/components/common/BrandLogo'
import { ConnectionBadge } from '@/components/common/ConnectionBadge'
import { ThemeToggle } from '@/components/common/ThemeToggle'

interface SidebarProps {
  onOpenCapabilities: () => void
}

const STORAGE_KEY = 'schemasense_sidebar_collapsed'

export function Sidebar({ onOpenCapabilities }: SidebarProps) {
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true'
    } catch {
      return false
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(collapsed))
    } catch {
      // Ignore storage errors
    }
  }, [collapsed])

  const navItems = [
    {
      to: '/',
      label: 'Workspace',
      icon: LayoutGrid,
      badge: 'Main',
      description: 'Natural language to SQL studio',
    },
    {
      to: '/schemas',
      label: 'Schema Explorer',
      icon: Database,
      badge: null,
      description: 'Tables, keys & relationships',
    },
    {
      to: '/history',
      label: 'Query History',
      icon: History,
      badge: null,
      description: 'Audit log & past executions',
    },
    {
      to: '/insights',
      label: 'Insights',
      icon: BarChart3,
      badge: null,
      description: 'Performance & optimization',
    },
    {
      to: '/settings',
      label: 'Settings',
      icon: Settings,
      badge: null,
      description: 'API & preferences',
    },
  ]

  return (
    <aside
      aria-label="Application Sidebar"
      className={`hidden md:flex flex-col justify-between border-r border-slate-800 bg-slate-950/80 backdrop-blur-xl transition-all duration-300 select-none light:border-slate-200 light:bg-slate-50/90 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Brand Section */}
      <div>
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800/80 light:border-slate-200">
          <NavLink
            to="/"
            className="flex items-center rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
            aria-label="SchemaSense AI Home"
          >
            <BrandLogo collapsed={collapsed} showSubtitle={false} size="sm" />
          </NavLink>

          <button
            onClick={() => setCollapsed((prev) => !prev)}
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded-[6px] border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/40 light:border-slate-200 light:hover:bg-slate-200 light:text-slate-600"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <div key={item.to} className="relative group">
                <NavLink
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-[10px] px-3 py-2 text-xs font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${
                      isActive
                        ? 'bg-indigo-600/15 text-indigo-300 font-semibold border border-indigo-500/30 shadow-sm shadow-indigo-500/10 light:bg-indigo-50 light:text-indigo-700 light:border-indigo-200'
                        : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 light:text-slate-600 light:hover:bg-slate-200/70 light:hover:text-slate-900'
                    } ${collapsed ? 'justify-center px-2' : ''}`
                  }
                  aria-label={collapsed ? item.label : undefined}
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                  {!collapsed && (
                    <span className="flex-1 truncate tracking-tight">{item.label}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span className="rounded-[4px] bg-indigo-500/20 px-1.5 py-0.2 text-[10px] font-mono-code text-indigo-300">
                      {item.badge}
                    </span>
                  )}
                </NavLink>

                {/* Accessible Floating Flyout for Collapsed Mode */}
                {collapsed && (
                  <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:flex group-focus-within:flex flex-col rounded-[8px] border border-slate-800 bg-slate-900 px-2.5 py-1.5 text-xs shadow-xl backdrop-blur-md z-50 whitespace-nowrap light:border-slate-200 light:bg-white light:shadow-md">
                    <span className="font-semibold text-slate-100 light:text-slate-900">
                      {item.label}
                    </span>
                    <span className="text-[10px] text-slate-400 light:text-slate-500">
                      {item.description}
                    </span>
                  </div>
                )}
              </div>
            )
          })}
        </nav>
      </div>

      {/* Bottom Section */}
      <div className="p-3 border-t border-slate-800/80 light:border-slate-200 space-y-3">
        {/* Capability Inspector Button */}
        {!collapsed ? (
          <button
            onClick={onOpenCapabilities}
            type="button"
            className="w-full flex items-center justify-between rounded-[8px] border border-slate-800/80 bg-slate-900/50 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-700 hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 light:border-slate-200 light:bg-white light:text-slate-700"
          >
            <span className="flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-indigo-400" />
              <span>Capabilities</span>
            </span>
            <span className="rounded px-1.5 py-0.2 bg-slate-800 text-[10px] font-mono-code text-slate-400 light:bg-slate-100">
              v0.1.0
            </span>
          </button>
        ) : (
          <div className="flex justify-center relative group">
            <button
              onClick={onOpenCapabilities}
              type="button"
              className="flex h-8 w-8 items-center justify-center rounded-[8px] border border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-indigo-400 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 light:border-slate-200"
              aria-label="System Capabilities Matrix"
            >
              <Activity className="h-4 w-4" />
            </button>
            <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-2 hidden group-hover:block rounded-[6px] border border-slate-800 bg-slate-900 px-2 py-1 text-xs text-slate-200 shadow-lg whitespace-nowrap z-50 light:border-slate-200 light:bg-white light:text-slate-800">
              System Capabilities Matrix
            </div>
          </div>
        )}

        {/* Connection Status & Theme Toggle */}
        <div
          className={`flex items-center justify-between ${
            collapsed ? 'flex-col gap-2' : 'flex-row'
          }`}
        >
          <ConnectionBadge
            compact={collapsed}
            onOpenCapabilities={onOpenCapabilities}
          />
          <ThemeToggle compact={collapsed} />
        </div>
      </div>
    </aside>
  )
}
