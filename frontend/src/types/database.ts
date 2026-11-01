/**
 * SchemaSense AI Database & Schema Intelligence Types
 */

export interface ColumnMetadata {
  name: string
  data_type: string
  nullable: boolean
  primary_key: boolean
  pk_position: number | null
  default_value: string | null
  is_foreign_key: boolean
  fk_target_table: string | null
  fk_target_column: string | null
}

export interface ForeignKeyMetadata {
  constraint_id: number | null
  from_column: string
  to_table: string
  to_column: string
  on_update: string | null
  on_delete: string | null
}

export interface IndexMetadata {
  name: string
  columns: string[]
  unique: boolean
}

export interface TableMetadata {
  name: string
  type: 'table' | 'view' | string
  column_count: number
  row_count: number
  columns: ColumnMetadata[]
  primary_keys: string[]
  foreign_keys: ForeignKeyMetadata[]
  indices: IndexMetadata[]
}

export interface RelationshipMetadata {
  id: string
  source_table: string
  source_column: string
  target_table: string
  target_column: string
  is_composite: boolean
  composite_pairs: Array<{ from: string; to: string }> | null
}

export interface DatabaseInfo {
  id: string
  name: string
  filename: string
  file_size_bytes: number
  created_at: string
  is_active: boolean
  is_protected: boolean
  table_count: number
  view_count: number
  description: string | null
}

export interface DatabaseSchemaResponse {
  database: DatabaseInfo
  dialect: string
  tables: TableMetadata[]
  relationships: RelationshipMetadata[]
  total_tables: number
  total_columns: number
  total_relationships: number
}

export interface TablePreviewResponse {
  database_id: string
  table_name: string
  columns: string[]
  column_types: Record<string, string>
  rows: Array<Record<string, any>>
  total_rows: number
  limit: number
  offset: number
  is_truncated: boolean
}

export interface SchemaContextResponse {
  database_id: string
  database_name: string
  dialect: string
  prompt_schema_context: string
  token_estimate: number
}

export interface DatabaseUploadResponse {
  database: DatabaseInfo
  message: string
}
