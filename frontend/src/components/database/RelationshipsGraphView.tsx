import { useState } from 'react'
import { ArrowRight, Link2, Search, Table } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import type { RelationshipMetadata } from '@/types/database'

interface RelationshipsGraphViewProps {
  relationships: RelationshipMetadata[]
  selectedTableName?: string
}

export function RelationshipsGraphView({
  relationships,
  selectedTableName,
}: RelationshipsGraphViewProps) {
  const [filterQuery, setFilterQuery] = useState('')

  const filtered = relationships.filter((rel) => {
    const q = filterQuery.toLowerCase()
    return (
      rel.source_table.toLowerCase().includes(q) ||
      rel.target_table.toLowerCase().includes(q) ||
      rel.source_column.toLowerCase().includes(q) ||
      rel.target_column.toLowerCase().includes(q)
    )
  })

  if (relationships.length === 0) {
    return (
      <div className="rounded-[12px] border border-slate-800 bg-slate-900/30 p-8 text-center light:border-slate-200 light:bg-white">
        <Link2 className="h-8 w-8 text-slate-500 mx-auto mb-2" />
        <h4 className="text-xs font-semibold text-slate-200 light:text-slate-800">
          No Explicit Foreign Key Relationships
        </h4>
        <p className="mt-1 text-xs text-slate-400 light:text-slate-600 max-w-sm mx-auto">
          This SQLite database does not have declared foreign key constraints. Relationships are
          extracted strictly from verified SQLite schema constraints without unverified heuristic guesses.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Search Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Link2 className="h-4 w-4 text-indigo-400" />
          <span className="text-xs font-semibold text-slate-200 light:text-slate-800">
            Relational Constraint Graph
          </span>
          <Badge variant="neutral" size="xs">
            {relationships.length} Relationships
          </Badge>
        </div>

        <div className="relative w-64">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter relationships..."
            className="w-full rounded-[8px] border border-slate-800 bg-slate-900/60 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 light:border-slate-300 light:bg-white light:text-slate-900"
          />
        </div>
      </div>

      {/* Relationship Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filtered.map((rel) => {
          const isRelatedToSelection =
            selectedTableName &&
            (rel.source_table === selectedTableName || rel.target_table === selectedTableName)

          return (
            <div
              key={rel.id}
              className={`rounded-[12px] border p-4 transition-all ${
                isRelatedToSelection
                  ? 'border-indigo-500/50 bg-indigo-500/5 shadow-sm'
                  : 'border-slate-800 bg-slate-950/60 hover:border-slate-700 light:border-slate-200 light:bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-3 text-[11px] text-slate-400 font-mono-code">
                <span className="flex items-center gap-1 text-slate-300 light:text-slate-700 font-semibold">
                  <Table className="h-3 w-3 text-indigo-400" />
                  {rel.source_table}
                </span>
                <span className="text-[10px] text-slate-500">
                  {rel.is_composite ? 'COMPOSITE FK' : 'FOREIGN KEY'}
                </span>
              </div>

              {/* Edge Visual */}
              <div className="flex items-center justify-between gap-2 p-2.5 rounded-[8px] bg-slate-900/60 border border-slate-800/80 light:bg-slate-50 light:border-slate-100">
                <div className="flex flex-col min-w-0">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    Child (FK)
                  </span>
                  <span className="text-xs font-mono-code font-medium text-indigo-300 truncate">
                    {rel.source_table}.{rel.source_column}
                  </span>
                </div>

                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 shrink-0">
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>

                <div className="flex flex-col min-w-0 text-right">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                    Parent (PK)
                  </span>
                  <span className="text-xs font-mono-code font-medium text-emerald-300 truncate">
                    {rel.target_table}.{rel.target_column}
                  </span>
                </div>
              </div>

              {/* Composite pairs expansion */}
              {rel.is_composite && rel.composite_pairs && (
                <div className="mt-2.5 space-y-1 text-[11px] font-mono-code text-slate-400">
                  {rel.composite_pairs.map((p, idx) => (
                    <div key={idx} className="flex items-center justify-between px-2 py-1 rounded bg-slate-900/30">
                      <span>{p.from}</span>
                      <span className="text-slate-600">→</span>
                      <span>{p.to}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
