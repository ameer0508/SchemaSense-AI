/**
 * TanStack Query hooks for Analytics and Telemetry.
 */

import { useQuery } from '@tanstack/react-query'
import { analyticsService } from '@/services/analyticsService'
import type {
  AnalyticsErrorsResponse,
  AnalyticsOverviewResponse,
  AnalyticsTimeseriesResponse,
} from '@/types/analytics'

export function useAnalyticsOverview(days?: number) {
  return useQuery<AnalyticsOverviewResponse, Error>({
    queryKey: ['analytics', 'overview', days],
    queryFn: () => analyticsService.getOverview(days),
  })
}

export function useAnalyticsTimeseries(days = 14) {
  return useQuery<AnalyticsTimeseriesResponse, Error>({
    queryKey: ['analytics', 'timeseries', days],
    queryFn: () => analyticsService.getTimeseries(days),
  })
}

export function useAnalyticsErrors(days?: number) {
  return useQuery<AnalyticsErrorsResponse, Error>({
    queryKey: ['analytics', 'errors', days],
    queryFn: () => analyticsService.getErrors(days),
  })
}
