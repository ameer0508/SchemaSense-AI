import { useState } from 'react'
import {
  Activity,
  Check,
  Cpu,
  Database,
  ExternalLink,
  Info,
  Lock,
  Moon,
  RefreshCw,
  Server,
  Sun,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { useBackendHealth } from '@/hooks/useBackendHealth'
import { useTheme } from '@/hooks/useTheme'
import { useActiveDatabase, useDatabases } from '@/hooks/useDatabase'
import { getApiBaseUrl, setApiBaseUrl } from '@/services/apiClient'

export function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { state, health, capabilities, latencyMs, refetch, error } = useBackendHealth()
  const { data: activeDatabase } = useActiveDatabase()
  const { data: databases } = useDatabases()

  const [apiUrl, setApiUrl] = useState<string>(() => getApiBaseUrl())
  const [saveStatus, setSaveStatus] = useState<string | null>(null)
  const [testing, setTesting] = useState<boolean>(false)

  const handleSaveApiUrl = () => {
    setApiBaseUrl(apiUrl)
    setSaveStatus('Endpoint saved!')
    refetch()
    setTimeout(() => setSaveStatus(null), 2500)
  }

  const handleResetApiUrl = () => {
    setApiBaseUrl(null)
    const def = getApiBaseUrl()
    setApiUrl(def)
    setSaveStatus('Reset to default (http://127.0.0.1:8001)')
    refetch()
    setTimeout(() => setSaveStatus(null), 2500)
  }

  const handleTestConnection = () => {
    setTesting(true)
    refetch()
    setTimeout(() => setTesting(false), 800)
  }



  return (
    <div className="space-y-8 max-w-4xl">
      {/* Page Header */}
      <div className="pb-4 border-b border-slate-800 light:border-slate-200">
        <h1 className="text-xl font-bold tracking-tight text-slate-100 light:text-slate-900">
          Settings &amp; Configuration
        </h1>
        <p className="mt-1 text-xs text-slate-400 light:text-slate-600">
          Manage application appearance, backend API connections, system capabilities, and AI provider architecture.
        </p>
      </div>

      {/* Section 1: Appearance & Theme */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance &amp; Theme</CardTitle>
          <CardDescription>
            Choose your interface theme. Optimized for high contrast and long developer sessions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-lg">
            <button
              onClick={() => setTheme('dark')}
              className={`flex items-center gap-3.5 rounded-[12px] border p-3.5 text-left transition-all ${
                theme === 'dark'
                  ? 'border-indigo-500 bg-indigo-500/10 text-white shadow-sm ring-1 ring-indigo-500/30'
                  : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="p-2.5 rounded-lg bg-slate-800 text-indigo-400">
                <Moon className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-100">Dark Theme (Default)</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Midnight surfaces, high-contrast code typography
                </div>
              </div>
            </button>

            <button
              onClick={() => setTheme('light')}
              className={`flex items-center gap-3.5 rounded-[12px] border p-3.5 text-left transition-all ${
                theme === 'light'
                  ? 'border-indigo-500 bg-indigo-500/10 text-slate-900 shadow-sm ring-1 ring-indigo-500/30'
                  : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 light:border-slate-200 light:bg-slate-50'
              }`}
            >
              <div className="p-2.5 rounded-lg bg-slate-200 text-amber-500">
                <Sun className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-800 light:text-slate-900">Light Theme</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Clean slate canvas, crisp hair-line borders
                </div>
              </div>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Section 2: Backend API Connection */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Server className="h-4 w-4 text-indigo-400" />
              <span>Backend API Server Endpoint</span>
            </CardTitle>
            <Badge
              variant={state === 'connected' ? 'success' : state === 'checking' ? 'warning' : 'error'}
              size="xs"
              dot
            >
              {state === 'connected' ? 'Connected' : state === 'checking' ? 'Connecting...' : 'Disconnected'}
            </Badge>
          </div>
          <CardDescription>
            Configure the target FastAPI backend URL. By default, it reads from VITE_API_BASE_URL (port 8001).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-300 light:text-slate-700">
              API Base URL
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder="http://127.0.0.1:8001"
                className="flex-1 rounded-[8px] border border-slate-800 bg-slate-950/70 px-3.5 py-2 font-mono-code text-xs text-slate-200 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 light:border-slate-300 light:bg-white light:text-slate-800"
              />
              <div className="flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSaveApiUrl}
                >
                  Save URL
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleTestConnection}
                  isLoading={testing}
                  leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
                >
                  Test
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleResetApiUrl}
                >
                  Reset
                </Button>
              </div>
            </div>
            {saveStatus && (
              <span className="text-[11px] text-emerald-400 font-medium">{saveStatus}</span>
            )}
          </div>

          {/* Connection Status Box */}
          <div className="rounded-[10px] border border-slate-800 bg-slate-950/50 p-4 text-xs space-y-2.5 light:border-slate-200 light:bg-slate-50">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 light:border-slate-200">
              <span className="text-slate-400">Connection State:</span>
              <span className="font-semibold text-slate-200 uppercase tracking-wide">
                {state}
              </span>
            </div>
            {state === 'connected' && health && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Service Name:</span>
                  <span className="text-slate-200 font-medium">{health.service}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Backend Version:</span>
                  <span className="font-mono-code text-slate-200">v{health.version}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Service Uptime:</span>
                  <span className="font-mono-code text-slate-200">{health.uptime_seconds}s</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Round-trip Ping Latency:</span>
                  <span className="font-mono-code text-emerald-400 font-semibold">{latencyMs} ms</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Environment:</span>
                  <span className="text-slate-200 font-mono-code uppercase text-[11px]">{health.environment}</span>
                </div>
              </>
            )}
            {state === 'disconnected' && (
              <div className="text-rose-400 text-[11px] leading-relaxed">
                <p className="font-semibold mb-1">Failed to establish connection to backend API</p>
                <p className="text-slate-400 mb-2">{error || 'Server unreachable at the specified URL.'}</p>
                <div className="font-mono-code bg-black/40 rounded px-2.5 py-1.5 text-[10px] text-slate-300 select-all">
                  cd backend &amp;&amp; uvicorn app.main:app --port 8001
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Section 2b: Database Foundation & Storage Policy */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-4 w-4 text-indigo-400" />
            <span>Database Foundation &amp; Storage Policy</span>
          </CardTitle>
          <CardDescription>
            Active SQLite connection parameters, local storage isolation, and registered database metrics.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-[10px] border border-slate-800 divide-y divide-slate-800/80 text-xs overflow-hidden light:border-slate-200 light:divide-slate-200">
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Current Active Database</span>
              <div className="flex items-center gap-2 font-mono-code">
                <span className="font-semibold text-slate-100 light:text-slate-900">
                  {activeDatabase ? activeDatabase.name : 'None'}
                </span>
                {activeDatabase && (
                  <Badge variant="indigo" size="xs">
                    {activeDatabase.table_count} Tables
                  </Badge>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Database Engine</span>
              <div className="flex items-center gap-1.5 font-mono-code text-slate-200">
                <span>SQLite 3 (C-Library Engine)</span>
                <Badge variant="success" size="xs" dot>
                  Read-Only Mode
                </Badge>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Registered Databases Count</span>
              <span className="font-mono-code text-slate-200 font-semibold">
                {databases?.length || 0} local databases
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Storage Security Policy</span>
              <span className="text-slate-300 font-medium">
                Backend-isolated storage with strict path traversal rejection &amp; integrity verification
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Demonstration Database</span>
              <span className="text-indigo-400 font-medium">
                Campus Intelligence (7 relational tables, synthetic records, protected)
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 3: Live System Capabilities Inspection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" />
            <span>Available System Capabilities</span>
          </CardTitle>
          <CardDescription>
            Reported dynamically from GET /api/capabilities on the active backend server.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-[8px] bg-slate-950/60 border border-slate-800 text-xs light:bg-slate-50 light:border-slate-200">
              <div>
                <div className="font-semibold text-slate-200 light:text-slate-800">
                  {capabilities?.product || 'SchemaSense AI'} — {capabilities?.phase || 'Phase 1 - Foundation'}
                </div>
                <div className="text-[11px] text-slate-400 light:text-slate-500 mt-0.5">
                  {capabilities?.phase_description || 'Core client-server architecture, typed schemas, and capability discovery.'}
                </div>
              </div>
              <Badge variant="indigo" size="sm">
                v{capabilities?.version || '0.1.0'}
              </Badge>
            </div>

            <div className="rounded-[8px] border border-slate-800/80 divide-y divide-slate-800 text-xs overflow-hidden light:border-slate-200 light:divide-slate-200">
              {capabilities?.capabilities ? (
                Object.entries(capabilities.capabilities).map(([key, enabled]) => (
                  <div
                    key={key}
                    className="flex items-center justify-between p-2.5 bg-slate-900/40 light:bg-white"
                  >
                    <span className="font-mono-code text-[11px] text-slate-300 light:text-slate-700">
                      {key}
                    </span>
                    {enabled ? (
                      <Badge variant="success" size="xs" dot>
                        <Check className="h-3 w-3 mr-1" /> Active
                      </Badge>
                    ) : (
                      <Badge variant="outline" size="xs">
                        Inactive in Phase 1
                      </Badge>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-4 text-center text-xs text-slate-500">
                  Connect backend to inspect live capability flags.
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 4: Live AI Model Engine Status & Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-cyan-400" />
              <span>Generative AI Engine &amp; Transformer Runtime</span>
            </CardTitle>
            <Badge
              variant={
                capabilities?.capabilities?.natural_language_sql ? 'success' : 'outline'
              }
              size="xs"
              dot
            >
              {capabilities?.capabilities?.natural_language_sql
                ? 'Phase 4 Active'
                : 'Inactive'}
            </Badge>
          </div>
          <CardDescription>
            Configured runtime transformer model, hardware device acceleration, and lazy-loading lifecycle.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-[10px] bg-cyan-500/10 border border-cyan-500/20 p-3.5 text-xs text-cyan-300">
            <div className="flex items-start gap-2">
              <Lock className="h-4 w-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Local Open-Weight Transformer</span>
                <p className="mt-0.5 text-[11px] text-slate-300 leading-relaxed">
                  SchemaSense AI runs local, open-weight language models (Qwen2.5-Coder-1.5B-Instruct) using Hugging Face Transformers. Zero paid subscription APIs or external cloud credentials are required.
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[10px] border border-slate-800 divide-y divide-slate-800/80 text-xs overflow-hidden light:border-slate-200 light:divide-slate-200">
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Primary Runtime Model</span>
              <span className="font-mono-code font-semibold text-cyan-300 light:text-cyan-700">
                Qwen/Qwen2.5-Coder-1.5B-Instruct
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Model Parameter Scale</span>
              <span className="font-mono-code text-slate-200">1.54 Billion (Decoder-Only)</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Execution Hardware</span>
              <span className="font-mono-code text-slate-200">CPU Execution (Torch Inference Mode)</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">AST Static Validator</span>
              <span className="font-mono-code text-emerald-400 font-medium">SQLGlot (SQLite Dialect AST)</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Max Generation Tokens</span>
              <span className="font-mono-code text-slate-200">384 tokens</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Decoding Strategy</span>
              <span className="font-mono-code text-slate-200">Greedy Decoding (temperature = 0.0)</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 5: Application Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-4 w-4 text-slate-400" />
            <span>Application Information &amp; Architecture Specs</span>
          </CardTitle>
          <CardDescription>
            System details, semantic versioning, and API documentation links.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-[10px] border border-slate-800 divide-y divide-slate-800/80 text-xs overflow-hidden light:border-slate-200 light:divide-slate-200">
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Product Name</span>
              <span className="font-semibold text-slate-200 light:text-slate-900">SchemaSense AI</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Subtitle</span>
              <span className="text-slate-300 light:text-slate-700">Natural Language. Precise SQL.</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">Release Stage</span>
              <span className="text-cyan-400 font-semibold font-mono-code">Phase 4 — Real Generative AI &amp; Schema-Aware SQL</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">FastAPI Interactive Docs</span>
              <a
                href="http://127.0.0.1:8001/docs"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium"
              >
                <span>/docs (Swagger UI)</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950/40 light:bg-white">
              <span className="text-slate-400">ReDoc API Reference</span>
              <a
                href="http://127.0.0.1:8001/redoc"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-medium"
              >
                <span>/redoc</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
