import { request } from './apiClient'
import type {
  HistoryFilterParams,
  HistorySettingsResponse,
  QueryHistoryListResponse,
  QueryHistoryRecord,
} from '../types/history'

export const historyService = {
  async listHistory(params: HistoryFilterParams = {}): Promise<QueryHistoryListResponse> {
    const searchParams = new URLSearchParams()
    if (params.page) searchParams.set('page', String(params.page))
    if (params.page_size) searchParams.set('page_size', String(params.page_size))
    if (params.search) searchParams.set('search', params.search)
    if (params.database_id) searchParams.set('database_id', params.database_id)
    if (params.status) searchParams.set('status', params.status)
    if (params.sort_desc !== undefined) searchParams.set('sort_desc', String(params.sort_desc))

    const queryStr = searchParams.toString()
    return request<QueryHistoryListResponse>(`/api/history${queryStr ? `?${queryStr}` : ''}`, {
      method: 'GET',
    })
  },

  async getHistoryItem(requestId: string): Promise<QueryHistoryRecord> {
    return request<QueryHistoryRecord>(`/api/history/${encodeURIComponent(requestId)}`, {
      method: 'GET',
    })
  },

  async deleteHistoryItem(requestId: string): Promise<{ status: string; request_id: string }> {
    return request<{ status: string; request_id: string }>(
      `/api/history/${encodeURIComponent(requestId)}`,
      {
        method: 'DELETE',
      }
    )
  },

  async clearHistory(): Promise<{ status: string; deleted_count: number }> {
    return request<{ status: string; deleted_count: number }>('/api/history', {
      method: 'DELETE',
    })
  },

  async getSettings(): Promise<HistorySettingsResponse> {
    return request<HistorySettingsResponse>('/api/history/settings', {
      method: 'GET',
    })
  },

  async updateSettings(isEnabled: boolean): Promise<HistorySettingsResponse> {
    return request<HistorySettingsResponse>('/api/history/settings', {
      method: 'PUT',
      body: JSON.stringify({ is_enabled: isEnabled }),
    })
  },
}
