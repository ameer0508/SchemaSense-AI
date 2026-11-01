/**
 * SchemaSense AI Typed API Definitions
 */

export interface HealthResponse {
  status: 'healthy' | 'unhealthy' | string
  version: string
  environment: string
  timestamp: string
  service: string
  uptime_seconds: number
}

export interface CapabilityFlags {
  health_check: boolean
  capabilities_discovery: boolean
  schema_introspection: boolean
  database_registration?: boolean
  sqlite_upload?: boolean
  relationship_discovery?: boolean
  table_preview?: boolean
  schema_context_generation?: boolean
  natural_language_sql: boolean
  sql_execution: boolean
  sql_self_correction: boolean
  query_history_archiving: boolean
}

export interface CapabilitiesResponse {
  product: string
  tagline: string
  version: string
  phase: string
  phase_description: string
  capabilities: CapabilityFlags
  supported_dialects: string[]
  supported_ai_providers: string[]
  active_ai_provider: string | null
}

export type ConnectionState = 'connected' | 'disconnected' | 'checking'

export interface BackendHealthState {
  state: ConnectionState
  health: HealthResponse | null
  capabilities: CapabilitiesResponse | null
  latencyMs: number | null
  lastChecked: Date | null
  error: string | null
  refetch: () => void
}
