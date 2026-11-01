import { useState } from 'react'
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Gauge,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import {
  useAnalyticsErrors,
  useAnalyticsOverview,
  useAnalyticsTimeseries,
} from '@/hooks/useAnalytics'

export function InsightsPage() {
  const [selectedDays, setSelectedDays] = useState<number | undefined>(14)

  const { data: overview, isLoading: overviewLoading } = useAnalyticsOverview(selectedDays)
  const { data: timeseries } = useAnalyticsTimeseries(selectedDays || 14)
  const { data: errorDist } = useAnalyticsErrors(selectedDays)

  const formatPercent = (val?: number | null) => {
    if (val === null || val === undefined) return 'N/A'
    return `${(val * 100).toFixed(1)}%`
  }

  const formatMs = (val?: number | null) => {
    if (val === null || val === undefined) return 'N/A'
    return `${val.toFixed(0)} ms`
  }

  const hasData = overview && overview.total_queries > 0

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800 light:border-slate-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 light:text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-indigo-400" />
            <span>Trustworthy Analytics &amp; Telemetry</span>
          </h1>
          <p className="mt-1 text-xs text-slate-400 light:text-slate-600">
            Real performance benchmarks, success ratios, and diagnostic error taxonomies derived strictly from persisted execution history.
          </p>
        </div>

        {/* Time Window Filter Selector */}
        <div className="flex items-center gap-1 bg-slate-900/60 light:bg-slate-100 border border-slate-800 light:border-slate-300 p-1 rounded-[8px]">
          {[
            { label: '7 Days', val: 7 },
            { label: '14 Days', val: 14 },
            { label: '30 Days', val: 30 },
            { label: 'All Time', val: undefined },
          ].map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => setSelectedDays(item.val)}
              className={`px-2.5 py-1 text-xs font-medium rounded-[6px] transition-colors ${
                selectedDays === item.val
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 light:text-slate-600 light:hover:text-slate-900'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {overviewLoading ? (
        <div className="p-12 text-center text-xs text-slate-400 animate-pulse">
          Aggregating telemetry from query history...
        </div>
      ) : !hasData ? (
        <div className="rounded-[14px] border border-slate-800 bg-slate-900/40 p-10 text-center light:border-slate-200 light:bg-white">
          <Activity className="h-10 w-10 text-indigo-400 mx-auto mb-3 opacity-60" />
          <h3 className="text-base font-semibold text-slate-200 light:text-slate-800">
            No Execution History Available Yet
          </h3>
          <p className="mt-2 text-xs text-slate-400 light:text-slate-600 max-w-md mx-auto">
            Analytics metrics and trend charts are calculated dynamically from genuine query executions.
            Head to the Workspace to run Text-to-SQL queries, and their benchmarks will automatically appear here.
          </p>
          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-medium bg-indigo-950/50 text-indigo-300 border border-indigo-800/40 light:bg-indigo-50 light:text-indigo-700">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Zero synthetic data guarantee: metrics reflect real database interactions only
          </div>
        </div>
      ) : (
        <>
          {/* Top KPI Cards Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {/* Total Queries */}
            <Card className="p-4 bg-slate-900/50 border-slate-800 light:bg-white light:border-slate-200">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Recorded Queries</span>
                <Database className="h-4 w-4 text-slate-500" />
              </div>
              <div className="mt-2 text-2xl font-bold text-slate-100 light:text-slate-900">
                {overview.total_queries}
              </div>
              <div className="mt-1 text-[11px] text-slate-500 flex items-center gap-1">
                <span>Total execution workflows</span>
              </div>
            </Card>

            {/* First-Attempt Success Rate */}
            <Card className="p-4 bg-slate-900/50 border-slate-800 light:bg-white light:border-slate-200">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>First-Attempt Success</span>
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-emerald-400 light:text-emerald-600">
                {formatPercent(overview.first_attempt_success_rate)}
              </div>
              <div className="mt-1 text-[11px] text-slate-500">
                {overview.first_attempt_successes} of {overview.total_queries} succeeded directly
              </div>
            </Card>

            {/* Self-Correction Recovery Rate */}
            <Card className="p-4 bg-slate-900/50 border-slate-800 light:bg-white light:border-slate-200">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Correction Recovery Rate</span>
                <Sparkles className="h-4 w-4 text-indigo-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-indigo-400 light:text-indigo-600">
                {formatPercent(overview.correction_success_rate)}
              </div>
              <div className="mt-1 text-[11px] text-slate-500">
                {overview.successes_after_correction} repaired of {overview.total_correction_attempts} attempts
              </div>
            </Card>

            {/* Overall Workflow Success Rate */}
            <Card className="p-4 bg-slate-900/50 border-slate-800 light:bg-white light:border-slate-200">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Overall Success Rate</span>
                <ShieldCheck className="h-4 w-4 text-cyan-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-cyan-400 light:text-cyan-600">
                {formatPercent(overview.overall_success_rate)}
              </div>
              <div className="mt-1 text-[11px] text-slate-500">
                {overview.first_attempt_successes + overview.successes_after_correction} total successful executions
              </div>
            </Card>
          </div>

          {/* Secondary Latency Benchmarks Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Card className="p-3 bg-slate-900/30 border-slate-800 light:bg-white light:border-slate-200 flex items-center gap-3">
              <div className="p-2 rounded-[8px] bg-indigo-950/40 text-indigo-400 border border-indigo-900/40">
                <Cpu className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400">Avg AI Generation Latency</div>
                <div className="text-sm font-bold text-slate-100 light:text-slate-900">
                  {formatMs(overview.avg_generation_duration_ms)}
                </div>
              </div>
            </Card>

            <Card className="p-3 bg-slate-900/30 border-slate-800 light:bg-white light:border-slate-200 flex items-center gap-3">
              <div className="p-2 rounded-[8px] bg-emerald-950/40 text-emerald-400 border border-emerald-900/40">
                <Clock className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400">Avg DB Execution Latency</div>
                <div className="text-sm font-bold text-slate-100 light:text-slate-900">
                  {formatMs(overview.avg_execution_duration_ms)}
                </div>
              </div>
            </Card>

            <Card className="p-3 bg-slate-900/30 border-slate-800 light:bg-white light:border-slate-200 flex items-center gap-3">
              <div className="p-2 rounded-[8px] bg-cyan-950/40 text-cyan-400 border border-cyan-900/40">
                <Gauge className="h-4 w-4" />
              </div>
              <div>
                <div className="text-[11px] text-slate-400">Avg End-to-End Latency</div>
                <div className="text-sm font-bold text-slate-100 light:text-slate-900">
                  {formatMs(overview.avg_total_duration_ms)}
                </div>
              </div>
            </Card>
          </div>

          {/* Charts Row: Timeseries Activity + Outcome Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Chart 1: Daily Activity Timeseries (2 cols) */}
            <Card className="lg:col-span-2 p-5 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xs font-semibold text-slate-200 light:text-slate-800 uppercase tracking-wider">
                    Daily Query Activity
                  </h3>
                  <p className="text-[11px] text-slate-500">Query volume and outcomes over the selected window</p>
                </div>
                <div className="flex items-center gap-3 text-[10px]">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    <span className="text-slate-400">First-Attempt</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-indigo-500" />
                    <span className="text-slate-400">Corrected</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-rose-500" />
                    <span className="text-slate-400">Failed</span>
                  </div>
                </div>
              </div>

              {/* Responsive SVG Bar Chart */}
              {timeseries && timeseries.points.length > 0 ? (
                <div className="space-y-2">
                  <div className="h-48 flex items-end gap-1 sm:gap-2 pt-6 px-1 border-b border-slate-800 light:border-slate-200">
                    {(() => {
                      const maxDaily = Math.max(1, ...timeseries.points.map((p) => p.total))
                      return timeseries.points.map((p) => {
                        const totalHeightPct = Math.round((p.total / maxDaily) * 100)
                        const firstPct = p.total > 0 ? (p.first_attempt_successes / p.total) * 100 : 0
                        const corrPct = p.total > 0 ? (p.corrected_successes / p.total) * 100 : 0
                        const failPct = p.total > 0 ? (p.failures / p.total) * 100 : 0
                        const dateShort = p.date.slice(5) // MM-DD

                        return (
                          <div
                            key={p.date}
                            className="flex-1 flex flex-col items-center h-full justify-end group relative"
                          >
                            {/* Hover tooltip */}
                            <div className="absolute -top-14 hidden group-hover:flex flex-col items-center z-20 bg-slate-950 border border-slate-700 text-[10px] text-slate-200 py-1 px-2 rounded shadow-lg pointer-events-none whitespace-nowrap">
                              <span className="font-semibold">{p.date}</span>
                              <span>Total: {p.total} ({p.first_attempt_successes} 1st, {p.corrected_successes} corr, {p.failures} fail)</span>
                            </div>

                            {/* Stacked bar container */}
                            <div
                              style={{ height: `${Math.max(p.total > 0 ? 8 : 2, totalHeightPct)}%` }}
                              className="w-full max-w-[28px] rounded-t overflow-hidden flex flex-col justify-end bg-slate-800/40 transition-all group-hover:brightness-125"
                            >
                              {p.total === 0 ? (
                                <div className="h-1 bg-slate-800/60 rounded-full" />
                              ) : (
                                <>
                                  {failPct > 0 && <div style={{ height: `${failPct}%` }} className="w-full bg-rose-500" />}
                                  {corrPct > 0 && <div style={{ height: `${corrPct}%` }} className="w-full bg-indigo-500" />}
                                  {firstPct > 0 && <div style={{ height: `${firstPct}%` }} className="w-full bg-emerald-500" />}
                                </>
                              )}
                            </div>

                            {/* Date Label */}
                            <div className="mt-2 text-[9px] text-slate-500 font-mono rotate-45 sm:rotate-0 origin-left">
                              {dateShort}
                            </div>
                          </div>
                        )
                      })
                    })()}
                  </div>
                </div>
              ) : (
                <div className="h-48 flex items-center justify-center text-xs text-slate-500">
                  No activity points recorded in this timeframe
                </div>
              )}
            </Card>

            {/* Chart 2: Outcome Proportions & Breakdown (1 col) */}
            <Card className="p-5 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200 flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-semibold text-slate-200 light:text-slate-800 uppercase tracking-wider mb-1">
                  Outcome Breakdown
                </h3>
                <p className="text-[11px] text-slate-500 mb-4">Proportion of query resolutions</p>

                {/* Horizontal Stacked Proportion Bar */}
                <div className="h-6 w-full rounded-[6px] overflow-hidden flex bg-slate-800/60">
                  {overview.total_queries > 0 ? (
                    <>
                      <div
                        style={{
                          width: `${(overview.first_attempt_successes / overview.total_queries) * 100}%`,
                        }}
                        className="bg-emerald-500 transition-all"
                        title={`First Attempt: ${overview.first_attempt_successes}`}
                      />
                      <div
                        style={{
                          width: `${(overview.successes_after_correction / overview.total_queries) * 100}%`,
                        }}
                        className="bg-indigo-500 transition-all"
                        title={`Corrected: ${overview.successes_after_correction}`}
                      />
                      <div
                        style={{
                          width: `${(overview.total_failures / overview.total_queries) * 100}%`,
                        }}
                        className="bg-rose-500 transition-all"
                        title={`Failed: ${overview.total_failures}`}
                      />
                    </>
                  ) : null}
                </div>

                {/* Legend list */}
                <div className="mt-5 space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-300 light:text-slate-700">
                      <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                      <span>First-Attempt Success</span>
                    </span>
                    <span className="font-semibold text-slate-200 light:text-slate-800">
                      {overview.first_attempt_successes} ({formatPercent(overview.first_attempt_success_rate)})
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-300 light:text-slate-700">
                      <span className="h-2.5 w-2.5 rounded-full bg-indigo-500" />
                      <span>Self-Corrected Success</span>
                    </span>
                    <span className="font-semibold text-slate-200 light:text-slate-800">
                      {overview.successes_after_correction} (
                      {formatPercent(overview.successes_after_correction / overview.total_queries)})
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-300 light:text-slate-700">
                      <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                      <span>Failed / Exhausted</span>
                    </span>
                    <span className="font-semibold text-slate-200 light:text-slate-800">
                      {overview.total_failures} ({formatPercent(overview.total_failures / overview.total_queries)})
                    </span>
                  </div>
                </div>
              </div>

              {/* Qualitative Summary Card */}
              <div className="mt-6 p-3 rounded-[8px] bg-slate-950/60 border border-slate-800 light:bg-slate-50 light:border-slate-200 text-[11px] text-slate-400">
                <div className="font-semibold text-slate-300 light:text-slate-700 mb-1 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Reliability Profile</span>
                </div>
                <div>
                  Most Queried:{' '}
                  <span className="font-medium text-slate-200 light:text-slate-800">
                    {overview.most_used_database || 'N/A'}
                  </span>
                </div>
              </div>
            </Card>
          </div>

          {/* Error Taxonomy Section */}
          <Card className="p-5 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200">
            <h3 className="text-xs font-semibold text-slate-200 light:text-slate-800 uppercase tracking-wider mb-1">
              Diagnosed Error Taxonomy
            </h3>
            <p className="text-[11px] text-slate-500 mb-4">
              Categorized breakdown of query errors triggering self-correction attempts
            </p>

            {errorDist && errorDist.categories.length > 0 ? (
              <div className="space-y-3">
                {errorDist.categories.map((err) => (
                  <div key={err.category} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-slate-200 light:text-slate-800 font-medium">
                        {err.category}
                      </span>
                      <span className="text-slate-400">
                        {err.count} {err.count === 1 ? 'occurrence' : 'occurrences'} ({err.percentage}%)
                      </span>
                    </div>
                    {/* Bar */}
                    <div className="h-2 w-full rounded-full bg-slate-800 light:bg-slate-200 overflow-hidden">
                      <div
                        style={{ width: `${err.percentage}%` }}
                        className="h-full bg-gradient-to-r from-indigo-500 to-rose-500 rounded-full"
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-500 bg-slate-950/40 rounded-[8px] border border-slate-800/60 light:bg-slate-50 light:border-slate-200">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 mx-auto mb-1 opacity-70" />
                <span>Zero recurring error patterns recorded in this timeframe.</span>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
