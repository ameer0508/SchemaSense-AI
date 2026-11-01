import { useState, useRef, useEffect } from 'react'
import {
  ChevronDown,
  Database,
  Check,
  Plus,
  Trash2,
} from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useDatabases, useActivateDatabase, useUnregisterDatabase } from '@/hooks/useDatabase'
import type { DatabaseInfo } from '@/types/database'

interface DatabaseSelectorProps {
  activeDatabase?: DatabaseInfo | null
  onOpenUpload: () => void
}

export function DatabaseSelector({ activeDatabase, onOpenUpload }: DatabaseSelectorProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const { data: databases, isLoading } = useDatabases()
  const activateMutation = useActivateDatabase()
  const unregisterMutation = useUnregisterDatabase()

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = async (dbId: string) => {
    if (activeDatabase?.id === dbId) {
      setDropdownOpen(false)
      return
    }
    try {
      await activateMutation.mutateAsync(dbId)
      setDropdownOpen(false)
    } catch (err) {
      console.error('Failed to activate database:', err)
    }
  }

  const handleDelete = async (e: React.MouseEvent, db: DatabaseInfo) => {
    e.stopPropagation()
    if (db.is_protected) return
    const confirmed = window.confirm(
      `Are you sure you want to unregister '${db.name}'? This will disconnect the database from SchemaSense AI.`
    )
    if (!confirmed) return

    try {
      await unregisterMutation.mutateAsync({ databaseId: db.id, deleteFile: true })
    } catch (err) {
      console.error('Failed to unregister database:', err)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setDropdownOpen(!dropdownOpen)}
        className="flex items-center gap-2.5 rounded-[10px] border border-slate-800 bg-slate-900/80 px-3.5 py-2 text-xs font-medium text-slate-200 transition-all hover:bg-slate-800/80 hover:border-slate-700 light:border-slate-200 light:bg-white light:text-slate-800 light:hover:bg-slate-50 shadow-sm"
        aria-haspopup="true"
        aria-expanded={dropdownOpen}
      >
        <div className="flex h-5 w-5 items-center justify-center rounded-md bg-indigo-500/15 text-indigo-400 border border-indigo-500/25">
          <Database className="h-3 w-3" />
        </div>

        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-100 light:text-slate-900 truncate max-w-[160px]">
              {activeDatabase ? activeDatabase.name : 'No Active Database'}
            </span>
            <Badge variant="indigo" size="xs">
              SQLite
            </Badge>
          </div>
          {activeDatabase && (
            <span className="text-[10px] text-slate-500 font-mono-code">
              {activeDatabase.table_count} tables • {formatBytes(activeDatabase.file_size_bytes)}
            </span>
          )}
        </div>

        <ChevronDown
          className={`h-3.5 w-3.5 text-slate-500 transition-transform ml-1 ${
            dropdownOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {dropdownOpen && (
        <div
          role="menu"
          className="absolute right-0 sm:left-0 z-50 mt-1.5 w-80 rounded-[12px] border border-slate-800 bg-slate-950 p-2 shadow-2xl backdrop-blur-xl light:border-slate-200 light:bg-white"
        >
          <div className="px-2.5 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800/80 light:border-slate-100 flex items-center justify-between">
            <span>Registered Databases</span>
            <span className="text-[10px] text-slate-500 font-mono-code">
              {databases?.length || 0} Total
            </span>
          </div>

          <div className="max-h-60 overflow-y-auto py-1 divide-y divide-slate-900 light:divide-slate-50">
            {isLoading ? (
              <div className="p-4 text-center text-xs text-slate-500">Loading databases...</div>
            ) : databases && databases.length > 0 ? (
              databases.map((db) => {
                const isSelected = activeDatabase?.id === db.id
                return (
                  <div
                    key={db.id}
                    onClick={() => handleSelect(db.id)}
                    className={`group flex items-center justify-between rounded-[8px] p-2.5 text-xs cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-indigo-600/15 text-indigo-300 light:bg-indigo-50 light:text-indigo-900'
                        : 'hover:bg-slate-900 text-slate-300 light:text-slate-700 light:hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-start gap-2 min-w-0">
                      <div className="mt-0.5">
                        {isSelected ? (
                          <Check className="h-3.5 w-3.5 text-indigo-400" />
                        ) : (
                          <Database className="h-3.5 w-3.5 text-slate-500" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-medium truncate">{db.name}</span>
                          {db.is_protected && (
                            <span
                              title="Protected Demonstration Database"
                              className="inline-flex items-center text-[10px] text-amber-400 bg-amber-500/10 px-1.5 rounded"
                            >
                              Demo
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono-code mt-0.5">
                          <span>{db.table_count} tables</span>
                          <span>•</span>
                          <span>{formatBytes(db.file_size_bytes)}</span>
                        </div>
                      </div>
                    </div>

                    {!db.is_protected && (
                      <button
                        type="button"
                        onClick={(e) => handleDelete(e, db)}
                        title="Unregister database"
                        className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                )
              })
            ) : (
              <div className="p-4 text-center text-xs text-slate-500">No databases registered</div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-800/80 light:border-slate-100">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setDropdownOpen(false)
                onOpenUpload()
              }}
              className="w-full gap-1.5 justify-center text-xs"
            >
              <Plus className="h-3.5 w-3.5 text-indigo-400" />
              <span>Upload New SQLite Database</span>
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
