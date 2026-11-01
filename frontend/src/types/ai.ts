/**
 * SchemaSense AI Generative AI & SQL Validation Types
 */

export type ValidationStatus =
  | 'valid'
  | 'invalid'
  | 'unsafe'
  | 'schema_mismatch'
  | 'unsupported'
  | 'unverified'

export type ModelLoadStatus =
  | 'not_loaded'
  | 'loading'
  | 'ready'
  | 'unavailable'
  | 'error'

export interface ModelMetadata {
  provider: string
  model_id: string
  device?: string
}

export interface SQLValidationResult {
  status: ValidationStatus
  is_valid: boolean
  syntax_valid: boolean
  schema_valid: boolean
  ast_type?: string | null
  tables_referenced: string[]
  columns_referenced: string[]
  issues: string[]
  warnings: string[]
}

export interface ExecutionStatus {
  status: string
  message: string
}

export interface GenerateSQLRequest {
  question: string
  database_id?: string | null
  temperature?: number
}

export interface GenerateSQLResponse {
  request_id: string
  database_id: string
  database_name: string
  model: ModelMetadata
  question: string
  sql: string
  explanation?: string | null
  assumptions: string[]
  validation: SQLValidationResult
  execution: ExecutionStatus
  generation_time_ms: number
  prompt_tokens_estimated?: number | null
}

export interface ModelStatusResponse {
  provider: string
  model_id: string
  status: ModelLoadStatus
  device: string
  is_available: boolean
  is_loading: boolean
  total_params?: string | null
  max_new_tokens: number
  temperature: number
  error_message?: string | null
}

export interface InitializeModelResponse {
  status: ModelLoadStatus
  model_id: string
  message: string
}
