/**
 * Database Management and Schema Intelligence Service Client
 */

import { request } from '@/services/apiClient'
import type {
  DatabaseInfo,
  DatabaseSchemaResponse,
  DatabaseUploadResponse,
  RelationshipMetadata,
  SchemaContextResponse,
  TablePreviewResponse,
} from '@/types/database'

export async function fetchDatabases(): Promise<DatabaseInfo[]> {
  return request<DatabaseInfo[]>('/api/databases')
}

export async function fetchActiveDatabase(): Promise<DatabaseInfo> {
  return request<DatabaseInfo>('/api/databases/active')
}

export async function activateDatabase(databaseId: string): Promise<DatabaseInfo> {
  return request<DatabaseInfo>(`/api/databases/${encodeURIComponent(databaseId)}/activate`, {
    method: 'POST',
  })
}

export async function uploadDatabase(file: File, name?: string): Promise<DatabaseUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  if (name && name.trim()) {
    formData.append('name', name.trim())
  }

  return request<DatabaseUploadResponse>('/api/databases/upload', {
    method: 'POST',
    body: formData,
  }, 30000) // 30s timeout for uploads
}

export async function unregisterDatabase(
  databaseId: string,
  deleteFile: boolean = false
): Promise<{ status: string; message: string }> {
  const query = deleteFile ? '?delete_file=true' : ''
  return request<{ status: string; message: string }>(
    `/api/databases/${encodeURIComponent(databaseId)}${query}`,
    {
      method: 'DELETE',
    }
  )
}

export async function fetchDatabaseSchema(databaseId: string): Promise<DatabaseSchemaResponse> {
  return request<DatabaseSchemaResponse>(
    `/api/databases/${encodeURIComponent(databaseId)}/schema`
  )
}

export async function fetchDatabaseRelationships(
  databaseId: string
): Promise<RelationshipMetadata[]> {
  return request<RelationshipMetadata[]>(
    `/api/databases/${encodeURIComponent(databaseId)}/relationships`
  )
}

export async function fetchTablePreview(
  databaseId: string,
  tableName: string,
  limit: number = 20,
  offset: number = 0
): Promise<TablePreviewResponse> {
  return request<TablePreviewResponse>(
    `/api/databases/${encodeURIComponent(databaseId)}/tables/${encodeURIComponent(tableName)}/preview?limit=${limit}&offset=${offset}`
  )
}

export async function fetchSchemaContext(databaseId: string): Promise<SchemaContextResponse> {
  return request<SchemaContextResponse>(
    `/api/databases/${encodeURIComponent(databaseId)}/schema-context`
  )
}
