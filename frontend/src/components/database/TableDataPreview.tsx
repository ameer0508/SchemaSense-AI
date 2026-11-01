import { useState } from 'react'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useTablePreview } from '@/hooks/useDatabase'

interface TableDataPreviewProps {
  databaseId: string
  tableName: string
}

export function TableDataPreview({ databaseId, tableName }: TableDataPreviewProps) {
  const [offset, setOffset] = useState(0)
  const pageSize = 20

  const { data: previewData, isLoading, isError, error } = useTablePreview(
    databaseId,
    tableName,
    pageSize,
    offset
  )

  const handleNext = () => {
    if (previewData && offset + pageSize < previewData.total_rows) {
      setOffset(offset + pageSize)
    }
  }

  const handlePrev = () => {
    setOffset(Math.max(0, offset - pageSize))
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-500">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-400 mb-2" />
        <span className="text-xs">Loading records from '{tableName}'...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-6 text-center text-xs text-red-400">
        Failed to load table records: {(error as any)?.message || 'Unknown error'}
      </div>
    )
  }

  if (!previewData || previewData.rows.length === 0) {
    return (
      <div className="p-10 text-center text-xs text-slate-500">
        No records found in table '{tableName}'.
      </div>
    )
  }

  const startRow = previewData.offset + 1
  const endRow = Math.min(previewData.offset + previewData.rows.length, previewData.total_rows)

  return (
    <div className="flex flex-col rounded-[12px] border border-slate-800 bg-slate-950/60 overflow-hidden light:border-slate-200 light:bg-white">
      {/* Records Header & Pagination Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 border-b border-slate-800/80 bg-slate-900/40 light:border-slate-100 light:bg-slate-50">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-200 light:text-slate-800">
            Records Preview
          </span>
          <span className="text-[11px] text-slate-500 font-mono-code">
            Showing {startRow} - {endRow} of {previewData.total_rows} rows
          </span>
          {previewData.is_truncated && (
            <Badge variant="warning" size="xs">
              Bounded View
            </Badge>
          )}
        </div>

        {/* Pagination buttons */}
        <div className="flex items-center gap-1.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrev}
            disabled={offset === 0}
            className="h-7 px-2 text-[11px]"
          >
            <ChevronLeft className="h-3.5 w-3.5 mr-0.5" />
            Prev
          </Button>
          <span className="text-[11px] text-slate-400 font-mono-code px-1">
            Page {Math.floor(offset / pageSize) + 1} of {Math.ceil(previewData.total_rows / pageSize) || 1}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNext}
            disabled={!previewData.is_truncated || endRow >= previewData.total_rows}
            className="h-7 px-2 text-[11px]"
          >
            Next
            <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
          </Button>
        </div>
      </div>

      {/* Horizontal Scrollable Table */}
      <div className="overflow-x-auto max-w-full">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/60 light:border-slate-200 light:bg-slate-100/70">
              <th className="py-2.5 px-3 text-[10px] font-mono-code font-bold uppercase tracking-wider text-slate-500 w-12 text-center">
                #
              </th>
              {previewData.columns.map((col) => (
                <th
                  key={col}
                  className="py-2.5 px-3.5 text-xs font-semibold text-slate-300 light:text-slate-700 whitespace-nowrap"
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col}</span>
                    <span className="text-[10px] font-normal text-slate-500 font-mono-code">
                      {previewData.column_types[col]}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 light:divide-slate-200">
            {previewData.rows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="hover:bg-slate-900/40 light:hover:bg-slate-50 transition-colors"
              >
                <td className="py-2 px-3 text-[10px] font-mono-code text-slate-500 text-center select-none bg-slate-950/20">
                  {startRow + rowIdx}
                </td>
                {previewData.columns.map((col) => {
                  const val = row[col]
                  return (
                    <td
                      key={col}
                      className="py-2 px-3.5 text-xs text-slate-300 light:text-slate-700 whitespace-nowrap font-mono-code max-w-[280px] truncate"
                    >
                      {val === null || val === undefined ? (
                        <span className="text-slate-500 italic text-[10px] px-1 py-0.5 rounded bg-slate-800/40">
                          NULL
                        </span>
                      ) : typeof val === 'string' && val.startsWith('<BLOB:') ? (
                        <span className="text-amber-400 font-mono text-[10px] bg-amber-500/10 px-1.5 py-0.5 rounded">
                          {val}
                        </span>
                      ) : typeof val === 'boolean' ? (
                        <span className={val ? 'text-emerald-400' : 'text-slate-400'}>
                          {val ? 'TRUE' : 'FALSE'}
                        </span>
                      ) : (
                        <span>{String(val)}</span>
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
  )
}
