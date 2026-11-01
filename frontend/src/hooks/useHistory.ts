/**
 * TanStack Query hooks for Query History and Settings.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { historyService } from '@/services/historyService'
import type {
  HistoryFilterParams,
  HistorySettingsResponse,
  QueryHistoryListResponse,
} from '@/types/history'

export function useHistoryList(params: HistoryFilterParams = {}) {
  return useQuery<QueryHistoryListResponse, Error>({
    queryKey: ['history', 'list', params],
    queryFn: () => historyService.listHistory(params),
  })
}

export function useHistorySettings() {
  return useQuery<HistorySettingsResponse, Error>({
    queryKey: ['history', 'settings'],
    queryFn: () => historyService.getSettings(),
  })
}

export function useUpdateHistorySettings() {
  const queryClient = useQueryClient()
  return useMutation<HistorySettingsResponse, Error, boolean>({
    mutationFn: (isEnabled: boolean) => historyService.updateSettings(isEnabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history', 'settings'] })
    },
  })
}

export function useDeleteHistoryItem() {
  const queryClient = useQueryClient()
  return useMutation<{ status: string; request_id: string }, Error, string>({
    mutationFn: (requestId: string) => historyService.deleteHistoryItem(requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
}

export function useClearHistory() {
  const queryClient = useQueryClient()
  return useMutation<{ status: string; deleted_count: number }, Error, void>({
    mutationFn: () => historyService.clearHistory(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
    },
  })
}
