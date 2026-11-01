/**
 * SchemaSense AI SQL Execution & Self-Correction API Service
 */

import { request } from './apiClient'
import type {
  AIQueryRequest,
  AIQueryResponse,
  ExecuteSQLRequest,
  ExecuteSQLResponse,
} from '@/types/execution'

export const executionService = {
  /**
   * Execute standalone read-only SQL query against a registered database.
   */
  async executeSql(payload: ExecuteSQLRequest): Promise<ExecuteSQLResponse> {
    return request<ExecuteSQLResponse>(
      '/api/sql/execute',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      30000 // 30 second timeout for query execution
    )
  },

  /**
   * Run end-to-end natural-language to database results query workflow with intelligent self-correction.
   * Uses 240s timeout to allow local transformer inference and multi-step repair attempts on CPU.
   */
  async queryAi(payload: AIQueryRequest): Promise<AIQueryResponse> {
    return request<AIQueryResponse>(
      '/api/ai/query',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      240000 // 4 minute timeout for local CPU model inference and self-correction
    )
  },
}
