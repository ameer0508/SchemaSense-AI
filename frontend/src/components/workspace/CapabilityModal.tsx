import { Check, Clock, Cpu, Database } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { useBackendHealth } from '@/hooks/useBackendHealth'

interface CapabilityModalProps {
  isOpen: boolean
  onClose: () => void
}

export function CapabilityModal({ isOpen, onClose }: CapabilityModalProps) {
  const { capabilities, state, health } = useBackendHealth()

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="System Capability Matrix"
      description="Live report from GET /api/capabilities showing active vs upcoming engine features."
      maxWidth="lg"
    >
      <div className="space-y-5">
        {/* Header Summary */}
        <div className="rounded-[12px] border border-indigo-500/20 bg-indigo-500/5 p-4 light:bg-indigo-50/50 light:border-indigo-200">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <span className="text-xs font-semibold text-indigo-400 light:text-indigo-700">
                {capabilities?.phase || 'Phase 1 - Foundation & Architecture'}
              </span>
              <p className="mt-1 text-xs text-slate-300 light:text-slate-700">
                {capabilities?.phase_description ||
                  'Foundational client-server architecture, typed schemas, and capability discovery.'}
              </p>
            </div>
            <Badge variant="indigo" size="sm">
              v{capabilities?.version || health?.version || '0.1.0'}
            </Badge>
          </div>
        </div>

        {/* Feature Matrix Table */}
        <div>
          <h4 className="text-xs font-semibold text-slate-300 light:text-slate-800 uppercase tracking-wider mb-2.5">
            Core Engine Capabilities
          </h4>
          <div className="rounded-[10px] border border-slate-800 divide-y divide-slate-800/80 overflow-hidden light:border-slate-200 light:divide-slate-200">
            {[
              {
                name: 'System Health Check',
                description: 'Real-time operational status, ping latency, and environment reporting.',
                active: capabilities?.capabilities?.health_check ?? (state === 'connected'),
                phase: 'Phase 1',
              },
              {
                name: 'Capability Discovery API',
                description: 'Programmatic discovery of system capability matrix and provider registry.',
                active: capabilities?.capabilities?.capabilities_discovery ?? (state === 'connected'),
                phase: 'Phase 1',
              },
              {
                name: 'Natural Language to SQL Engine',
                description: 'LLM reasoning engine translating natural language questions into dialect-aware SQL.',
                active: capabilities?.capabilities?.natural_language_sql ?? false,
                phase: 'Phase 2',
              },
              {
                name: 'Schema Introspection Service',
                description: 'Automatic discovery of database tables, column types, and foreign key relations.',
                active: capabilities?.capabilities?.schema_introspection ?? false,
                phase: 'Phase 2',
              },
              {
                name: 'Safe SQL Execution Sandbox',
                description: 'Isolated, read-only SQL execution with strict timeouts and AST validation.',
                active: capabilities?.capabilities?.sql_execution ?? false,
                phase: 'Phase 2',
              },
              {
                name: 'Query History & Versioning',
                description: 'Persistent audit trail and execution history tracking.',
                active: capabilities?.capabilities?.query_history_archiving ?? false,
                phase: 'Phase 2',
              },
              {
                name: 'Agentic Self-Correction Loop',
                description: 'Autonomous multi-step loop diagnosing execution errors and fixing SQL syntax.',
                active: capabilities?.capabilities?.sql_self_correction ?? false,
                phase: 'Phase 3',
              },
            ].map((feat) => (
              <div
                key={feat.name}
                className="flex items-center justify-between p-3 bg-slate-900/30 hover:bg-slate-900/60 transition-colors light:bg-white light:hover:bg-slate-50"
              >
                <div className="pr-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-slate-200 light:text-slate-900">
                      {feat.name}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono-code">{feat.phase}</span>
                  </div>
                  <p className="mt-0.5 text-[11px] text-slate-400 light:text-slate-500">
                    {feat.description}
                  </p>
                </div>
                <div className="shrink-0">
                  {feat.active ? (
                    <Badge variant="success" size="xs" dot>
                      <Check className="h-3 w-3 mr-0.5" /> Active
                    </Badge>
                  ) : (
                    <Badge variant="outline" size="xs">
                      <Clock className="h-3 w-3 mr-0.5" /> Inactive
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Architecture Targets */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <div className="rounded-[10px] border border-slate-800 bg-slate-900/40 p-3 light:border-slate-200 light:bg-slate-50">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300 light:text-slate-800">
              <Database className="h-3.5 w-3.5 text-cyan-400" />
              Supported SQL Dialects
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(capabilities?.supported_dialects || [
                'postgresql',
                'sqlite',
                'mysql',
                'snowflake',
              ]).map((dialect) => (
                <span
                  key={dialect}
                  className="rounded px-2 py-0.5 text-[10px] font-mono-code bg-slate-800/80 text-cyan-300 border border-slate-700/60 light:bg-white light:text-cyan-700 light:border-slate-200"
                >
                  {dialect}
                </span>
              ))}
            </div>
          </div>

          <div className="rounded-[10px] border border-slate-800 bg-slate-900/40 p-3 light:border-slate-200 light:bg-slate-50">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300 light:text-slate-800">
              <Cpu className="h-3.5 w-3.5 text-indigo-400" />
              Prepared AI Engine Providers
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(capabilities?.supported_ai_providers || [
                'gemini',
                'openai',
                'anthropic',
                'local',
              ]).map((provider) => (
                <span
                  key={provider}
                  className="rounded px-2 py-0.5 text-[10px] font-mono-code bg-slate-800/80 text-indigo-300 border border-slate-700/60 light:bg-white light:text-indigo-700 light:border-slate-200"
                >
                  {provider}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  )
}
