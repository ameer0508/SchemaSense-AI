import type { ModelMetadata, SQLValidationResult } from './ai'

export type QueryExecutionStatus =
  | 'success_first_attempt'
  | 'success_after_correction'
  | 'failed_validation'
  | 'failed_execution'
  | 'correction_exhausted'
  | 'unsafe_rejected'
  | 'model_unavailable'
  | 'timeout'

export interface ExecuteSQLRequest {
  database_id: string
  sql: string
  max_rows?: number
  timeout_seconds?: number
}

export interface SemanticWarningItem {
  code: string
  severity: 'info' | 'advisory' | 'warning' | 'error'
  message: string
  evidence: Record<string, any>
}

export interface SemanticAnalysisResult {
  is_semantically_sound: boolean
  warnings: string[]
  structured_warnings?: SemanticWarningItem[]
  detected_patterns: string[]
  recommendation?: string | null
}

export interface ExecuteSQLResponse {
  request_id: string
  database_id: string
  sql: string
  status: 'success' | 'error' | 'timeout' | 'rejected'
  columns: string[]
  rows: (string | number | boolean | null)[][]
  row_count: number
  total_rows_estimated?: number | null
  is_truncated: boolean
  duration_ms: number
  error_message?: string | null
  error_code?: string | null
  validation?: SQLValidationResult | null
  semantic_analysis?: SemanticAnalysisResult | null
}

export interface CorrectionAttempt {
  attempt_number: number
  attempt_type: 'initial' | 'correction'
  sql: string
  validation_status: string
  execution_status: string
  error_category?: string | null
  error_message?: string | null
  explanation?: string | null
  changes_made: string[]
  generation_time_ms: number
  execution_time_ms: number
  is_accepted: boolean
}

export interface AIQueryRequest {
  question: string
  database_id?: string
  auto_correct?: boolean
  max_corrections?: number
  temperature?: number
}

export interface AIQueryResponse {
  request_id: string
  question: string
  database_id: string
  database_name: string
  model: ModelMetadata
  final_status: QueryExecutionStatus
  initial_sql: string
  final_sql: string
  validation: SQLValidationResult
  execution?: ExecuteSQLResponse | null
  semantic_analysis?: SemanticAnalysisResult | null
  correction_trace: CorrectionAttempt[]
  total_correction_attempts: number
  total_duration_ms: number
  summary: string
}
