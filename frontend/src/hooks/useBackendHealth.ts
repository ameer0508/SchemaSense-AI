import { useQuery } from '@tanstack/react-query'
import { fetchCapabilities, fetchHealth } from '@/services/healthService'
import type {
  BackendHealthState,
  CapabilitiesResponse,
  ConnectionState,
  HealthResponse,
} from '@/types/api'

export function useBackendHealth(): BackendHealthState {
  const healthQuery = useQuery({
    queryKey: ['backend-health'],
    queryFn: fetchHealth,
    refetchInterval: 15000, // Background poll every 15 seconds to minimize noise
    refetchOnWindowFocus: false, // Prevent jittery refetches on window focus
    retry: 1,
    retryDelay: 1500,
  })

  const capabilitiesQuery = useQuery({
    queryKey: ['backend-capabilities'],
    queryFn: fetchCapabilities,
    enabled: healthQuery.isSuccess && healthQuery.data?.data?.status === 'healthy',
    refetchInterval: 60000,
    refetchOnWindowFocus: false,
    retry: 1,
  })

  let state: ConnectionState = 'checking'
  if (healthQuery.isLoading && !healthQuery.data) {
    state = 'checking'
  } else if (healthQuery.isSuccess && healthQuery.data?.data?.status === 'healthy') {
    state = 'connected'
  } else if (healthQuery.isError) {
    state = 'disconnected'
  }

  const health: HealthResponse | null = healthQuery.data?.data ?? null
  const capabilities: CapabilitiesResponse | null = capabilitiesQuery.data ?? null
  const latencyMs: number | null = healthQuery.data?.latencyMs ?? null
  const error: string | null =
    healthQuery.error instanceof Error ? healthQuery.error.message : null

  const handleRefetch = () => {
    void healthQuery.refetch()
    void capabilitiesQuery.refetch()
  }

  return {
    state,
    health,
    capabilities,
    latencyMs,
    lastChecked: healthQuery.dataUpdatedAt ? new Date(healthQuery.dataUpdatedAt) : null,
    error,
    refetch: handleRefetch,
  }
}
