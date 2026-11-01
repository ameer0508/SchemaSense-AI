export interface AnalyticsOverviewResponse {
  total_queries: number
  first_attempt_successes: number
  successes_after_correction: number
  total_failures: number
  total_correction_attempts: number
  first_attempt_success_rate?: number | null
  correction_success_rate?: number | null
  overall_success_rate?: number | null
  avg_generation_duration_ms?: number | null
  avg_execution_duration_ms?: number | null
  avg_total_duration_ms?: number | null
  most_used_database?: string | null
  most_common_error?: string | null
}

export interface TimeseriesPoint {
  date: string
  total: number
  first_attempt_successes: number
  corrected_successes: number
  failures: number
}

export interface AnalyticsTimeseriesResponse {
  points: TimeseriesPoint[]
  range_days: number
}

export interface ErrorCategoryStat {
  category: string
  count: number
  percentage: number
}

export interface AnalyticsErrorsResponse {
  categories: ErrorCategoryStat[]
  total_errors: number
}
