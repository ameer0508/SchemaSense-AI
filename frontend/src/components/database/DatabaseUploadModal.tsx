import { useState, useRef, type DragEvent, type ChangeEvent } from 'react'
import { AlertCircle, CheckCircle2, FileUp, Loader2, UploadCloud } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { useUploadDatabase, useActivateDatabase } from '@/hooks/useDatabase'

interface DatabaseUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: (databaseId: string) => void
}

const ALLOWED_EXTENSIONS = ['.db', '.sqlite', '.sqlite3']
const MAX_SIZE_MB = 20

export function DatabaseUploadModal({ isOpen, onClose, onSuccess }: DatabaseUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [autoActivate, setAutoActivate] = useState(true)

  const fileInputRef = useRef<HTMLInputElement>(null)
  const uploadMutation = useUploadDatabase()
  const activateMutation = useActivateDatabase()

  const resetState = () => {
    setSelectedFile(null)
    setDisplayName('')
    setDragOver(false)
    setError(null)
    setSuccessMessage(null)
  }

  const handleClose = () => {
    resetState()
    onClose()
  }

  const validateAndSetFile = (file: File) => {
    setError(null)
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Invalid file type (${ext}). Please select a .db, .sqlite, or .sqlite3 file.`)
      return
    }

    if (file.size === 0) {
      setError('Selected file is empty (0 bytes).')
      return
    }

    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File size exceeds ${MAX_SIZE_MB} MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`)
      return
    }

    setSelectedFile(file)
    if (!displayName) {
      setDisplayName(file.name.replace(/\.[^/.]+$/, ''))
    }
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setError(null)

    try {
      const result = await uploadMutation.mutateAsync({
        file: selectedFile,
        name: displayName.trim() || undefined,
      })

      if (autoActivate) {
        await activateMutation.mutateAsync(result.database.id)
      }

      setSuccessMessage(`Database '${result.database.name}' uploaded successfully!`)
      setTimeout(() => {
        handleClose()
        if (onSuccess) {
          onSuccess(result.database.id)
        }
      }, 1200)
    } catch (err: any) {
      setError(err?.message || 'Upload failed. Please check the database file and try again.')
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Upload SQLite Database"
      description="Select or drop a local SQLite database (.db, .sqlite, .sqlite3) to introspect its schema."
    >
      <div className="space-y-4 pt-1">
        {/* Error Alert */}
        {error && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-[10px] border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300 light:bg-red-50 light:text-red-800 light:border-red-200"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
            <div className="flex-1 font-medium leading-relaxed">{error}</div>
          </div>
        )}

        {/* Success Alert */}
        {successMessage && (
          <div
            role="status"
            className="flex items-center gap-2 rounded-[10px] border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-300 light:bg-emerald-50 light:text-emerald-800 light:border-emerald-200"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            <span className="font-medium">{successMessage}</span>
          </div>
        )}

        {/* Drag and Drop Box */}
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative flex flex-col items-center justify-center rounded-[12px] border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
            dragOver
              ? 'border-indigo-500 bg-indigo-500/10 scale-[0.99]'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 hover:bg-slate-900/60 light:border-slate-300 light:bg-slate-50 light:hover:bg-slate-100'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".db,.sqlite,.sqlite3"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-400 mb-3 border border-indigo-500/20">
            {uploadMutation.isPending ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : (
              <UploadCloud className="h-6 w-6" />
            )}
          </div>

          <div className="text-xs font-medium text-slate-200 light:text-slate-800">
            {selectedFile ? (
              <span className="text-indigo-400 font-semibold">{selectedFile.name}</span>
            ) : (
              <span>Click to browse or drop SQLite file here</span>
            )}
          </div>

          <p className="mt-1 text-[11px] text-slate-500">
            {selectedFile
              ? `${(selectedFile.size / 1024).toFixed(1)} KB — Click to change file`
              : 'Supports .db, .sqlite, .sqlite3 files up to 20 MB'}
          </p>
        </div>

        {/* Display Name Input */}
        <div>
          <label
            htmlFor="db-display-name"
            className="block text-xs font-semibold text-slate-300 light:text-slate-700 mb-1"
          >
            Database Display Name (Optional)
          </label>
          <input
            id="db-display-name"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="e.g. Production Replica, Analytics Sandbox"
            className="w-full rounded-[8px] border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500/60 light:border-slate-300 light:bg-white light:text-slate-900"
          />
        </div>

        {/* Auto-activate Checkbox */}
        <div className="flex items-center gap-2 pt-1">
          <input
            id="auto-activate"
            type="checkbox"
            checked={autoActivate}
            onChange={(e) => setAutoActivate(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-slate-800 text-indigo-600 focus:ring-indigo-500/20 bg-slate-900"
          />
          <label htmlFor="auto-activate" className="text-xs text-slate-400 light:text-slate-600 select-none">
            Immediately set as active database upon registration
          </label>
        </div>

        {/* Actions Footer */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800 light:border-slate-200">
          <Button variant="ghost" size="sm" onClick={handleClose} disabled={uploadMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleUpload}
            disabled={!selectedFile || uploadMutation.isPending}
            className="gap-1.5"
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Validating & Uploading...</span>
              </>
            ) : (
              <>
                <FileUp className="h-3.5 w-3.5" />
                <span>Upload & Register</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
