import { useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  Database,
  Download,
  Info,
  Table,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { exportResultsToCsv } from '@/utils/csvExport'
import type { ExecuteSQLResponse, SemanticAnalysisResult } from '@/types/execution'

interface ResultsTableProps {
  execution: ExecuteSQLResponse | null
  semanticAnalysis?: SemanticAnalysisResult | null
  isLoading?: boolean
}

export function ResultsTable({
  execution,
  semanticAnalysis,
  isLoading = false,
}: ResultsTableProps) {
  const [copiedCell, setCopiedCell] = useState<string | null>(null)
  const [showSemanticDetails, setShowSemanticDetails] = useState<boolean>(true)

  const handleCopyCell = (value: any, coordKey: string) => {
    if (value === null || value === undefined) return
    navigator.clipboard.writeText(String(value))
    setCopiedCell(coordKey)
    setTimeout(() => setCopiedCell(null), 1500)
  }

  const handleExportCsv = () => {
    if (!execution || execution.columns.length === 0) return
    exportResultsToCsv(
      execution.columns,
      execution.rows,
      `query_results_${execution.database_id}_${Date.now()}.csv`,
      execution.is_truncated
    )
  }

  // Loading State
  if (isLoading) {
    return (
      <div className="rounded-[16px] border border-slate-800 bg-slate-900/50 p-12 text-center backdrop-blur-md light:border-slate-200 light:bg-white space-y-4">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse">
          <Database className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-slate-200 light:text-slate-800">
            Executing Read-Only Query...
          </h4>
          <p className="text-xs text-slate-400 light:text-slate-500">
            Running through secure SQLite authorizer sandbox and collecting bounded results.
          </p>
        </div>
      </div>
    )
  }

  // No Execution Yet
  if (!execution) {
    return (
      <div className="rounded-[16px] border border-slate-800 bg-slate-900/40 p-10 text-center backdrop-blur-md light:border-slate-200 light:bg-white space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800 text-slate-400 light:bg-slate-100">
          <Table className="h-6 w-6" />
        </div>
        <h3 className="text-base font-bold text-slate-200 light:text-slate-800">
          No Query Results Yet
        </h3>
        <p className="text-xs text-slate-400 light:text-slate-500 max-w-md mx-auto">
          Submit a question and select <strong className="text-cyan-400">Generate &amp; Run</strong> to execute SQL in the secure read-only sandbox and inspect live database records.
        </p>
      </div>
    )
  }

  // Error Execution State
  if (execution.status !== 'success') {
    return (
      <div className="rounded-[16px] border border-rose-500/30 bg-rose-500/5 p-6 backdrop-blur-md light:bg-rose-50/50 light:border-rose-200 space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-rose-300 light:text-rose-900 flex items-center gap-2">
              Query Execution {execution.status === 'timeout' ? 'Timed Out' : 'Failed'}
              <Badge variant="error" size="xs">
                {execution.error_code || 'EXECUTION_ERROR'}
              </Badge>
            </h4>
            <p className="text-xs text-slate-400 light:text-slate-600 mt-0.5">
              Duration: {execution.duration_ms}ms · Database: {execution.database_id}
            </p>
          </div>
        </div>

        <div className="rounded-[10px] border border-slate-800 bg-slate-950 p-4 font-mono-code text-xs text-rose-300 light:bg-slate-900">
          {execution.error_message || 'An unexpected database error occurred during execution.'}
        </div>
      </div>
    )
  }

  // Semantic Warnings from analyzer
  const effectiveSemantic = semanticAnalysis || execution.semantic_analysis
  const hasSemanticWarnings = effectiveSemantic && !effectiveSemantic.is_semantically_sound && effectiveSemantic.warnings.length > 0

  return (
    <div className="space-y-4">
      {/* Semantic Quality Warning Banner (Addressing Phase 6/8 Semantic Correctness Gap) */}
      {hasSemanticWarnings && (
        <div className="rounded-[14px] border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200 light:bg-amber-50 light:border-amber-200 light:text-amber-800 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-semibold text-amber-300 light:text-amber-900">
              <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
              <span>Semantic Quality Advisory: SQL executed successfully, but results may not answer the question correctly.</span>
            </div>
            <button
              type="button"
              onClick={() => setShowSemanticDetails(!showSemanticDetails)}
              className="text-[11px] underline text-amber-400 hover:text-amber-300"
            >
              {showSemanticDetails ? 'Hide Details' : 'Show Details'}
            </button>
          </div>

          {showSemanticDetails && (
            <div className="pl-6 space-y-2 pt-1 border-t border-amber-500/20">
              {effectiveSemantic.structured_warnings && effectiveSemantic.structured_warnings.length > 0 ? (
                <div className="space-y-2">
                  {effectiveSemantic.structured_warnings.map((sw, idx) => (
                    <div key={idx} className="p-2.5 rounded-[8px] bg-slate-950/60 border border-amber-500/20 text-xs">
                      <div className="flex items-center gap-2 font-semibold text-amber-300 light:text-amber-900">
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase">
                          {sw.code}
                        </span>
                        <span>{sw.message}</span>
                      </div>
                      {sw.evidence && Object.keys(sw.evidence).length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1.5 text-[10px] text-slate-400 light:text-slate-600">
                          {Object.entries(sw.evidence).map(([k, v]) => (
                            <span key={k} className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono light:bg-slate-200 light:border-slate-300">
                              {k}: <strong className="text-slate-200 light:text-slate-800">{String(v)}</strong>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
                  {effectiveSemantic.warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              )}
              {effectiveSemantic.recommendation && (
                <p className="text-[11px] text-amber-100 font-medium light:text-amber-950">
                  <span className="font-bold">Recommendation: </span>
                  {effectiveSemantic.recommendation}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Results Header Bar */}
      <div className="rounded-[14px] border border-slate-800 bg-slate-900/70 p-3.5 backdrop-blur-md light:border-slate-200 light:bg-white flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="text-xs font-bold text-slate-100 light:text-slate-900 flex items-center gap-1.5">
            <Table className="h-4 w-4 text-cyan-400" />
            Query Results
          </span>

          <Badge variant="success" size="sm">
            {execution.row_count} {execution.row_count === 1 ? 'row' : 'rows'}
          </Badge>

          <Badge variant="neutral" size="sm">
            {execution.duration_ms} ms
          </Badge>

          {execution.is_truncated && (
            <Badge variant="warning" size="sm">
              Truncated at {execution.row_count} rows
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleExportCsv}
            disabled={execution.rows.length === 0}
            leftIcon={<Download className="h-3.5 w-3.5 text-cyan-400" />}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Truncation Warning Indicator */}
      {execution.is_truncated && (
        <div className="flex items-center gap-2 rounded-[10px] border border-amber-500/20 bg-amber-500/5 px-3.5 py-2 text-xs text-amber-300 light:bg-amber-50 light:text-amber-800">
          <Info className="h-3.5 w-3.5 text-amber-400 shrink-0" />
          <span>
            Results were capped at the safety limit of {execution.row_count} records. Bounded fetching prevents out-of-memory overhead.
          </span>
        </div>
      )}

      {/* Table Container */}
      {execution.rows.length === 0 ? (
        <div className="rounded-[14px] border border-slate-800 bg-slate-900/40 p-8 text-center light:border-slate-200 light:bg-white space-y-2">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 light:text-indigo-600 bg-indigo-950/40 px-2.5 py-1 rounded-full border border-indigo-800/40 light:bg-indigo-50 light:border-indigo-300">
            <Info className="h-3.5 w-3.5" />
            <span>0 Records Matched</span>
          </div>
          <p className="text-xs text-slate-300 light:text-slate-700 font-medium">
            Query executed successfully in {execution.duration_ms}ms, but returned 0 rows.
          </p>
          <p className="text-[11px] text-slate-500 max-w-md mx-auto">
            A query returning zero rows is syntactically valid and executed without database errors. Verify whether numerical or textual filter criteria match the actual values in the database.
          </p>
        </div>
      ) : (
        <div className="rounded-[14px] border border-slate-800 bg-slate-900/60 shadow-lg backdrop-blur-md overflow-hidden light:border-slate-200 light:bg-white">
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="sticky top-0 z-10 bg-slate-950/90 backdrop-blur-md border-b border-slate-800 text-[11px] font-bold text-slate-300 uppercase tracking-wider light:bg-slate-100 light:border-slate-200 light:text-slate-700">
                <tr>
                  <th scope="col" className="py-2.5 px-3 w-12 text-center text-slate-500 font-mono-code">
                    #
                  </th>
                  {execution.columns.map((col, idx) => (
                    <th scope="col" key={idx} className="py-2.5 px-4 font-semibold text-slate-200 light:text-slate-800">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 light:divide-slate-200/60 font-sans">
                {execution.rows.map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    className="hover:bg-slate-800/40 transition-colors light:hover:bg-slate-50"
                  >
                    <td className="py-2 px-3 text-center text-[10px] font-mono-code text-slate-500 select-none">
                      {rowIdx + 1}
                    </td>
                    {row.map((cell, colIdx) => {
                      const coordKey = `${rowIdx}-${colIdx}`
                      const isNumber = typeof cell === 'number'
                      const isNull = cell === null || cell === undefined
                      const isCopied = copiedCell === coordKey

                      return (
                        <td
                          key={colIdx}
                          onClick={() => handleCopyCell(cell, coordKey)}
                          title="Click to copy cell value"
                          className={`py-2 px-4 whitespace-nowrap cursor-pointer transition-colors relative group ${
                            isNumber ? 'text-right font-mono-code text-cyan-300 light:text-cyan-800' : 'text-slate-200 light:text-slate-800'
                          }`}
                        >
                          {isNull ? (
                            <span className="text-[10px] font-mono-code italic text-slate-500 bg-slate-800/50 light:bg-slate-200 px-1.5 py-0.5 rounded">
                              NULL
                            </span>
                          ) : (
                            <span>{String(cell)}</span>
                          )}

                          {/* Quick copy indicator badge */}
                          {isCopied && (
                            <span className="absolute top-1 right-1 text-[9px] bg-emerald-500 text-slate-950 font-bold px-1 rounded shadow">
                              Copied!
                            </span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
