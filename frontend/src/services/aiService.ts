/**
 * SchemaSense AI Generative AI Service
 */

import { request } from './apiClient'
import type {
  GenerateSQLRequest,
  GenerateSQLResponse,
  InitializeModelResponse,
  ModelStatusResponse,
} from '@/types/ai'

export const aiService = {
  /**
   * Fetch current model loading and hardware status.
   */
  async getModelStatus(): Promise<ModelStatusResponse> {
    return request<ModelStatusResponse>('/api/ai/status', { method: 'GET' }, 8000)
  },

  /**
   * Trigger asynchronous model initialization / preload.
   */
  async initializeModel(): Promise<InitializeModelResponse> {
    return request<InitializeModelResponse>('/api/ai/initialize', { method: 'POST' }, 10000)
  },

  /**
   * Generate schema-grounded SQL from a natural language question.
   * Generous timeout (180s) to comfortably accommodate CPU-bound transformer inference.
   */
  async generateSql(payload: GenerateSQLRequest): Promise<GenerateSQLResponse> {
    return request<GenerateSQLResponse>(
      '/api/ai/generate-sql',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      180000
    )
  },
}
