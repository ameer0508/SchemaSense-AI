import { useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  GitCompare,
  ShieldAlert,
  Sparkles,
  Wrench,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { SqlDiffViewer } from './SqlDiffViewer'
import type { CorrectionAttempt, QueryExecutionStatus } from '@/types/execution'

interface CorrectionTimelineProps {
  attempts: CorrectionAttempt[]
  finalStatus?: QueryExecutionStatus
  initialSql?: string
  finalSql?: string
  totalDurationMs?: number
  summary?: string
}

export function CorrectionTimeline({
  attempts = [],
  finalStatus,
  initialSql,
  finalSql,
  totalDurationMs,
  summary,
}: CorrectionTimelineProps) {
  const [expandedAttempts, setExpandedAttempts] = useState<Record<number, boolean>>({ 1: true, 2: true, 3: true })

  const toggleExpand = (attemptNum: number) => {
    setExpandedAttempts((prev) => ({
      ...prev,
      [attemptNum]: !prev[attemptNum],
    }))
  }

  if (attempts.length === 0) {
    return (
      <div className="rounded-[16px] border border-slate-800 bg-slate-900/40 p-8 text-center backdrop-blur-md light:border-slate-200 light:bg-white space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800 text-slate-400 light:bg-slate-100">
          <GitCompare className="h-6 w-6" />
        </div>
        <h3 className="text-base font-bold text-slate-200 light:text-slate-800">
          No Self-Correction Trace Yet
        </h3>
        <p className="text-xs text-slate-400 light:text-slate-500 max-w-md mx-auto">
          Submit a database question with <strong className="text-cyan-400">Auto-Correct</strong> enabled.
          When queries encounter validation or database execution errors, the agentic repair loop will diagnose and display each repair iteration here.
        </p>
      </div>
    )
  }

  const hasCorrectionOccurred = attempts.length > 1 && Boolean(initialSql && finalSql && initialSql !== finalSql)
  const lastAttempt = attempts[attempts.length - 1]

  return (
    <div className="space-y-6">
      {/* Top Diff Comparison if repairs occurred */}
      {hasCorrectionOccurred && initialSql && finalSql && (
        <SqlDiffViewer
          initialSql={initialSql}
          finalSql={finalSql}
          explanation={lastAttempt?.explanation}
          changesMade={lastAttempt?.changes_made}
        />
      )}

      {/* Summary Banner */}
      <div className="rounded-[14px] border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-md light:border-slate-200 light:bg-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-100 light:text-slate-900">
                Self-Correction Execution Trace
              </span>
              <Badge
                variant={
                  finalStatus === 'success_first_attempt' || finalStatus === 'success_after_correction'
                    ? 'success'
                    : finalStatus === 'unsafe_rejected'
                    ? 'error'
                    : 'warning'
                }
                size="xs"
              >
                {finalStatus?.replace(/_/g, ' ').toUpperCase()}
              </Badge>
            </div>
            <p className="text-[11px] text-slate-400 light:text-slate-600 mt-0.5">
              {summary || `Completed with ${attempts.length} evaluated attempt(s).`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <Badge variant="neutral" size="sm">
            {attempts.length} {attempts.length === 1 ? 'Attempt' : 'Attempts Total'}
          </Badge>
          {totalDurationMs !== undefined && (
            <Badge variant="indigo" size="sm">
              <Clock className="h-3 w-3 mr-1 inline" />
              {totalDurationMs > 1000 ? `${(totalDurationMs / 1000).toFixed(1)}s` : `${totalDurationMs}ms`}
            </Badge>
          )}
        </div>
      </div>

      {/* Attempt Cards Timeline */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800 light:before:bg-slate-200">
        {attempts.map((attempt) => {
          const isExpanded = expandedAttempts[attempt.attempt_number] ?? true
          const isSuccess = attempt.is_accepted

          return (
            <div
              key={attempt.attempt_number}
              className={`relative rounded-[16px] border p-4.5 sm:p-5 transition-all shadow-md backdrop-blur-md ${
                isSuccess
                  ? 'border-emerald-500/30 bg-slate-900/80 light:border-emerald-200 light:bg-emerald-50/20'
                  : attempt.validation_status === 'unsafe'
                  ? 'border-rose-500/30 bg-slate-900/80 light:border-rose-200 light:bg-rose-50/20'
                  : 'border-amber-500/30 bg-slate-900/80 light:border-amber-200 light:bg-amber-50/20'
              }`}
            >
              {/* Timeline Node Icon on Left Rail */}
              <div
                className={`absolute -left-[30px] sm:-left-[38px] top-4.5 flex h-6 w-6 items-center justify-center rounded-full border-2 ${
                  isSuccess
                    ? 'border-emerald-500 bg-slate-950 text-emerald-400'
                    : attempt.validation_status === 'unsafe'
                    ? 'border-rose-500 bg-slate-950 text-rose-400'
                    : 'border-amber-500 bg-slate-950 text-amber-400'
                }`}
              >
                {isSuccess ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : attempt.validation_status === 'unsafe' ? (
                  <ShieldAlert className="h-3.5 w-3.5" />
                ) : (
                  <AlertTriangle className="h-3.5 w-3.5" />
                )}
              </div>

              {/* Card Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3 light:border-slate-200/80">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-100 light:text-slate-900">
                    Attempt #{attempt.attempt_number}
                  </span>
                  <Badge variant={attempt.attempt_type === 'initial' ? 'neutral' : 'indigo'} size="xs">
                    {attempt.attempt_type === 'initial' ? 'Initial Candidate' : 'Self-Correction'}
                  </Badge>
                  <Badge
                    variant={isSuccess ? 'success' : attempt.validation_status === 'unsafe' ? 'error' : 'warning'}
                    size="xs"
                  >
                    {isSuccess
                      ? 'Verified & Accepted'
                      : attempt.validation_status === 'unsafe'
                      ? 'Unsafe Rejected'
                      : attempt.error_category || 'Failed'}
                  </Badge>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400 font-mono-code">
                    Gen: {attempt.generation_time_ms > 1000 ? `${(attempt.generation_time_ms / 1000).toFixed(1)}s` : `${attempt.generation_time_ms}ms`}
                  </span>
                  {attempt.execution_time_ms > 0 && (
                    <span className="text-[11px] text-slate-400 font-mono-code">
                      · Exec: {attempt.execution_time_ms}ms
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => toggleExpand(attempt.attempt_number)}
                    className="ml-2 rounded p-1 text-slate-400 hover:text-slate-200 light:hover:text-slate-800"
                    aria-label={isExpanded ? 'Collapse attempt' : 'Expand attempt'}
                  >
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Card Body */}
              {isExpanded && (
                <div className="mt-3.5 space-y-3">
                  {/* Error Callout if attempt failed */}
                  {!isSuccess && attempt.error_message && (
                    <div className="rounded-[10px] border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200 light:bg-amber-50 light:text-amber-800 space-y-1">
                      <div className="flex items-center gap-1.5 font-semibold text-amber-300 light:text-amber-900">
                        <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                        <span>Diagnostic Feedback ({attempt.error_category || 'Error'}):</span>
                      </div>
                      <p className="font-mono-code text-[11px] pl-5 leading-relaxed">
                        {attempt.error_message}
                      </p>
                    </div>
                  )}

                  {/* Changes Made if this was a repair attempt */}
                  {attempt.changes_made && attempt.changes_made.length > 0 && (
                    <div className="rounded-[10px] border border-indigo-500/20 bg-indigo-500/5 p-3 text-xs text-indigo-300 light:bg-indigo-50/50 light:text-indigo-800">
                      <span className="font-semibold flex items-center gap-1 mb-1">
                        <Wrench className="h-3.5 w-3.5 text-indigo-400" />
                        Repairs Applied by Generative Model:
                      </span>
                      <ul className="list-disc list-inside text-[11px] space-y-0.5 text-slate-300 light:text-slate-700 pl-1">
                        {attempt.changes_made.map((ch, idx) => (
                          <li key={idx}>{ch}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Model Explanation */}
                  {attempt.explanation && (
                    <p className="text-xs text-slate-300 light:text-slate-600 leading-relaxed italic">
                      "{attempt.explanation}"
                    </p>
                  )}

                  {/* SQL Candidate Code Viewer */}
                  <div className="relative rounded-[10px] border border-slate-800 bg-slate-950 p-3 light:border-slate-200 light:bg-slate-900">
                    <pre className="overflow-x-auto text-xs font-mono-code text-cyan-300 light:text-cyan-200 leading-relaxed whitespace-pre-wrap">
                      <code>{attempt.sql}</code>
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
