import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Database,
  Filter,
  History,
  RotateCcw,
  Search,
  ShieldAlert,
  Sparkles,
  Trash2,
  XCircle,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { useDatabases } from '@/hooks/useDatabase'
import {
  useClearHistory,
  useDeleteHistoryItem,
  useHistoryList,
  useHistorySettings,
  useUpdateHistorySettings,
} from '@/hooks/useHistory'
import type { QueryHistoryRecord } from '@/types/history'

export function QueryHistoryPage() {
  const navigate = useNavigate()

  // State
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDb, setSelectedDb] = useState<string>('')
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Modals state
  const [activeItem, setActiveItem] = useState<QueryHistoryRecord | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [clearConfirmOpen, setClearConfirmOpen] = useState(false)
  const [copiedSql, setCopiedSql] = useState(false)

  // Queries
  const { data: databasesData } = useDatabases()
  const { data: settingsData } = useHistorySettings()
  const { data: historyData, isLoading, isError } = useHistoryList({
    page,
    page_size: pageSize,
    search: searchQuery,
    database_id: selectedDb || undefined,
    status: selectedStatus || undefined,
    sort_desc: true,
  })

  // Mutations
  const updateSettingsMutation = useUpdateHistorySettings()
  const deleteMutation = useDeleteHistoryItem()
  const clearMutation = useClearHistory()

  // Copy helper
  const handleCopySql = (sql: string) => {
    navigator.clipboard.writeText(sql)
    setCopiedSql(true)
    setTimeout(() => setCopiedSql(false), 2000)
  }

  // Reuse Query: navigate to workspace with question in router state without auto-running
  const handleReuseQuery = (item: QueryHistoryRecord) => {
    navigate('/workspace', {
      state: {
        question: item.question,
        database_id: item.database_id,
      },
    })
  }

  // Formatting helpers
  const formatTimestamp = (isoStr: string) => {
    try {
      const date = new Date(isoStr)
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return isoStr
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success_first_attempt':
        return (
          <Badge variant="success" size="sm">
            <CheckCircle2 className="h-3 w-3 mr-1 inline" />
            Success (1st Try)
          </Badge>
        )
      case 'success_after_correction':
        return (
          <Badge variant="indigo" size="sm">
            <Sparkles className="h-3 w-3 mr-1 inline" />
            Self-Corrected
          </Badge>
        )
      case 'success':
        return (
          <Badge variant="success" size="sm">
            <CheckCircle2 className="h-3 w-3 mr-1 inline" />
            Success
          </Badge>
        )
      case 'failed_validation':
        return (
          <Badge variant="warning" size="sm">
            <AlertTriangle className="h-3 w-3 mr-1 inline" />
            Validation Failed
          </Badge>
        )
      case 'failed_execution':
        return (
          <Badge variant="error" size="sm">
            <XCircle className="h-3 w-3 mr-1 inline" />
            Execution Error
          </Badge>
        )
      case 'unsafe_rejected':
        return (
          <Badge variant="error" size="sm">
            <ShieldAlert className="h-3 w-3 mr-1 inline" />
            Security Rejected
          </Badge>
        )
      case 'timeout':
        return (
          <Badge variant="warning" size="sm">
            <Clock className="h-3 w-3 mr-1 inline" />
            Timeout
          </Badge>
        )
      case 'correction_exhausted':
        return (
          <Badge variant="error" size="sm">
            <RotateCcw className="h-3 w-3 mr-1 inline" />
            Exhausted
          </Badge>
        )
      case 'generated_only':
        return (
          <Badge variant="neutral" size="sm">
            Generated Only
          </Badge>
        )
      default:
        return (
          <Badge variant="neutral" size="sm">
            {status}
          </Badge>
        )
    }
  }

  const isEnabled = settingsData?.is_enabled ?? true
  const totalSaved = settingsData?.total_saved_queries ?? 0
  const historyDbSize = settingsData?.history_db_size_bytes
    ? `${(settingsData.history_db_size_bytes / 1024).toFixed(1)} KB`
    : '0 KB'

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800 light:border-slate-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 light:text-slate-900 flex items-center gap-2">
            <History className="h-5 w-5 text-indigo-400" />
            <span>Persistent Query History</span>
          </h1>
          <p className="mt-1 text-xs text-slate-400 light:text-slate-600">
            Durable local audit trail of natural language questions, generated SQL, execution telemetry, and self-correction traces.
          </p>
        </div>

        {/* Privacy Recording Toggle & Clear All */}
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-300 light:text-slate-700 bg-slate-900/60 light:bg-slate-100 border border-slate-800 light:border-slate-300 px-3 py-1.5 rounded-[8px]">
            <span>Record History</span>
            <input
              type="checkbox"
              checked={isEnabled}
              onChange={(e) => updateSettingsMutation.mutate(e.target.checked)}
              className="rounded accent-indigo-600 cursor-pointer h-3.5 w-3.5"
            />
          </label>

          {totalSaved > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setClearConfirmOpen(true)}
              className="text-xs text-rose-400 border-rose-900/40 hover:bg-rose-950/30 light:text-rose-600 light:border-rose-300 light:hover:bg-rose-50"
            >
              <Trash2 className="h-3.5 w-3.5 mr-1" />
              Clear All
            </Button>
          )}
        </div>
      </div>

      {/* History Stats Overview Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="p-3 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Saved Queries</div>
          <div className="mt-1 text-lg font-bold text-slate-100 light:text-slate-900">{totalSaved}</div>
        </Card>
        <Card className="p-3 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Audit DB Size</div>
          <div className="mt-1 text-lg font-bold text-slate-100 light:text-slate-900">{historyDbSize}</div>
        </Card>
        <Card className="p-3 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Filtered Matches</div>
          <div className="mt-1 text-lg font-bold text-indigo-400 light:text-indigo-600">
            {historyData ? historyData.total : 0}
          </div>
        </Card>
        <Card className="p-3 bg-slate-900/40 border-slate-800 light:bg-white light:border-slate-200">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Storage Mode</div>
          <div className="mt-1 text-xs font-semibold text-emerald-400 light:text-emerald-600 flex items-center gap-1.5 pt-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>SQLite WAL (Local)</span>
          </div>
        </Card>
      </div>

      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-slate-900/60 light:bg-slate-50 border border-slate-800 light:border-slate-200 p-3 rounded-[10px]">
        {/* Search text */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setPage(1)
            }}
            placeholder="Search questions or SQL statements..."
            className="w-full rounded-[8px] border border-slate-800 bg-slate-950/60 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 light:border-slate-300 light:bg-white light:text-slate-800"
          />
        </div>

        {/* Database & Status Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Database className="h-3.5 w-3.5" />
            <select
              value={selectedDb}
              onChange={(e) => {
                setSelectedDb(e.target.value)
                setPage(1)
              }}
              className="rounded-[6px] border border-slate-800 bg-slate-950/80 px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/60 light:border-slate-300 light:bg-white light:text-slate-800"
            >
              <option value="">All Databases</option>
              {databasesData?.map((db) => (
                <option key={db.id} value={db.id}>
                  {db.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="h-3.5 w-3.5" />
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value)
                setPage(1)
              }}
              className="rounded-[6px] border border-slate-800 bg-slate-950/80 px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500/60 light:border-slate-300 light:bg-white light:text-slate-800"
            >
              <option value="">All Statuses</option>
              <option value="success_first_attempt">First-Attempt Success</option>
              <option value="success_after_correction">Self-Corrected</option>
              <option value="failed_validation">Validation Failed</option>
              <option value="failed_execution">Execution Error</option>
              <option value="unsafe_rejected">Security Rejected</option>
              <option value="timeout">Timeout</option>
              <option value="generated_only">Generated Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Query History Table */}
      <div className="rounded-[12px] border border-slate-800 bg-slate-950/40 overflow-hidden light:border-slate-200 light:bg-white">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-400 animate-pulse">
            Loading persistent query history records...
          </div>
        ) : isError ? (
          <div className="p-12 text-center text-xs text-rose-400">
            Failed to load query history records. Please check the backend connection.
          </div>
        ) : !historyData || historyData.items.length === 0 ? (
          <div className="p-12 text-center">
            <History className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <div className="text-sm font-semibold text-slate-300 light:text-slate-700">No Query Records Found</div>
            <p className="mt-1 text-xs text-slate-500 max-w-sm mx-auto">
              {searchQuery || selectedDb || selectedStatus
                ? 'No historical queries match your active search and filter criteria.'
                : 'Execute natural language queries in the Workspace to establish a genuine audit record.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300 light:text-slate-700">
              <thead className="bg-slate-900/80 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800 light:bg-slate-100 light:border-slate-200 light:text-slate-600">
                <tr>
                  <th className="py-3 px-4">Question & Database</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-center">Corrections</th>
                  <th className="py-3 px-3">Total Latency</th>
                  <th className="py-3 px-3">Timestamp</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 light:divide-slate-200">
                {historyData.items.map((item) => (
                  <tr
                    key={item.request_id}
                    className="hover:bg-slate-900/40 light:hover:bg-slate-50 transition-colors"
                  >
                    <td className="py-3 px-4 max-w-md">
                      <div className="font-medium text-slate-200 light:text-slate-900 truncate" title={item.question}>
                        {item.question}
                      </div>
                      <div className="mt-0.5 text-[11px] text-slate-500 flex items-center gap-1.5">
                        <Database className="h-3 w-3 text-slate-400" />
                        <span>{item.database_name}</span>
                        <span>•</span>
                        <span className="font-mono text-[10px] text-indigo-400 light:text-indigo-600">
                          {item.generation_mode}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">{getStatusBadge(item.final_status)}</td>
                    <td className="py-3 px-3 text-center whitespace-nowrap">
                      {item.correction_count > 0 ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-900/40 text-indigo-300 border border-indigo-500/30 light:bg-indigo-50 light:text-indigo-700">
                          {item.correction_count}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[11px]">0</span>
                      )}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap text-slate-300 light:text-slate-700 font-mono text-[11px]">
                      {item.total_duration_ms > 0 ? `${item.total_duration_ms.toFixed(0)} ms` : '< 1 ms'}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap text-slate-400 light:text-slate-500 text-[11px]">
                      {formatTimestamp(item.created_at)}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setActiveItem(item)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-950/40 light:text-indigo-600"
                      >
                        Details
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleReuseQuery(item)}
                        className="text-xs"
                        title="Load question into Workspace composer"
                      >
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Reuse
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteConfirmId(item.request_id)}
                        className="text-xs text-slate-500 hover:text-rose-400 hover:bg-rose-950/30"
                        title="Delete query record"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {historyData && historyData.total_pages > 1 && (
          <div className="flex items-center justify-between p-3 border-t border-slate-800 light:border-slate-200 bg-slate-900/40 light:bg-slate-50 text-xs text-slate-400">
            <div>
              Showing Page <span className="font-semibold text-slate-200 light:text-slate-800">{page}</span> of{' '}
              <span className="font-semibold text-slate-200 light:text-slate-800">{historyData.total_pages}</span> (
              {historyData.total} total)
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="text-xs py-1 px-2.5"
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(historyData.total_pages, p + 1))}
                disabled={page >= historyData.total_pages}
                className="text-xs py-1 px-2.5"
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Modal: Query Details */}
      {activeItem && (
        <Modal
          isOpen={true}
          onClose={() => setActiveItem(null)}
          title="Query Audit Details"
          maxWidth="lg"
        >
          <div className="space-y-4 text-xs">
            {/* Natural Question */}
            <div className="p-3 rounded-[8px] bg-slate-900/80 border border-slate-800 light:bg-slate-100 light:border-slate-300">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Natural Language Question
              </div>
              <div className="text-sm font-medium text-slate-100 light:text-slate-900">{activeItem.question}</div>
            </div>

            {/* Metadata Chips */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
              <div className="p-2 rounded bg-slate-900/50 border border-slate-800 light:bg-slate-50 light:border-slate-200">
                <span className="text-slate-500">Database:</span>{' '}
                <span className="font-semibold text-slate-300 light:text-slate-700">{activeItem.database_name}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/50 border border-slate-800 light:bg-slate-50 light:border-slate-200">
                <span className="text-slate-500">Status:</span>{' '}
                <span className="font-semibold text-slate-300 light:text-slate-700">{activeItem.final_status}</span>
              </div>
              <div className="p-2 rounded bg-slate-900/50 border border-slate-800 light:bg-slate-50 light:border-slate-200">
                <span className="text-slate-500">Rows:</span>{' '}
                <span className="font-semibold text-slate-300 light:text-slate-700">
                  {activeItem.row_count !== null ? activeItem.row_count : 'N/A'}
                </span>
              </div>
              <div className="p-2 rounded bg-slate-900/50 border border-slate-800 light:bg-slate-50 light:border-slate-200">
                <span className="text-slate-500">Corrections:</span>{' '}
                <span className="font-semibold text-slate-300 light:text-slate-700">{activeItem.correction_count}</span>
              </div>
            </div>

            {/* Generated & Final SQL */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Final Validated SQL
                </span>
                <button
                  type="button"
                  onClick={() => handleCopySql(activeItem.final_sql)}
                  className="text-slate-400 hover:text-slate-200 flex items-center gap-1 text-[11px]"
                >
                  {copiedSql ? (
                    <>
                      <Check className="h-3 w-3 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy SQL</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-3 rounded-[8px] bg-slate-950 font-mono text-[11px] text-indigo-300 border border-slate-800 overflow-x-auto light:bg-slate-900 light:text-indigo-200">
                {activeItem.final_sql}
              </pre>
            </div>

            {/* Initial SQL if self-corrected */}
            {activeItem.initial_sql && activeItem.initial_sql !== activeItem.final_sql && (
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Initial Candidate SQL (Pre-Correction)
                </span>
                <pre className="p-2.5 rounded-[8px] bg-slate-950/60 font-mono text-[10px] text-amber-300/80 border border-amber-900/30 overflow-x-auto">
                  {activeItem.initial_sql}
                </pre>
              </div>
            )}

            {/* Latency breakdown */}
            <div className="flex items-center gap-4 text-[11px] text-slate-400 border-t border-slate-800 pt-3 light:border-slate-200">
              <div>
                Gen: <span className="font-mono text-slate-200 light:text-slate-800">{activeItem.generation_duration_ms} ms</span>
              </div>
              <div>
                Exec: <span className="font-mono text-slate-200 light:text-slate-800">{activeItem.execution_duration_ms} ms</span>
              </div>
              <div>
                Total: <span className="font-mono text-indigo-400 font-semibold">{activeItem.total_duration_ms} ms</span>
              </div>
            </div>

            {/* Error Diagnostics if failed */}
            {activeItem.error_category && (
              <div className="p-3 rounded-[8px] bg-rose-950/30 border border-rose-900/40 text-rose-300">
                <div className="font-semibold flex items-center gap-1.5">
                  <XCircle className="h-4 w-4" />
                  <span>Diagnosed Category: {activeItem.error_category}</span>
                </div>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800 light:border-slate-200">
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  handleReuseQuery(activeItem)
                  setActiveItem(null)
                }}
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1" />
                Reuse Question in Workspace
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Single Delete Confirmation */}
      {deleteConfirmId && (
        <Modal
          isOpen={true}
          onClose={() => setDeleteConfirmId(null)}
          title="Delete History Record"
          maxWidth="sm"
        >
          <div className="space-y-4 text-xs text-slate-300 light:text-slate-700">
            <p>
              Are you sure you want to permanently delete this query record? This action cannot be undone.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setDeleteConfirmId(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => {
                  deleteMutation.mutate(deleteConfirmId)
                  setDeleteConfirmId(null)
                }}
              >
                Delete Record
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Modal: Clear All Confirmation */}
      {clearConfirmOpen && (
        <Modal
          isOpen={true}
          onClose={() => setClearConfirmOpen(false)}
          title="Clear Entire Query History"
          maxWidth="sm"
        >
          <div className="space-y-4 text-xs text-slate-300 light:text-slate-700">
            <p className="text-rose-400 font-semibold flex items-center gap-1.5">
              <AlertTriangle className="h-4 w-4" />
              <span>Warning: Irreversible Action</span>
            </p>
            <p>
              This will permanently delete all {totalSaved} recorded historical queries and vacuum the history database file.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setClearConfirmOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => {
                  clearMutation.mutate()
                  setClearConfirmOpen(false)
                }}
              >
                Confirm Clear All
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
