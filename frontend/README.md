# SchemaSense AI — Frontend Studio

**Subtitle**: Natural Language. Precise SQL.  
**Phase**: Phase 8 — Final Engineering Audit, Academic Evidence & Demonstration Readiness  
**Target Environment**: React 19 / TypeScript 5.8 / Vite / Tailwind CSS / TanStack Query  

---

## 1. Architecture Overview

```text
frontend/
├── public/
│   └── favicon.svg           # Custom vector emblem
├── src/
│   ├── components/
│   │   ├── common/           # BrandLogo, ThemeToggle, ConnectionBadge
│   │   ├── composer/         # QuestionComposer, SampleSuggestions
│   │   ├── database/         # DatabaseSelector, DatabaseUploadModal, TableDataPreview
│   │   ├── ui/               # Button, Badge, Card, Modal
│   │   └── workspace/        # ResultsTable, GeneratedSqlViewer, CorrectionTimeline, CapabilityModal
│   ├── hooks/
│   │   ├── useBackendHealth.ts  # TanStack Query hook with ping latency & retry
│   │   ├── useDatabases.ts      # Active database catalog & introspection hook
│   │   ├── useExecution.ts      # Query execution & self-correction mutation
│   │   └── useTheme.ts          # Dark/light theme toggle with FOUC prevention
│   ├── layouts/
│   │   ├── MobileNav.tsx     # Responsive mobile drawer
│   │   ├── RootLayout.tsx    # App shell & layout wrapper
│   │   ├── Sidebar.tsx       # Collapsible desktop sidebar
│   │   └── TopNav.tsx        # Top navigation bar & breadcrumbs
│   ├── routes/
│   │   ├── InsightsPage.tsx        # Telemetry & execution analytics
│   │   ├── NotFoundPage.tsx        # 404 handler
│   │   ├── QueryHistoryPage.tsx    # Query audit log with search & reuse
│   │   ├── SchemaExplorerPage.tsx  # Dynamic database schema catalog & data preview
│   │   ├── SettingsPage.tsx        # Configuration & model status
│   │   └── WorkspacePage.tsx       # Natural language to SQL studio
│   ├── services/
│   │   ├── apiClient.ts      # Typed fetch wrapper with configurable base URL
│   │   └── healthService.ts  # Calls /api/health and /api/capabilities
│   ├── types/
│   │   └── api.ts            # Typed interfaces for health, capabilities, connection states
│   ├── App.tsx
│   ├── index.css             # Design tokens and custom theme styling
│   └── main.tsx
├── .env.example
├── .env
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## 2. Getting Started

### 2.1 Prerequisites
- Node.js 18+ or 20+ LTS
- npm or pnpm

### 2.2 Install Dependencies
```bash
npm install
```

### 2.3 Configuration
Copy `.env.example` to `.env` if local overrides are needed:
```bash
cp .env.example .env
```
Default `VITE_API_BASE_URL` is `http://localhost:8001`.

### 2.4 Running the Development Server
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### 2.5 Building for Production
```bash
npm run build
```
Type checks via `tsc -b` and builds production bundle to `dist/`.
