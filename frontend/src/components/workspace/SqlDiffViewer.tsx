import { useState } from 'react'
import { Check, Copy, GitCompare } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'

interface SqlDiffViewerProps {
  initialSql: string
  finalSql: string
  explanation?: string | null
  changesMade?: string[]
}

export function SqlDiffViewer({
  initialSql,
  finalSql,
  explanation,
  changesMade = [],
}: SqlDiffViewerProps) {
  const [copiedInitial, setCopiedInitial] = useState(false)
  const [copiedFinal, setCopiedFinal] = useState(false)

  const copyToClipboard = (text: string, setCopied: (v: boolean) => void) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-[16px] border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md light:border-slate-200 light:bg-white space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-3 light:border-slate-100">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <GitCompare className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-100 light:text-slate-900 flex items-center gap-2">
              SQL Self-Correction Comparison
              <Badge variant="indigo" size="xs">
                Before &amp; After
              </Badge>
            </h4>
            <p className="text-[11px] text-slate-400 light:text-slate-500">
              Comparing initial model output against verified corrected query
            </p>
          </div>
        </div>

        {changesMade.length > 0 && (
          <Badge variant="success" size="sm">
            {changesMade.length} {changesMade.length === 1 ? 'repair applied' : 'repairs applied'}
          </Badge>
        )}
      </div>

      {/* Explanation & Changes List */}
      {(explanation || changesMade.length > 0) && (
        <div className="rounded-[12px] border border-cyan-500/20 bg-cyan-500/5 p-3.5 text-xs text-slate-300 light:border-cyan-200 light:bg-cyan-50/50 light:text-slate-700 space-y-2">
          {explanation && (
            <p className="text-cyan-200 font-medium light:text-cyan-800 leading-relaxed">
              {explanation}
            </p>
          )}

          {changesMade.length > 0 && (
            <ul className="space-y-1 text-[11px] text-slate-300 light:text-slate-600 list-disc list-inside">
              {changesMade.map((change, idx) => (
                <li key={idx} className="leading-snug">
                  <span className="font-semibold text-cyan-300 light:text-cyan-700">Change: </span>
                  {change}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Side-by-Side or Stacked Diff Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Initial SQL Candidate */}
        <div className="rounded-[12px] border border-amber-500/30 bg-slate-950/70 p-3.5 light:bg-slate-50 light:border-amber-300 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 light:border-slate-200 text-xs">
              <span className="font-semibold text-amber-400 light:text-amber-600 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                Initial Candidate (Failed)
              </span>
              <button
                type="button"
                onClick={() => copyToClipboard(initialSql, setCopiedInitial)}
                className="text-slate-400 hover:text-slate-200 light:hover:text-slate-700 text-[11px] flex items-center gap-1"
                title="Copy Initial SQL"
              >
                {copiedInitial ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                <span>{copiedInitial ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <pre className="mt-2.5 overflow-x-auto text-xs font-mono-code text-amber-200/90 light:text-amber-900 leading-relaxed whitespace-pre-wrap">
              <code>{initialSql}</code>
            </pre>
          </div>
        </div>

        {/* Corrected Final SQL */}
        <div className="rounded-[12px] border border-emerald-500/30 bg-slate-950/70 p-3.5 light:bg-slate-50 light:border-emerald-300 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 light:border-slate-200 text-xs">
              <span className="font-semibold text-emerald-400 light:text-emerald-600 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Corrected SQL (Accepted)
              </span>
              <button
                type="button"
                onClick={() => copyToClipboard(finalSql, setCopiedFinal)}
                className="text-slate-400 hover:text-slate-200 light:hover:text-slate-700 text-[11px] flex items-center gap-1"
                title="Copy Corrected SQL"
              >
                {copiedFinal ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                <span>{copiedFinal ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <pre className="mt-2.5 overflow-x-auto text-xs font-mono-code text-emerald-300 light:text-emerald-900 leading-relaxed whitespace-pre-wrap">
              <code>{finalSql}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
