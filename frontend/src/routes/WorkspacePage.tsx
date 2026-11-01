import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import {
  AlertCircle,
  ArrowRight,
  Code2,
  Database,
  GitCompare,
  Table,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { QuestionComposer } from '@/components/composer/QuestionComposer'
import { GeneratedSqlViewer } from '@/components/workspace/GeneratedSqlViewer'
import { ModelStatusBar } from '@/components/workspace/ModelStatusBar'
import { ResultsTable } from '@/components/workspace/ResultsTable'
import { CorrectionTimeline } from '@/components/workspace/CorrectionTimeline'
import { useBackendHealth } from '@/hooks/useBackendHealth'
import { useActiveDatabase } from '@/hooks/useDatabase'
import { useGenerateSql } from '@/hooks/useAi'
import { useAiQuery } from '@/hooks/useQueryExecution'
import type { GenerateSQLResponse } from '@/types/ai'
import type { AIQueryResponse } from '@/types/execution'

export function WorkspacePage() {
  const location = useLocation()
  const queryClient = useQueryClient()
  const locationState = location.state as { question?: string; database_id?: string } | null
  const reusedQuestion = locationState?.question || ''

  const [selectedDialect, setSelectedDialect] = useState<string>('sqlite')
  const [activeTab, setActiveTab] = useState<'sql' | 'results' | 'trace'>('sql')
  const [lastQuestion, setLastQuestion] = useState<string>('')
  const [generationResponse, setGenerationResponse] = useState<GenerateSQLResponse | null>(null)
  const [queryResponse, setQueryResponse] = useState<AIQueryResponse | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [processingStage, setProcessingStage] = useState<string>('')
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0)

  const { state, latencyMs, health } = useBackendHealth()
  const { data: activeDatabase } = useActiveDatabase()
  const generateSqlMutation = useGenerateSql()
  const aiQueryMutation = useAiQuery()

  const isLoading = generateSqlMutation.isPending || aiQueryMutation.isPending

  // Track honest elapsed seconds during inference
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>
    if (isLoading) {
      setElapsedSeconds(0)
      const start = Date.now()
      interval = setInterval(() => {
        setElapsedSeconds(Math.floor((Date.now() - start) / 100) / 10)
      }, 100)
    }
    return () => clearInterval(interval)
  }, [isLoading])

  // 1. Primary Action: Generate & Run (End-to-End Query Workflow)
  const handleGenerateAndRun = (question: string, autoCorrect: boolean) => {
    setLastQuestion(question)
    setErrorMessage(null)
    setProcessingStage('Generating SQL and evaluating schema...')

    aiQueryMutation.mutate(
      {
        question,
        database_id: activeDatabase?.id,
        auto_correct: autoCorrect,
        temperature: 0.0,
      },
      {
        onSuccess: (data) => {
          setQueryResponse(data)

          // Also adapt for the Generated SQL Viewer tab
          setGenerationResponse({
            request_id: data.request_id,
            database_id: data.database_id,
            database_name: data.database_name,
            model: data.model,
            question: data.question,
            sql: data.final_sql,
            explanation: data.summary,
            assumptions: [],
            validation: data.validation,
            generation_time_ms: data.total_duration_ms,
            prompt_tokens_estimated: 0,
            execution: {
              status: data.execution?.status || 'not_executed',
              message: data.summary,
            },
          })

          // Smart Tab Routing: If corrections were required, navigate to trace tab; otherwise show results
          if (data.total_correction_attempts > 0) {
            setActiveTab('trace')
          } else if (data.execution && data.execution.status === 'success') {
            setActiveTab('results')
          } else {
            setActiveTab('sql')
          }
          setProcessingStage('')

          // Invalidate history and analytics queries so tabs are immediately up to date
          queryClient.invalidateQueries({ queryKey: ['history'] })
          queryClient.invalidateQueries({ queryKey: ['analytics'] })
        },
        onError: (err: any) => {
          setErrorMessage(
            err.message || 'Execution failed. Please verify AI model readiness and database registration.'
          )
          setProcessingStage('')
        },
      }
    )
  }

  // 2. Secondary Action: Generate SQL Only (Preserves Phase 4 capability)
  const handleGenerateOnly = (question: string) => {
    setLastQuestion(question)
    setErrorMessage(null)
    setProcessingStage('Generating schema-grounded SQL...')

    generateSqlMutation.mutate(
      {
        question,
        database_id: activeDatabase?.id,
        temperature: 0.0,
      },
      {
        onSuccess: (data) => {
          setGenerationResponse(data)
          setActiveTab('sql')
          setProcessingStage('')

          // Invalidate history and analytics
          queryClient.invalidateQueries({ queryKey: ['history'] })
          queryClient.invalidateQueries({ queryKey: ['analytics'] })
        },
        onError: (err: any) => {
          setErrorMessage(
            err.message || 'Generation failed. Please check AI model status and database connection.'
          )
          setProcessingStage('')
        },
      }
    )
  }

  const handleRegenerate = () => {
    if (lastQuestion) {
      handleGenerateAndRun(lastQuestion, true)
    }
  }

  const handleClear = () => {
    setGenerationResponse(null)
    setQueryResponse(null)
    setErrorMessage(null)
  }

  return (
    <div className="space-y-6">
      {/* Hero / Context Banner */}
      <div className="relative overflow-hidden rounded-[20px] border border-slate-800 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-cyan-950/20 p-6 sm:p-8 backdrop-blur-xl shadow-xl light:border-slate-200 light:bg-white light:from-slate-50 light:to-cyan-50/30 light:shadow-sm">
        {/* Glow Accent */}
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -left-20 -bottom-20 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="indigo" size="sm" dot>
                Phase 6 Active · AI Reliability, Persistent History &amp; Analytics
              </Badge>
              {state === 'connected' && (
                <Badge variant="success" size="sm">
                  FastAPI Server v{health?.version || '0.1.0'} ({latencyMs}ms)
                </Badge>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 light:text-slate-900">
              Natural Language. <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">Precise SQL.</span>
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 light:text-slate-600 leading-relaxed">
              SchemaSense AI connects real generative AI to your SQLite database. Queries are generated, statically validated with SQLGlot, executed in a secure read-only sandbox, and automatically self-corrected using execution feedback.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0 text-xs">
            <div className="rounded-[10px] border border-slate-800 bg-slate-950/60 p-3 light:border-slate-200 light:bg-slate-100/70">
              <div className="text-[11px] text-slate-400 font-medium">Core USP Active</div>
              <div className="font-semibold text-cyan-400 light:text-cyan-600 mt-0.5">
                Generate → Validate → Execute → Diagnose → Repair
              </div>
            </div>
            <div className="rounded-[10px] border border-slate-800 bg-slate-950/60 p-3 light:border-slate-200 light:bg-slate-100/70">
              <div className="text-[11px] text-slate-400 font-medium">Sandbox Security</div>
              <div className="font-semibold text-emerald-400 light:text-emerald-600 mt-0.5">
                SQLite Authorizer + Timeout Interruption
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Status Bar */}
      <ModelStatusBar />

      {/* Real Active Database Status Bar */}
      <div className="rounded-[14px] border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md light:border-slate-200 light:bg-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Database className="h-4 w-4" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Active Database:</span>
              <span className="text-xs font-bold text-slate-100 light:text-slate-900 font-mono-code">
                {activeDatabase ? activeDatabase.name : 'No Database Active'}
              </span>
              <Badge variant="indigo" size="xs">
                SQLite 3
              </Badge>
              {activeDatabase && (
                <Badge variant="success" size="xs" dot>
                  Read-Only Mode
                </Badge>
              )}
            </div>

            <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono-code mt-0.5">
              {activeDatabase ? (
                <>
                  <span>{activeDatabase.table_count} tables ready for schema grounding</span>
                  <span>•</span>
                  <span>File: {activeDatabase.filename}</span>
                </>
              ) : (
                <span>No database connected. Connect a database in Schema Explorer.</span>
              )}
            </div>
          </div>
        </div>

        <Link
          to="/schema-explorer"
          className="inline-flex items-center gap-1.5 rounded-[8px] bg-slate-800/80 hover:bg-slate-700/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors light:bg-slate-100 light:text-slate-800 light:hover:bg-slate-200"
        >
          <span>Explore Database Schema</span>
          <ArrowRight className="h-3.5 w-3.5 text-cyan-400" />
        </Link>
      </div>

      {/* Error Callout (if any) */}
      {errorMessage && (
        <div className="rounded-[12px] border border-rose-500/30 bg-rose-500/10 p-4 text-xs text-rose-300 flex items-start gap-3 light:bg-rose-50 light:text-rose-700">
          <AlertCircle className="h-4 w-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Query Processing Failed: </span>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Primary Question Composer */}
      <section aria-label="Question Composer">
        <QuestionComposer
          initialValue={reusedQuestion}
          selectedDialect={selectedDialect}
          onDialectChange={setSelectedDialect}
          activeDatabase={activeDatabase}
          onGenerateAndRun={handleGenerateAndRun}
          onGenerateOnly={handleGenerateOnly}
          isLoading={isLoading}
          processingStage={processingStage}
        />

        {/* Long-Running CPU Inference Live Elapsed Timer Banner */}
        {isLoading && (
          <div className="mt-3 rounded-[12px] border border-indigo-500/30 bg-indigo-500/10 p-3.5 text-xs text-indigo-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 light:bg-indigo-50 light:border-indigo-200 light:text-indigo-800 animate-pulse">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-indigo-400 animate-ping shrink-0" />
              <span className="font-medium">
                {processingStage || 'Processing query on local CPU (Qwen2.5-Coder-1.5B)...'}
              </span>
              <span className="text-[11px] text-slate-400 light:text-slate-500 hidden sm:inline">
                (Complex schema inference may take 30–50s)
              </span>
            </div>
            <div className="font-mono font-bold text-indigo-300 light:text-indigo-700 bg-indigo-950/60 light:bg-indigo-100 px-2.5 py-1 rounded border border-indigo-800/40 w-fit">
              Elapsed: {elapsedSeconds.toFixed(1)}s
            </div>
          </div>
        )}
      </section>

      {/* Output & Verification Workspace */}
      <section className="space-y-4" aria-label="Output & Verification Workspace">
        {/* Workspace Tab Switcher */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-slate-800 light:border-slate-200">
          <div role="tablist" aria-label="Output and verification workspaces" className="flex items-center gap-1.5">
            <button
              id="tab-results-sandbox"
              role="tab"
              aria-selected={activeTab === 'results'}
              aria-controls="panel-results-sandbox"
              onClick={() => setActiveTab('results')}
              className={`flex items-center gap-2 rounded-[8px] px-3.5 py-1.5 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 ${
                activeTab === 'results'
                  ? 'bg-cyan-600/15 text-cyan-300 border border-cyan-500/30 light:bg-cyan-50 light:text-cyan-700'
                  : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
              }`}
            >
              <Table className="h-4 w-4" />
              <span>Query Results</span>
              {queryResponse?.execution && queryResponse.execution.status === 'success' && (
                <span className="rounded bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 text-[9px] font-mono-code">
                  {queryResponse.execution.row_count} rows
                </span>
              )}
            </button>

            <button
              id="tab-sql-preview"
              role="tab"
              aria-selected={activeTab === 'sql'}
              aria-controls="panel-sql-preview"
              onClick={() => setActiveTab('sql')}
              className={`flex items-center gap-2 rounded-[8px] px-3.5 py-1.5 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 ${
                activeTab === 'sql'
                  ? 'bg-cyan-600/15 text-cyan-300 border border-cyan-500/30 light:bg-cyan-50 light:text-cyan-700'
                  : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
              }`}
            >
              <Code2 className="h-4 w-4" />
              <span>Generated SQL</span>
              <span className="rounded bg-slate-800 px-1 py-0.2 text-[9px] font-mono-code text-cyan-400 light:bg-slate-200">
                AST Verified
              </span>
            </button>

            <button
              id="tab-correction-trace"
              role="tab"
              aria-selected={activeTab === 'trace'}
              aria-controls="panel-correction-trace"
              onClick={() => setActiveTab('trace')}
              className={`flex items-center gap-2 rounded-[8px] px-3.5 py-1.5 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 ${
                activeTab === 'trace'
                  ? 'bg-cyan-600/15 text-cyan-300 border border-cyan-500/30 light:bg-cyan-50 light:text-cyan-700'
                  : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
              }`}
            >
              <GitCompare className="h-4 w-4" />
              <span>Correction Trace</span>
              {queryResponse && queryResponse.total_correction_attempts > 0 ? (
                <span className="rounded bg-indigo-500/20 text-indigo-300 px-1.5 py-0.2 text-[9px] font-mono-code font-bold">
                  {queryResponse.total_correction_attempts} {queryResponse.total_correction_attempts === 1 ? 'repair' : 'repairs'}
                </span>
              ) : (
                <span className="rounded bg-slate-800 px-1 py-0.2 text-[9px] font-mono-code text-slate-400 light:bg-slate-200">
                  Direct pass
                </span>
              )}
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-[11px] font-medium">Read-Only Authorizer Active</span>
          </div>
        </div>

        {/* Tab Panels */}
        <div className="mt-2">
          {activeTab === 'results' && (
            <div id="panel-results-sandbox" role="tabpanel" aria-labelledby="tab-results-sandbox">
              <ResultsTable
                execution={queryResponse?.execution || null}
                semanticAnalysis={queryResponse?.semantic_analysis}
                isLoading={aiQueryMutation.isPending}
              />
            </div>
          )}

          {activeTab === 'sql' && (
            <div id="panel-sql-preview" role="tabpanel" aria-labelledby="tab-sql-preview">
              <GeneratedSqlViewer
                generationResponse={generationResponse}
                isLoading={isLoading}
                selectedDialect={selectedDialect}
                onRegenerate={handleRegenerate}
                onClear={handleClear}
              />
            </div>
          )}

          {activeTab === 'trace' && (
            <div id="panel-correction-trace" role="tabpanel" aria-labelledby="tab-correction-trace">
              <CorrectionTimeline
                attempts={queryResponse?.correction_trace || []}
                finalStatus={queryResponse?.final_status}
                initialSql={queryResponse?.initial_sql}
                finalSql={queryResponse?.final_sql}
                totalDurationMs={queryResponse?.total_duration_ms}
                summary={queryResponse?.summary}
              />
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
