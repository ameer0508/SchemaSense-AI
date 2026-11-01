import {
  Cpu,
  Download,
  Loader2,
  RefreshCw,
  Sparkles,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { useInitializeModel, useModelStatus } from '@/hooks/useAi'

export function ModelStatusBar() {
  const { data: statusData, isLoading, refetch } = useModelStatus()
  const { mutate: initializeModel, isPending: isInitializing } = useInitializeModel()

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-1.5 text-xs text-slate-400 light:border-slate-200 light:bg-slate-50">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />
        <span>Checking AI Model Status...</span>
      </div>
    )
  }

  const modelId = statusData?.model_id || 'Qwen/Qwen2.5-Coder-1.5B-Instruct'
  const shortModelId = modelId.includes('/') ? modelId.split('/')[1] : modelId
  const status = statusData?.status || 'not_loaded'
  const device = (statusData?.device || 'cpu').toUpperCase()
  const isModelLoading = status === 'loading' || isInitializing

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-slate-800/80 bg-slate-900/60 px-3.5 py-2 text-xs backdrop-blur-sm light:border-slate-200 light:bg-white light:shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1.5 font-medium text-slate-200 light:text-slate-800">
          <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
          <span>AI Engine:</span>
          <span className="font-mono text-cyan-300 light:text-cyan-700">{shortModelId}</span>
        </div>

        <Badge variant="outline" size="xs" className="bg-slate-800/40 light:bg-slate-100 text-slate-300 light:text-slate-700">
          <Cpu className="h-3 w-3 mr-1 text-slate-400 inline" />
          {device} Mode
        </Badge>

        {status === 'ready' && (
          <Badge variant="success" size="xs" dot>
            Model Ready
          </Badge>
        )}

        {isModelLoading && (
          <Badge variant="warning" size="xs" className="animate-pulse">
            <Loader2 className="h-3 w-3 mr-1 animate-spin inline" />
            Loading Weights...
          </Badge>
        )}

        {status === 'not_loaded' && !isModelLoading && (
          <Badge variant="warning" size="xs">
            Lazy Loaded (Not in RAM)
          </Badge>
        )}

        {status === 'error' && (
          <Badge variant="error" size="xs" dot>
            Load Error
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-2">
        {status === 'not_loaded' && !isModelLoading && (
          <button
            onClick={() => initializeModel()}
            disabled={isInitializing}
            className="flex items-center gap-1.5 rounded-md bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 px-2.5 py-1 text-xs font-medium transition-colors"
            title="Preload transformer weights into memory now, or let it load automatically on your first query"
          >
            <Download className="h-3 w-3" />
            <span>Preload Weights</span>
          </button>
        )}

        {isModelLoading && (
          <span className="text-[11px] text-amber-300 light:text-amber-600 animate-pulse">
            Initializing model...
          </span>
        )}

        <button
          onClick={() => refetch()}
          title="Refresh AI engine status"
          className="rounded p-1 text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>
    </div>
  )
}
