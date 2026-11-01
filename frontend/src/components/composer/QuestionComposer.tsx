import { KeyboardEvent, useEffect, useId, useRef, useState } from 'react'
import {
  AlertCircle,
  CheckSquare,
  CornerDownLeft,
  Loader2,
  Play,
  Wrench,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { SampleSuggestions } from './SampleSuggestions'
import type { DatabaseInfo } from '@/types/database'

interface QuestionComposerProps {
  initialValue?: string
  selectedDialect: string
  onDialectChange: (dialect: string) => void
  activeDatabase?: DatabaseInfo | null
  onGenerate?: (question: string) => void
  onGenerateAndRun?: (question: string, autoCorrect: boolean) => void
  onGenerateOnly?: (question: string) => void
  isLoading?: boolean
  processingStage?: string
}

export function QuestionComposer({
  initialValue = '',
  selectedDialect,
  onDialectChange,
  activeDatabase,
  onGenerate,
  onGenerateAndRun,
  onGenerateOnly,
  isLoading = false,
  processingStage,
}: QuestionComposerProps) {
  const [question, setQuestion] = useState(initialValue)
  const [autoCorrect, setAutoCorrect] = useState(true)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const composerId = useId()

  useEffect(() => {
    if (initialValue) {
      setQuestion(initialValue)
    }
  }, [initialValue])

  const handleClear = () => {
    setQuestion('')
    textareaRef.current?.focus()
  }

  const handleSelectSample = (sample: string) => {
    setQuestion(sample)
    textareaRef.current?.focus()
  }

  const canGenerate = Boolean(
    activeDatabase && question.trim().length >= 2 && !isLoading
  )

  const handleGenerateAndRunAction = () => {
    if (!canGenerate) return
    const q = question.trim()
    if (onGenerateAndRun) {
      onGenerateAndRun(q, autoCorrect)
    } else if (onGenerate) {
      onGenerate(q)
    }
  }

  const handleGenerateOnlyAction = () => {
    if (!canGenerate) return
    const q = question.trim()
    if (onGenerateOnly) {
      onGenerateOnly(q)
    } else if (onGenerate) {
      onGenerate(q)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canGenerate) {
        handleGenerateAndRunAction()
      }
    }
  }

  const dialects = [
    { id: 'sqlite', label: 'SQLite' },
    { id: 'postgresql', label: 'PostgreSQL' },
    { id: 'mysql', label: 'MySQL' },
    { id: 'snowflake', label: 'Snowflake' },
  ]

  const wordCount = question.trim() ? question.trim().split(/\s+/).length : 0

  // Determine disabled reason for user feedback
  let disabledReason: string | null = null
  if (!activeDatabase) {
    disabledReason = 'No database is currently active. Select or connect an active database in the Schema Explorer or header.'
  } else if (question.trim().length < 2) {
    disabledReason = 'Enter a question in plain English (minimum 2 characters) to generate SQL.'
  } else if (isLoading) {
    disabledReason = 'Inference or execution is currently running. Please wait for the current query to complete.'
  }

  return (
    <div className="space-y-4">
      {/* Composer Card Container */}
      <div className="relative rounded-[16px] border border-slate-800 bg-slate-900/70 p-4 shadow-lg backdrop-blur-md transition-all duration-200 focus-within:border-cyan-500/60 focus-within:ring-2 focus-within:ring-cyan-500/20 light:border-slate-200 light:bg-white light:shadow-sm">
        {/* Dialect Selector & Header Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80 light:border-slate-100">
          <div className="flex items-center gap-2">
            <span
              id={`${composerId}-dialect-label`}
              className="text-xs font-semibold text-slate-300 light:text-slate-700"
            >
              Dialect:
            </span>
            <div
              role="radiogroup"
              aria-labelledby={`${composerId}-dialect-label`}
              className="flex items-center gap-1"
            >
              {dialects.map((d) => (
                <button
                  key={d.id}
                  role="radio"
                  aria-checked={selectedDialect === d.id}
                  type="button"
                  onClick={() => onDialectChange(d.id)}
                  className={`rounded-[6px] px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 ${
                    selectedDialect === d.id
                      ? 'bg-cyan-600/20 text-cyan-300 border border-cyan-500/30 light:bg-cyan-100 light:text-cyan-800'
                      : 'text-slate-400 hover:text-slate-200 light:text-slate-600 light:hover:text-slate-900'
                  }`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Auto-Correct Toggle */}
            <label className="flex items-center gap-1.5 cursor-pointer text-xs select-none">
              <input
                type="checkbox"
                checked={autoCorrect}
                onChange={(e) => setAutoCorrect(e.target.checked)}
                className="sr-only"
              />
              <span className={`flex h-4 w-4 items-center justify-center rounded border transition-colors ${
                autoCorrect
                  ? 'border-cyan-500 bg-cyan-600/30 text-cyan-300 light:bg-cyan-100 light:text-cyan-800'
                  : 'border-slate-700 bg-slate-800 text-transparent'
              }`}>
                {autoCorrect && <CheckSquare className="h-3 w-3 text-cyan-400" />}
              </span>
              <span className="text-slate-300 font-medium text-[11px] light:text-slate-700 flex items-center gap-1">
                <Wrench className="h-3 w-3 text-cyan-400" />
                Auto-Correct on Error
              </span>
            </label>

            <span className="text-slate-700 light:text-slate-300">|</span>

            {/* Clear Button */}
            {question && (
              <button
                type="button"
                onClick={handleClear}
                disabled={isLoading}
                className="text-xs text-slate-400 hover:text-slate-200 light:text-slate-500 light:hover:text-slate-800 flex items-center gap-1"
              >
                <X className="h-3 w-3" />
                <span>Clear</span>
              </button>
            )}

            <span className="text-[11px] text-slate-500 font-mono-code">
              {wordCount} {wordCount === 1 ? 'word' : 'words'}
            </span>
          </div>
        </div>

        {/* Text Input Area */}
        <div className="mt-3">
          <label htmlFor="natural-language-composer" className="sr-only">
            Natural language question for database
          </label>
          <textarea
            id="natural-language-composer"
            ref={textareaRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={3}
            placeholder={
              activeDatabase
                ? `Ask a question about ${activeDatabase.name} (e.g. 'Show the top 5 students with highest GPA' or 'How many courses are there?')...`
                : 'Select an active database to begin querying with AI...'
            }
            className="w-full resize-none bg-transparent text-sm leading-relaxed text-slate-100 placeholder:text-slate-500 focus:outline-none light:text-slate-900 light:placeholder:text-slate-400 font-sans disabled:opacity-60"
          />
        </div>

        {/* Footer Actions */}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80 light:border-slate-100">
          <div className="flex items-center gap-2 text-xs text-slate-400 light:text-slate-500">
            {isLoading ? (
              <span className="flex items-center gap-2 text-cyan-400 font-mono-code text-[11px] animate-pulse">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>{processingStage || 'Processing neural inference & database execution...'}</span>
              </span>
            ) : (
              <>
                <span className="flex items-center gap-1">
                  <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono-code text-slate-300 light:border-slate-300 light:bg-slate-100 light:text-slate-700">
                    Enter
                  </kbd>
                  <span>to Run</span>
                </span>
                <span>&middot;</span>
                <span className="flex items-center gap-1">
                  <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 text-[10px] font-mono-code text-slate-300 light:border-slate-300 light:bg-slate-100 light:text-slate-700">
                    Shift + Enter
                  </kbd>
                  <span>for new line</span>
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Secondary Action: Generate SQL Only (Preserves Phase 4 capability) */}
            <Button
              variant="secondary"
              size="sm"
              onClick={handleGenerateOnlyAction}
              disabled={!canGenerate}
              className="text-xs"
              title="Generate SQL without executing against database"
            >
              Generate SQL Only
            </Button>

            {/* Primary Action: Generate & Run (Phase 5 end-to-end execution & self-correction) */}
            <div className="relative group">
              <Button
                variant="primary"
                size="md"
                onClick={handleGenerateAndRunAction}
                disabled={!canGenerate}
                leftIcon={
                  isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                  ) : (
                    <Play className="h-3.5 w-3.5 text-cyan-400 fill-cyan-400/20" />
                  )
                }
                rightIcon={!isLoading ? <CornerDownLeft className="h-3.5 w-3.5 opacity-60" /> : undefined}
                className={!canGenerate ? 'cursor-not-allowed opacity-60' : 'shadow-md shadow-cyan-500/20'}
                aria-disabled={!canGenerate}
                aria-describedby={!canGenerate ? `${composerId}-disabled-reason` : undefined}
              >
                {isLoading ? 'Processing Query...' : 'Generate & Run'}
              </Button>

              {/* Tooltip explaining disabled state */}
              {!canGenerate && disabledReason && (
                <div
                  id={`${composerId}-disabled-reason`}
                  role="tooltip"
                  className="pointer-events-none absolute bottom-full right-0 mb-2 hidden w-64 rounded-[8px] border border-amber-500/30 bg-slate-950/95 p-2 text-xs text-amber-300 shadow-xl backdrop-blur-md group-hover:block group-focus-within:block z-20"
                >
                  <div className="flex items-start gap-1.5">
                    <AlertCircle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
                    <div>
                      <span className="font-semibold">Action Unavailable</span>
                      <p className="mt-0.5 text-[11px] text-slate-300">
                        {disabledReason}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Suggestion Chips */}
      <SampleSuggestions onSelectQuery={handleSelectSample} />
    </div>
  )
}
