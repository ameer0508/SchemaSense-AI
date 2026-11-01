import { useState } from 'react'
import { CheckCircle2, ChevronDown, RefreshCw, XCircle } from 'lucide-react'
import { useBackendHealth } from '@/hooks/useBackendHealth'
import { getApiBaseUrl } from '@/services/apiClient'

interface ConnectionBadgeProps {
  compact?: boolean
  className?: string
  onOpenCapabilities?: () => void
}

export function ConnectionBadge({
  compact = false,
  className = '',
  onOpenCapabilities,
}: ConnectionBadgeProps) {
  const { state, health, latencyMs, refetch, error } = useBackendHealth()
  const [showPopover, setShowPopover] = useState(false)
  const [isRetrying, setIsRetrying] = useState(false)

  const handleRetry = () => {
    setIsRetrying(true)
    refetch()
    setTimeout(() => setIsRetrying(false), 800)
  }

  const isConnected = state === 'connected'
  const isChecking = state === 'checking'

  return (
    <div className={`relative inline-block ${className}`}>
      {/* Badge Button */}
      <button
        onClick={() => setShowPopover((prev) => !prev)}
        type="button"
        className={`group flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 ${
          isConnected
            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/15 light:bg-emerald-50 light:text-emerald-700 light:border-emerald-200'
            : isChecking
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-400 hover:bg-amber-500/15'
              : 'border-rose-500/30 bg-rose-500/10 text-rose-400 hover:bg-rose-500/15 light:bg-rose-50 light:text-rose-700 light:border-rose-200'
        }`}
        title="Click to view backend connection details"
        aria-label={`Backend connection status: ${state}`}
      >
        {/* Pulsing Dot */}
        <span className="relative flex h-2 w-2">
          {isConnected && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
          )}
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${
              isConnected ? 'bg-emerald-400' : isChecking ? 'bg-amber-400 animate-pulse' : 'bg-rose-500'
            }`}
          />
        </span>

        {compact ? (
          <span className="sr-only">{state}</span>
        ) : (
          <span className="flex items-center gap-1.5 font-medium tracking-tight">
            <span>{isConnected ? 'API Connected' : isChecking ? 'Connecting...' : 'API Disconnected'}</span>
            {isConnected && latencyMs !== null && (
              <span className="text-[10px] opacity-75 font-mono-code">{latencyMs}ms</span>
            )}
            <ChevronDown className="h-3 w-3 opacity-60 transition-transform group-hover:translate-y-0.5" />
          </span>
        )}
      </button>

      {/* Connection Detail Popover */}
      {showPopover && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowPopover(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-full mt-2 z-50 w-80 rounded-[14px] border border-slate-800 bg-slate-900/95 p-4 shadow-xl shadow-black/50 backdrop-blur-md text-left text-xs light:border-slate-200 light:bg-white light:shadow-lg">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 light:border-slate-100">
              <span className="font-semibold text-slate-200 light:text-slate-900 flex items-center gap-1.5">
                {isConnected ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <XCircle className="h-4 w-4 text-rose-400" />
                )}
                Backend Server Status
              </span>
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className="flex items-center gap-1 text-[11px] font-medium text-indigo-400 hover:text-indigo-300 focus:outline-none disabled:opacity-50"
              >
                <RefreshCw className={`h-3 w-3 ${isRetrying ? 'animate-spin' : ''}`} />
                Retry
              </button>
            </div>

            <div className="mt-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 light:text-slate-500">Target Endpoint</span>
                <span className="font-mono-code text-[11px] text-slate-300 light:text-slate-800 truncate max-w-[170px]">
                  {getApiBaseUrl()}
                </span>
              </div>

              {isConnected && health && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 light:text-slate-500">Service</span>
                    <span className="text-slate-300 light:text-slate-800 font-medium">
                      {health.service}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 light:text-slate-500">Version</span>
                    <span className="font-mono-code text-slate-300 light:text-slate-800">
                      v{health.version}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 light:text-slate-500">Round-trip Latency</span>
                    <span className="font-mono-code text-emerald-400 font-medium">
                      {latencyMs} ms
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400 light:text-slate-500">Environment</span>
                    <span className="text-slate-300 light:text-slate-800 uppercase text-[10px] tracking-wide font-semibold">
                      {health.environment}
                    </span>
                  </div>
                </>
              )}

              {!isConnected && (
                <div className="mt-2 rounded-[8px] bg-rose-500/10 border border-rose-500/20 p-2.5 text-rose-300 text-[11px] leading-relaxed">
                  <p className="font-semibold mb-1">Cannot reach FastAPI backend</p>
                  <p className="text-slate-300 text-[10px] mb-2">
                    {error || 'Connection refused. Ensure the backend server is running locally.'}
                  </p>
                  <div className="font-mono-code bg-black/40 rounded px-2 py-1 text-[10px] text-slate-300 select-all">
                    cd backend &amp;&amp; uvicorn app.main:app --port 8001
                  </div>
                </div>
              )}
            </div>

            {isConnected && onOpenCapabilities && (
              <div className="mt-3 pt-3 border-t border-slate-800/80 light:border-slate-100">
                <button
                  onClick={() => {
                    setShowPopover(false)
                    onOpenCapabilities()
                  }}
                  className="w-full text-center text-[11px] text-indigo-400 hover:text-indigo-300 font-medium py-1 rounded bg-indigo-500/10 hover:bg-indigo-500/20 transition-colors"
                >
                  View Live Capabilities Matrix &rarr;
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
