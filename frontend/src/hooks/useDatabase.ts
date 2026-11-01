/**
 * TanStack Query hooks for database management and schema intelligence
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  activateDatabase,
  fetchActiveDatabase,
  fetchDatabaseRelationships,
  fetchDatabaseSchema,
  fetchDatabases,
  fetchSchemaContext,
  fetchTablePreview,
  unregisterDatabase,
  uploadDatabase,
} from '@/services/databaseService'

export const DATABASE_QUERY_KEYS = {
  all: ['databases'] as const,
  active: ['databases', 'active'] as const,
  schema: (id?: string) => ['databases', id, 'schema'] as const,
  relationships: (id?: string) => ['databases', id, 'relationships'] as const,
  preview: (id?: string, table?: string, limit?: number, offset?: number) =>
    ['databases', id, 'preview', table, limit, offset] as const,
  schemaContext: (id?: string) => ['databases', id, 'schema-context'] as const,
}

export function useDatabases() {
  return useQuery({
    queryKey: DATABASE_QUERY_KEYS.all,
    queryFn: fetchDatabases,
    staleTime: 30000,
    retry: 1,
  })
}

export function useActiveDatabase() {
  return useQuery({
    queryKey: DATABASE_QUERY_KEYS.active,
    queryFn: fetchActiveDatabase,
    staleTime: 30000,
    retry: 1,
  })
}

export function useDatabaseSchema(databaseId?: string) {
  return useQuery({
    queryKey: DATABASE_QUERY_KEYS.schema(databaseId),
    queryFn: () => {
      if (!databaseId) throw new Error('databaseId is required')
      return fetchDatabaseSchema(databaseId)
    },
    enabled: Boolean(databaseId),
    staleTime: 60000,
    retry: 1,
  })
}

export function useDatabaseRelationships(databaseId?: string) {
  return useQuery({
    queryKey: DATABASE_QUERY_KEYS.relationships(databaseId),
    queryFn: () => {
      if (!databaseId) throw new Error('databaseId is required')
      return fetchDatabaseRelationships(databaseId)
    },
    enabled: Boolean(databaseId),
    staleTime: 60000,
    retry: 1,
  })
}

export function useTablePreview(
  databaseId?: string,
  tableName?: string,
  limit: number = 20,
  offset: number = 0
) {
  return useQuery({
    queryKey: DATABASE_QUERY_KEYS.preview(databaseId, tableName, limit, offset),
    queryFn: () => {
      if (!databaseId || !tableName) throw new Error('databaseId and tableName required')
      return fetchTablePreview(databaseId, tableName, limit, offset)
    },
    enabled: Boolean(databaseId && tableName),
    staleTime: 30000,
    retry: 1,
  })
}

export function useSchemaContext(databaseId?: string) {
  return useQuery({
    queryKey: DATABASE_QUERY_KEYS.schemaContext(databaseId),
    queryFn: () => {
      if (!databaseId) throw new Error('databaseId is required')
      return fetchSchemaContext(databaseId)
    },
    enabled: Boolean(databaseId),
    staleTime: 60000,
    retry: 1,
  })
}

export function useActivateDatabase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (databaseId: string) => activateDatabase(databaseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DATABASE_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: DATABASE_QUERY_KEYS.active })
    },
  })
}

export function useUploadDatabase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, name }: { file: File; name?: string }) =>
      uploadDatabase(file, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DATABASE_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: DATABASE_QUERY_KEYS.active })
    },
  })
}

export function useUnregisterDatabase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ databaseId, deleteFile }: { databaseId: string; deleteFile?: boolean }) =>
      unregisterDatabase(databaseId, deleteFile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DATABASE_QUERY_KEYS.all })
      queryClient.invalidateQueries({ queryKey: DATABASE_QUERY_KEYS.active })
    },
  })
}
