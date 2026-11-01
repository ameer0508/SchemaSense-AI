/**
 * TanStack Query hooks for SQL execution and end-to-end AI query workflow.
 */

import { useMutation } from '@tanstack/react-query'
import { executionService } from '@/services/executionService'
import type {
  AIQueryRequest,
  AIQueryResponse,
  ExecuteSQLRequest,
  ExecuteSQLResponse,
} from '@/types/execution'

export function useExecuteSql() {
  return useMutation<ExecuteSQLResponse, Error, ExecuteSQLRequest>({
    mutationFn: (payload: ExecuteSQLRequest) => executionService.executeSql(payload),
  })
}

export function useAiQuery() {
  return useMutation<AIQueryResponse, Error, AIQueryRequest>({
    mutationFn: (payload: AIQueryRequest) => executionService.queryAi(payload),
  })
}
