export interface QueryHistoryRecord {
  request_id: string
  created_at: string
  database_id: string
  database_name: string
  question: string
  generation_mode: string
  model_id?: string | null
  initial_sql: string
  final_sql: string
  final_status: string
  validation_status: string
  execution_status: string
  row_count?: number | null
  correction_count: number
  generation_duration_ms: number
  execution_duration_ms: number
  total_duration_ms: number
  semantic_warning_count: number
  error_category?: string | null
  correction_trace_summary?: string | null
  semantic_warnings_summary?: string | null
}

export interface QueryHistoryListResponse {
  items: QueryHistoryRecord[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface HistorySettingsResponse {
  is_enabled: boolean
  total_saved_queries: number
  history_db_size_bytes: number
}

export interface HistoryFilterParams {
  page?: number
  page_size?: number
  search?: string
  database_id?: string
  status?: string
  sort_desc?: boolean
}
