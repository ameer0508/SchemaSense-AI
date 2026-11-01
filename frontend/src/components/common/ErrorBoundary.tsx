import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('SchemaSense AI Uncaught UI Error:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center" role="alert">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 shadow-inner">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <h2 className="text-lg font-bold text-slate-100 light:text-slate-900 mb-2">
            {this.props.fallbackTitle || 'Component Encountered an Unexpected Error'}
          </h2>
          <p className="max-w-md text-xs text-slate-400 light:text-slate-600 mb-6 leading-relaxed">
            {this.state.error?.message ||
              'A rendering issue occurred. Your workspace state is preserved.'}
          </p>
          <div className="flex items-center gap-3">
            <Button
              variant="primary"
              size="sm"
              onClick={this.handleReset}
              leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
            >
              Try Again
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={this.handleReload}
            >
              Reload Studio
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
