import { clsx } from 'clsx'

interface BrandLogoProps {
  collapsed?: boolean
  showSubtitle?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function BrandLogo({
  collapsed = false,
  showSubtitle = true,
  size = 'md',
  className,
}: BrandLogoProps) {
  const iconSizes = {
    sm: 'h-7 w-7',
    md: 'h-8 w-8',
    lg: 'h-10 w-10',
  }[size]

  return (
    <div className={clsx('flex items-center gap-3 select-none', className)}>
      {/* Custom Vector Emblem */}
      <div
        className={clsx(
          'relative flex items-center justify-center rounded-[10px] bg-gradient-to-br from-indigo-500/20 via-slate-900 to-cyan-500/10 border border-indigo-500/30 p-1.5 shadow-sm shadow-indigo-500/10 transition-transform duration-200 hover:scale-105',
          iconSizes
        )}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-full w-full text-indigo-400"
        >
          {/* Database Stack */}
          <path
            d="M4 6C4 4.34315 7.58172 3 12 3C16.4183 3 20 4.34315 20 6M4 6V18C4 19.6569 7.58172 21 12 21C16.4183 21 20 19.6569 20 18V6M4 6C4 7.65685 7.58172 9 12 9C16.4183 9 20 7.65685 20 6M4 12C4 13.6569 7.58172 15 12 15C16.4183 15 20 13.6569 20 12"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
          {/* Neural Synapse Node */}
          <circle cx="18" cy="5" r="2.5" fill="#06b6d4" />
          <circle cx="18" cy="5" r="4" stroke="#06b6d4" strokeOpacity="0.4" strokeWidth="0.75" />
        </svg>
      </div>

      {/* Brand Text */}
      {!collapsed && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold tracking-tight text-slate-100 light:text-slate-900">
              SchemaSense
            </span>
            <span className="rounded-[5px] bg-indigo-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/25">
              AI
            </span>
          </div>
          {showSubtitle && (
            <span className="mt-1 text-[11px] font-medium text-slate-400 light:text-slate-500">
              Natural Language. Precise SQL.
            </span>
          )}
        </div>
      )}
    </div>
  )
}
