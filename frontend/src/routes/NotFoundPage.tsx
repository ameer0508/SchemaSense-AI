import { ArrowLeft, FileQuestion } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-4">
        <FileQuestion className="h-10 w-10" />
      </div>
      <h1 className="text-2xl font-bold text-slate-100 light:text-slate-900 mb-2">
        Page Not Found
      </h1>
      <p className="text-sm text-slate-400 light:text-slate-600 max-w-sm mb-6">
        The route you requested does not exist in SchemaSense AI.
      </p>
      <Link to="/">
        <Button variant="primary" size="md" leftIcon={<ArrowLeft className="h-4 w-4" />}>
          Back to Workspace
        </Button>
      </Link>
    </div>
  )
}
