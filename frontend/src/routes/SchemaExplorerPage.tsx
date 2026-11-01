import { useState, useMemo } from 'react'
import {
  Check,
  Copy,
  Database,
  Key,
  Link2,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Table as TableIcon,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { DatabaseSelector } from '@/components/database/DatabaseSelector'
import { DatabaseUploadModal } from '@/components/database/DatabaseUploadModal'
import { TableDataPreview } from '@/components/database/TableDataPreview'
import { RelationshipsGraphView } from '@/components/database/RelationshipsGraphView'
import {
  useActiveDatabase,
  useDatabaseSchema,
  useSchemaContext,
} from '@/hooks/useDatabase'

type ExplorerViewMode = 'table-details' | 'global-relationships' | 'schema-context'
type TableDetailTab = 'columns' | 'preview' | 'relationships'

export function SchemaExplorerPage() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null)
  const [tableSearch, setTableSearch] = useState('')
  const [viewMode, setViewMode] = useState<ExplorerViewMode>('table-details')
  const [tableDetailTab, setTableDetailTab] = useState<TableDetailTab>('columns')
  const [copiedContext, setCopiedContext] = useState(false)

  // Fetch active database
  const {
    data: activeDatabase,
    isLoading: isActiveLoading,
    refetch: refetchActive,
  } = useActiveDatabase()

  // Fetch full schema for active database
  const {
    data: schema,
    isLoading: isSchemaLoading,
    isRefetching: isSchemaRefetching,
    refetch: refetchSchema,
  } = useDatabaseSchema(activeDatabase?.id)

  // Fetch LLM schema context
  const { data: schemaContextData } = useSchemaContext(activeDatabase?.id)

  // Auto-select first table if none selected
  const selectedTable = useMemo(() => {
    if (!schema?.tables || schema.tables.length === 0) return null
    if (selectedTableName) {
      const found = schema.tables.find((t) => t.name === selectedTableName)
      if (found) return found
    }
    return schema.tables[0]
  }, [schema, selectedTableName])

  // Filtered tables list
  const filteredTables = useMemo(() => {
    if (!schema?.tables) return []
    if (!tableSearch.trim()) return schema.tables
    const q = tableSearch.toLowerCase()
    return schema.tables.filter((t) => t.name.toLowerCase().includes(q))
  }, [schema, tableSearch])

  // Relationships involving the selected table
  const tableRelationships = useMemo(() => {
    if (!schema?.relationships || !selectedTable) return []
    return schema.relationships.filter(
      (r) => r.source_table === selectedTable.name || r.target_table === selectedTable.name
    )
  }, [schema, selectedTable])

  const handleCopySchemaContext = () => {
    if (!schemaContextData?.prompt_schema_context) return
    navigator.clipboard.writeText(schemaContextData.prompt_schema_context)
    setCopiedContext(true)
    setTimeout(() => setCopiedContext(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Page Header & Database Switcher Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800 light:border-slate-200">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 light:text-slate-900">
            Schema Explorer
          </h1>
          <p className="mt-1 text-xs text-slate-400 light:text-slate-600">
            Real SQLite schema introspection, column inspection, relational graph discovery, and record previews.
          </p>
        </div>

        {/* Database Selector & Actions */}
        <div className="flex items-center gap-2">
          <DatabaseSelector
            activeDatabase={activeDatabase}
            onOpenUpload={() => setUploadModalOpen(true)}
          />

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchActive()
              refetchSchema()
            }}
            title="Refresh database schema"
            disabled={isSchemaRefetching}
            className="h-9 px-2.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isSchemaRefetching ? 'animate-spin text-indigo-400' : ''}`} />
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setUploadModalOpen(true)}
            className="gap-1.5 h-9"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Upload SQLite</span>
          </Button>
        </div>
      </div>

      {/* Database Schema Overview Stats Bar */}
      {schema && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-[12px] border border-slate-800 bg-slate-900/40 p-3.5 light:border-slate-200 light:bg-white">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
              Database Engine
            </span>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-sm font-bold text-slate-100 light:text-slate-900 font-mono-code">
                SQLite 3
              </span>
              <Badge variant="neutral" size="xs">
                Read-Only
              </Badge>
            </div>
          </div>

          <div className="rounded-[12px] border border-slate-800 bg-slate-900/40 p-3.5 light:border-slate-200 light:bg-white">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
              Tables & Views
            </span>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-sm font-bold text-indigo-400 font-mono-code">
                {schema.total_tables}
              </span>
              <span className="text-[11px] text-slate-500">objects</span>
            </div>
          </div>

          <div className="rounded-[12px] border border-slate-800 bg-slate-900/40 p-3.5 light:border-slate-200 light:bg-white">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
              Total Columns
            </span>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-sm font-bold text-emerald-400 font-mono-code">
                {schema.total_columns}
              </span>
              <span className="text-[11px] text-slate-500">attributes</span>
            </div>
          </div>

          <div className="rounded-[12px] border border-slate-800 bg-slate-900/40 p-3.5 light:border-slate-200 light:bg-white">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block">
              Foreign Key Graph
            </span>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="text-sm font-bold text-amber-400 font-mono-code">
                {schema.total_relationships}
              </span>
              <span className="text-[11px] text-slate-500">constraints</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Explorer Workspace */}
      {isSchemaLoading || isActiveLoading ? (
        <div className="flex flex-col items-center justify-center p-20 text-slate-500">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400 mb-3" />
          <span className="text-xs font-medium">Introspecting SQLite database schema...</span>
        </div>
      ) : !schema || schema.tables.length === 0 ? (
        <div className="rounded-[16px] border border-slate-800 bg-slate-900/30 p-12 text-center light:border-slate-200 light:bg-white">
          <Database className="h-10 w-10 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200 light:text-slate-800">
            No Database Active
          </h3>
          <p className="mt-1 text-xs text-slate-400 light:text-slate-600 max-w-md mx-auto">
            Connect the bundled Campus Intelligence demonstration database or upload your own SQLite database file to begin exploring tables and columns.
          </p>
          <div className="mt-4">
            <Button variant="primary" size="sm" onClick={() => setUploadModalOpen(true)}>
              Upload Database File
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Table List Navigation (4 cols) */}
          <div className="lg:col-span-4 rounded-[14px] border border-slate-800 bg-slate-950/60 p-4 space-y-3 light:border-slate-200 light:bg-white">
            {/* View Mode Switcher */}
            <div className="flex items-center rounded-[8px] bg-slate-900/80 p-1 border border-slate-800/80 light:bg-slate-100 light:border-slate-200">
              <button
                type="button"
                onClick={() => setViewMode('table-details')}
                className={`flex-1 rounded-[6px] py-1.5 text-xs font-medium transition-colors flex items-center justify-center gap-1.5 ${
                  viewMode === 'table-details'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
                }`}
              >
                <TableIcon className="h-3 w-3" />
                <span>Tables</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode('global-relationships')}
                className={`flex-1 rounded-[6px] py-1.5 text-xs font-medium transition-colors flex items-center justify-center gap-1.5 ${
                  viewMode === 'global-relationships'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
                }`}
              >
                <Link2 className="h-3 w-3" />
                <span>Graph</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode('schema-context')}
                className={`flex-1 rounded-[6px] py-1.5 text-xs font-medium transition-colors flex items-center justify-center gap-1.5 ${
                  viewMode === 'schema-context'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
                }`}
              >
                <Sparkles className="h-3 w-3" />
                <span>LLM Context</span>
              </button>
            </div>

            {/* Table Search Input */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                value={tableSearch}
                onChange={(e) => setTableSearch(e.target.value)}
                placeholder="Search tables..."
                className="w-full rounded-[8px] border border-slate-800 bg-slate-900/60 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 light:border-slate-300 light:bg-slate-50 light:text-slate-900"
              />
            </div>

            {/* Table Items */}
            <div className="space-y-1 max-h-[540px] overflow-y-auto pr-0.5">
              {filteredTables.map((t) => {
                const isSelected = selectedTable?.name === t.name && viewMode === 'table-details'
                return (
                  <button
                    key={t.name}
                    type="button"
                    onClick={() => {
                      setSelectedTableName(t.name)
                      setViewMode('table-details')
                    }}
                    className={`w-full flex items-center justify-between rounded-[8px] px-3 py-2 text-xs transition-colors text-left ${
                      isSelected
                        ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 light:bg-indigo-50 light:text-indigo-900 light:border-indigo-200'
                        : 'hover:bg-slate-900 text-slate-300 border border-transparent light:text-slate-700 light:hover:bg-slate-100'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <TableIcon
                        className={`h-3.5 w-3.5 shrink-0 ${
                          isSelected ? 'text-indigo-400' : 'text-slate-500'
                        }`}
                      />
                      <span className="font-mono-code font-medium truncate">{t.name}</span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0 font-mono-code text-[10px] text-slate-500">
                      <span>{t.column_count} cols</span>
                      <span>•</span>
                      <span>{t.row_count} rows</span>
                    </div>
                  </button>
                )
              })}

              {filteredTables.length === 0 && (
                <div className="p-4 text-center text-xs text-slate-500">
                  No tables matching '{tableSearch}'
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Detailed View (8 cols) */}
          <div className="lg:col-span-8 rounded-[14px] border border-slate-800 bg-slate-950/60 p-5 light:border-slate-200 light:bg-white min-h-[580px]">
            {/* View Mode: Global Relationships */}
            {viewMode === 'global-relationships' && (
              <RelationshipsGraphView
                relationships={schema.relationships}
                selectedTableName={selectedTable?.name}
              />
            )}

            {/* View Mode: LLM Schema Context */}
            {viewMode === 'schema-context' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-slate-200 light:text-slate-800 uppercase tracking-wider flex items-center gap-2">
                      <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                      <span>Deterministic LLM Schema Context</span>
                    </h3>
                    <p className="text-[11px] text-slate-400 light:text-slate-600 mt-0.5">
                      Compact, deterministic schema representation engineered for Generative AI prompt injection in Phase 4.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="indigo" size="xs">
                      ~{schemaContextData?.token_estimate || 0} Tokens
                    </Badge>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCopySchemaContext}
                      className="h-7 text-xs gap-1"
                    >
                      {copiedContext ? (
                        <>
                          <Check className="h-3 w-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" />
                          <span>Copy Prompt Context</span>
                        </>
                      )}
                    </Button>
                  </div>
                </div>

                <div className="rounded-[10px] border border-slate-800 bg-slate-950 p-4 font-mono-code text-[11px] text-slate-300 leading-relaxed overflow-x-auto max-h-[480px] light:border-slate-200 light:bg-slate-900 light:text-slate-200">
                  <pre>{schemaContextData?.prompt_schema_context || 'Generating schema context...'}</pre>
                </div>
              </div>
            )}

            {/* View Mode: Selected Table Details */}
            {viewMode === 'table-details' && selectedTable && (
              <div className="space-y-5">
                {/* Table Inspector Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80 light:border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      <TableIcon className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-sm font-bold text-slate-100 light:text-slate-900 font-mono-code">
                          {selectedTable.name}
                        </h2>
                        <Badge variant="neutral" size="xs">
                          {selectedTable.type}
                        </Badge>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono-code">
                        {selectedTable.row_count} total rows • {selectedTable.column_count} columns
                      </span>
                    </div>
                  </div>

                  {/* Sub-tab Navigation */}
                  <div className="flex items-center rounded-[8px] bg-slate-900/80 p-0.5 border border-slate-800 light:bg-slate-100 light:border-slate-200">
                    <button
                      type="button"
                      onClick={() => setTableDetailTab('columns')}
                      className={`rounded-[6px] px-3 py-1 text-xs font-medium transition-colors ${
                        tableDetailTab === 'columns'
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
                      }`}
                    >
                      Columns ({selectedTable.columns.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setTableDetailTab('preview')}
                      className={`rounded-[6px] px-3 py-1 text-xs font-medium transition-colors ${
                        tableDetailTab === 'preview'
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
                      }`}
                    >
                      Data Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => setTableDetailTab('relationships')}
                      className={`rounded-[6px] px-3 py-1 text-xs font-medium transition-colors ${
                        tableDetailTab === 'relationships'
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 light:text-slate-600'
                      }`}
                    >
                      Foreign Keys ({tableRelationships.length})
                    </button>
                  </div>
                </div>

                {/* Sub-tab 1: Columns Definition Table */}
                {tableDetailTab === 'columns' && (
                  <div className="rounded-[10px] border border-slate-800 overflow-hidden light:border-slate-200">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-50">
                          <th className="py-2.5 px-3.5 font-semibold text-slate-300 light:text-slate-700">
                            Column
                          </th>
                          <th className="py-2.5 px-3.5 font-semibold text-slate-300 light:text-slate-700">
                            Data Type
                          </th>
                          <th className="py-2.5 px-3.5 font-semibold text-slate-300 light:text-slate-700">
                            Key Constraint
                          </th>
                          <th className="py-2.5 px-3.5 font-semibold text-slate-300 light:text-slate-700">
                            Nullable
                          </th>
                          <th className="py-2.5 px-3.5 font-semibold text-slate-300 light:text-slate-700">
                            Default
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 light:divide-slate-200">
                        {selectedTable.columns.map((col) => (
                          <tr
                            key={col.name}
                            className="hover:bg-slate-900/40 light:hover:bg-slate-50 transition-colors"
                          >
                            <td className="py-2.5 px-3.5 font-mono-code font-semibold text-slate-200 light:text-slate-800 flex items-center gap-1.5">
                              {col.primary_key && (
                                <span title="Primary Key">
                                  <Key className="h-3 w-3 text-amber-400 shrink-0" />
                                </span>
                              )}
                              {col.is_foreign_key && !col.primary_key && (
                                <span title="Foreign Key">
                                  <Link2 className="h-3 w-3 text-indigo-400 shrink-0" />
                                </span>
                              )}
                              <span>{col.name}</span>
                            </td>

                            <td className="py-2.5 px-3.5 font-mono-code text-[11px] text-indigo-300">
                              <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                                {col.data_type}
                              </span>
                            </td>

                            <td className="py-2.5 px-3.5">
                              {col.primary_key ? (
                                <Badge variant="warning" size="xs">
                                  {col.pk_position && col.pk_position > 1
                                    ? `PK (pos ${col.pk_position})`
                                    : 'PRIMARY KEY'}
                                </Badge>
                              ) : col.is_foreign_key ? (
                                <Badge variant="indigo" size="xs">
                                  FK → {col.fk_target_table}.{col.fk_target_column}
                                </Badge>
                              ) : (
                                <span className="text-slate-600">-</span>
                              )}
                            </td>

                            <td className="py-2.5 px-3.5 font-mono-code text-[11px]">
                              {col.nullable ? (
                                <span className="text-emerald-400">YES</span>
                              ) : (
                                <span className="text-slate-500">NO</span>
                              )}
                            </td>

                            <td className="py-2.5 px-3.5 font-mono-code text-[11px] text-slate-400">
                              {col.default_value !== null ? col.default_value : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Sub-tab 2: Paginated Data Preview */}
                {tableDetailTab === 'preview' && activeDatabase && (
                  <TableDataPreview
                    databaseId={activeDatabase.id}
                    tableName={selectedTable.name}
                  />
                )}

                {/* Sub-tab 3: Table Relationships */}
                {tableDetailTab === 'relationships' && (
                  <div className="space-y-3">
                    {tableRelationships.length === 0 ? (
                      <div className="p-8 text-center text-xs text-slate-500 border border-slate-800 rounded-[10px]">
                        No foreign key constraints defined on table '{selectedTable.name}'.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {tableRelationships.map((rel) => {
                          const isOutgoing = rel.source_table === selectedTable.name
                          return (
                            <div
                              key={rel.id}
                              className="flex items-center justify-between p-3 rounded-[10px] border border-slate-800 bg-slate-900/40 text-xs font-mono-code light:border-slate-200 light:bg-slate-50"
                            >
                              <div className="flex items-center gap-2">
                                <Badge variant={isOutgoing ? 'indigo' : 'neutral'} size="xs">
                                  {isOutgoing ? 'REFERENCES (OUTGOING)' : 'REFERENCED BY (INCOMING)'}
                                </Badge>
                                <span className="text-slate-300 light:text-slate-700">
                                  {rel.source_table}.{rel.source_column} → {rel.target_table}.{rel.target_column}
                                </span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload Database Modal */}
      <DatabaseUploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onSuccess={() => {
          refetchActive()
          refetchSchema()
        }}
      />
    </div>
  )
}
