import { request } from './apiClient'
import type { CapabilitiesResponse, HealthResponse } from '@/types/api'

export async function fetchHealth(): Promise<{ data: HealthResponse; latencyMs: number }> {
  const start = performance.now()
  const data = await request<HealthResponse>('/api/health')
  const latencyMs = Math.round(performance.now() - start)
  return { data, latencyMs }
}

export async function fetchCapabilities(): Promise<CapabilitiesResponse> {
  return request<CapabilitiesResponse>('/api/capabilities')
}
