/**
 * TanStack Query hooks for AI status, initialization, and SQL generation
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { aiService } from '@/services/aiService'
import type { GenerateSQLRequest, GenerateSQLResponse, ModelStatusResponse } from '@/types/ai'

export const AI_QUERY_KEYS = {
  status: ['ai', 'status'] as const,
  generation: ['ai', 'generation'] as const,
}

/**
 * Hook to retrieve accurate AI model loading status and hardware device.
 * Dynamically polls more frequently if the model is currently loading/downloading.
 */
export function useModelStatus() {
  return useQuery<ModelStatusResponse>({
    queryKey: AI_QUERY_KEYS.status,
    queryFn: () => aiService.getModelStatus(),
    refetchInterval: (query) => {
      const data = query.state.data
      if (data?.status === 'loading') {
        return 2500 // Poll every 2.5s while downloading/loading weights
      }
      return 20000 // Poll every 20s when idle/ready
    },
    staleTime: 5000,
  })
}

/**
 * Hook to trigger background model loading.
 */
export function useInitializeModel() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => aiService.initializeModel(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: AI_QUERY_KEYS.status })
    },
  })
}

/**
 * Hook to generate schema-grounded SQL from natural language questions.
 */
export function useGenerateSql() {
  return useMutation<GenerateSQLResponse, Error, GenerateSQLRequest>({
    mutationFn: (payload: GenerateSQLRequest) => aiService.generateSql(payload),
  })
}
