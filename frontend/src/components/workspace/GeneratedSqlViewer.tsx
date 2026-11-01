import React, { useState } from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Copy,
  Cpu,
  Database,
  FileCode,
  Info,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  Trash2,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import type { GenerateSQLResponse, ValidationStatus } from '@/types/ai'

interface GeneratedSqlViewerProps {
  generationResponse: GenerateSQLResponse | null
  isLoading?: boolean
  selectedDialect: string
  onRegenerate?: () => void
  onClear?: () => void
}

/**
 * Lightweight token-based SQL syntax highlighter.
 */
function highlightSql(sql: string): React.ReactNode[] {
  const lines = sql.split('\n')

  return lines.map((line, lineIdx) => {
    // Check for comment
    const commentIdx = line.indexOf('--')
    let mainPart = line
    let commentPart = ''
    if (commentIdx !== -1) {
      mainPart = line.substring(0, commentIdx)
      commentPart = line.substring(commentIdx)
    }

    // Tokenize mainPart
    const tokens = mainPart.split(/([A-Za-z_][A-Za-z0-9_]*|'[^']*'|\d+(?:\.\d+)?|[,();=><!+*-]|\s+)/g)

    const renderedTokens = tokens.map((token, tokIdx) => {
      if (!token) return null

      const upper = token.toUpperCase()
      // SQL Keywords
      const KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'CROSS',
        'ON', 'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'AND', 'OR',
        'NOT', 'IN', 'IS', 'NULL', 'LIKE', 'BETWEEN', 'UNION', 'ALL', 'WITH', 'CASE',
        'WHEN', 'THEN', 'ELSE', 'END', 'DESC', 'ASC', 'DISTINCT',
      ]

      // Aggregate / Scalar Functions
      const FUNCTIONS = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'COALESCE', 'LENGTH', 'UPPER', 'LOWER']

      if (KEYWORDS.includes(upper)) {
        return (
          <span key={tokIdx} className="text-cyan-400 font-semibold light:text-cyan-600">
            {token}
          </span>
        )
      }

      if (FUNCTIONS.includes(upper)) {
        return (
          <span key={tokIdx} className="text-purple-400 font-semibold light:text-purple-600">
            {token}
          </span>
        )
      }

      // String literals
      if (token.startsWith("'") && token.endsWith("'")) {
        return (
          <span key={tokIdx} className="text-emerald-300 light:text-emerald-600">
            {token}
          </span>
        )
      }

      // Numbers
      if (/^\d+(?:\.\d+)?$/.test(token)) {
        return (
          <span key={tokIdx} className="text-amber-300 light:text-amber-600">
            {token}
          </span>
        )
      }

      // Default identifier / punctuation / whitespace
      return (
        <span key={tokIdx} className="text-slate-200 light:text-slate-800">
          {token}
        </span>
      )
    })

    return (
      <div key={lineIdx} className="leading-relaxed">
        {renderedTokens}
        {commentPart && (
          <span className="text-slate-500 italic light:text-slate-400">{commentPart}</span>
        )}
      </div>
    )
  })
}

export function GeneratedSqlViewer({
  generationResponse,
  isLoading = false,
  selectedDialect,
  onRegenerate,
  onClear,
}: GeneratedSqlViewerProps) {
  const [copied, setCopied] = useState(false)
  const [showExplanation, setShowExplanation] = useState(true)

  const handleCopy = async () => {
    if (!generationResponse?.sql) return
    try {
      await navigator.clipboard.writeText(generationResponse.sql)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback
      setCopied(false)
    }
  }

  // 1. Loading State
  if (isLoading) {
    return (
      <div className="rounded-[14px] border border-cyan-500/30 bg-slate-900/80 p-8 text-center backdrop-blur-md light:border-cyan-200 light:bg-white shadow-lg">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 mb-4 animate-spin">
          <RefreshCw className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-slate-100 light:text-slate-900">
          Generating Schema-Aware SQL...
        </h3>
        <p className="mt-1 text-xs text-slate-400 light:text-slate-600 max-w-md mx-auto">
          Conditioning transformer prompt on SQLite database schema, generating autoregressive token predictions, and performing SQLGlot AST validation.
        </p>
      </div>
    )
  }

  // 2. Empty / Awaiting Input State
  if (!generationResponse) {
    return (
      <div className="rounded-[14px] border border-slate-800 bg-slate-900/40 p-8 text-center backdrop-blur-sm light:border-slate-200 light:bg-white light:shadow-sm">
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800/60 text-slate-400 mb-3 light:bg-slate-100 light:text-slate-600">
          <Sparkles className="h-6 w-6 text-cyan-400" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200 light:text-slate-800">
          Generated SQL Output Editor
        </h3>
        <p className="mt-1 text-xs text-slate-400 light:text-slate-600 max-w-md mx-auto">
          Enter a question in plain English above and click <strong className="text-cyan-400">Generate SQL</strong>. The model will ground the query in your active SQLite database schema.
        </p>
      </div>
    )
  }

  const { sql, explanation, assumptions, validation, model, generation_time_ms, database_name } =
    generationResponse

  // Helper badge for validation status
  const getValidationBadge = (status: ValidationStatus) => {
    switch (status) {
      case 'valid':
        return (
          <Badge variant="success" size="xs" dot>
            AST Valid & Grounded
          </Badge>
        )
      case 'unsafe':
        return (
          <Badge variant="error" size="xs" dot>
            Security Violation (Unsafe)
          </Badge>
        )
      case 'schema_mismatch':
        return (
          <Badge variant="warning" size="xs" dot>
            Schema Mismatch
          </Badge>
        )
      case 'invalid':
        return (
          <Badge variant="error" size="xs" dot>
            Syntax Error
          </Badge>
        )
      case 'unsupported':
        return (
          <Badge variant="warning" size="xs" dot>
            Unsupported AST
          </Badge>
        )
      default:
        return (
          <Badge variant="outline" size="xs">
            Unverified Schema
          </Badge>
        )
    }
  }

  const lines = sql.trim().split('\n')

  return (
    <div
      aria-label="Generated SQL Output Region"
      className="rounded-[14px] border border-slate-800 bg-slate-900/70 overflow-hidden backdrop-blur-sm shadow-xl light:border-slate-200 light:bg-white light:shadow-sm"
    >
      {/* Editor Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 border-b border-slate-800/80 bg-slate-900/90 light:border-slate-100 light:bg-slate-50">
        <div className="flex flex-wrap items-center gap-2">
          <FileCode className="h-4 w-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-200 light:text-slate-800 font-mono-code">
            query.sqlite.sql
          </span>
          <Badge variant="outline" size="xs">
            {selectedDialect.toUpperCase()}
          </Badge>
          {getValidationBadge(validation.status)}
          <Badge variant="outline" size="xs" className="bg-slate-800/50 light:bg-slate-100 text-slate-300 light:text-slate-700">
            <Cpu className="h-3 w-3 mr-1 text-cyan-400 inline" />
            {model.model_id.includes('/') ? model.model_id.split('/')[1] : model.model_id}
          </Badge>
        </div>

        <div className="flex items-center gap-1.5">
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              aria-label="Regenerate SQL query"
              title="Regenerate query"
              className="flex items-center gap-1 rounded-[6px] px-2.5 py-1 text-xs text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors light:bg-slate-100 light:text-slate-700 light:border-slate-200"
            >
              <RefreshCw className="h-3 w-3 text-cyan-400" />
              <span>Regenerate</span>
            </button>
          )}

          <button
            onClick={handleCopy}
            aria-label="Copy generated SQL"
            className="flex items-center gap-1 rounded-[6px] px-2.5 py-1 text-xs text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors light:bg-slate-100 light:text-slate-700 light:border-slate-200"
          >
            {copied ? (
              <>
                <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400 font-medium">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3 w-3 text-slate-400" />
                <span>Copy SQL</span>
              </>
            )}
          </button>

          {onClear && (
            <button
              onClick={onClear}
              aria-label="Clear SQL viewer"
              title="Clear generated query"
              className="flex items-center gap-1 rounded-[6px] px-2 py-1 text-xs text-slate-400 hover:text-rose-400 bg-slate-800/30 hover:bg-rose-500/10 border border-slate-800 hover:border-rose-500/30 transition-colors"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Static Validation Issues Callout (if any) */}
      {validation.issues.length > 0 && (
        <div className="px-4 py-2.5 bg-rose-500/10 border-b border-rose-500/20 text-xs text-rose-300 flex items-start gap-2 light:bg-rose-50 light:text-rose-700">
          <ShieldAlert className="h-4 w-4 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Validation Rejected: </span>
            <ul className="list-disc list-inside mt-0.5 space-y-0.5">
              {validation.issues.map((issue, idx) => (
                <li key={idx}>{issue}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Warnings Callout (if any) */}
      {validation.warnings.length > 0 && (
        <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/20 text-xs text-amber-300 flex items-start gap-2 light:bg-amber-50 light:text-amber-700">
          <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold">Notice: </span>
            <span>{validation.warnings.join(' ')}</span>
          </div>
        </div>
      )}

      {/* Editor Content Area with Line Numbers */}
      <div className="relative p-4 font-mono-code text-xs leading-relaxed overflow-x-auto bg-slate-950/70 light:bg-slate-50 min-h-[160px]">
        {/* Phase 5 Execution Boundary Badge */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full border border-slate-700/60 bg-slate-800/80 px-2.5 py-0.5 text-[10px] font-medium text-slate-400 backdrop-blur-md light:border-slate-300 light:bg-white light:text-slate-600">
          <span>Execution: <strong>Not Executed</strong> (Phase 5 Boundary)</span>
        </div>

        <div className="flex select-none space-x-3">
          {/* Line Numbers */}
          <div className="flex flex-col text-right pr-3 select-none border-r border-slate-800/80 light:border-slate-300 text-slate-600 light:text-slate-400 font-mono-code">
            {lines.map((_, i) => (
              <span key={i}>{i + 1}</span>
            ))}
          </div>

          {/* Syntax Highlighted Code */}
          <div className="flex-1 select-text overflow-x-auto font-mono-code">
            {highlightSql(sql.trim())}
          </div>
        </div>
      </div>

      {/* Explanation and Assumptions Section */}
      {(explanation || (assumptions && assumptions.length > 0)) && (
        <div className="border-t border-slate-800/80 bg-slate-900/40 p-3.5 text-xs light:border-slate-100 light:bg-slate-50/70">
          <div className="flex items-center justify-between mb-1.5">
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="flex items-center gap-1.5 font-semibold text-slate-300 light:text-slate-700 hover:text-white"
            >
              <Info className="h-3.5 w-3.5 text-cyan-400" />
              <span>Query Logic & Model Explanation</span>
              <span className="text-[10px] text-slate-500">
                ({showExplanation ? 'Hide' : 'Show'})
              </span>
            </button>
          </div>

          {showExplanation && (
            <div className="mt-2 space-y-2 text-slate-400 light:text-slate-600">
              {explanation && <p className="leading-relaxed">{explanation}</p>}

              {assumptions && assumptions.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-800/40 light:border-slate-200">
                  <span className="font-medium text-slate-300 light:text-slate-700">Assumptions:</span>
                  <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-400 light:text-slate-600">
                    {assumptions.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Editor Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2 border-t border-slate-800/60 bg-slate-900/60 text-[11px] text-slate-400 light:border-slate-100 light:bg-slate-50">
        <span className="flex items-center gap-2 font-mono-code">
          <span className="flex items-center gap-1">
            <Database className="h-3 w-3 text-cyan-400" />
            <span>Target: {database_name}</span>
          </span>
          <span>&middot;</span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-slate-400" />
            <span>{generation_time_ms} ms</span>
          </span>
          <span>&middot;</span>
          <span>AST: {validation.ast_type || 'Select'}</span>
          <span>&middot;</span>
          <span>Tables: {validation.tables_referenced.join(', ') || 'none'}</span>
        </span>

        <span className="text-[10px] text-slate-500">
          Static AST Checked &middot; Execution scheduled for Phase 5
        </span>
      </div>
    </div>
  )
}
