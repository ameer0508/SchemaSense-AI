import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RootLayout } from '@/layouts/RootLayout'
import { WorkspacePage } from '@/routes/WorkspacePage'
import { SchemaExplorerPage } from '@/routes/SchemaExplorerPage'
import { QueryHistoryPage } from '@/routes/QueryHistoryPage'
import { InsightsPage } from '@/routes/InsightsPage'
import { SettingsPage } from '@/routes/SettingsPage'
import { NotFoundPage } from '@/routes/NotFoundPage'

// Create TanStack Query client with resilient defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      refetchOnWindowFocus: true,
      retry: 1,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootLayout />}>
            <Route index element={<WorkspacePage />} />
            <Route path="workspace" element={<Navigate to="/" replace />} />
            <Route path="schemas" element={<SchemaExplorerPage />} />
            <Route path="history" element={<QueryHistoryPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
