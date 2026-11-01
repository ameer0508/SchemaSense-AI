import { request } from './apiClient'
import type {
  AnalyticsErrorsResponse,
  AnalyticsOverviewResponse,
  AnalyticsTimeseriesResponse,
} from '../types/analytics'

export const analyticsService = {
  async getOverview(days?: number): Promise<AnalyticsOverviewResponse> {
    const query = days ? `?days=${days}` : ''
    return request<AnalyticsOverviewResponse>(`/api/analytics/overview${query}`, {
      method: 'GET',
    })
  },

  async getTimeseries(days = 14): Promise<AnalyticsTimeseriesResponse> {
    return request<AnalyticsTimeseriesResponse>(`/api/analytics/timeseries?days=${days}`, {
      method: 'GET',
    })
  },

  async getErrors(days?: number): Promise<AnalyticsErrorsResponse> {
    const query = days ? `?days=${days}` : ''
    return request<AnalyticsErrorsResponse>(`/api/analytics/errors${query}`, {
      method: 'GET',
    })
  },
}
