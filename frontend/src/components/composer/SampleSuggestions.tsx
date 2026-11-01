import { Sparkles } from 'lucide-react'

export interface QuerySuggestion {
  id: string
  label: string
  query: string
  category: 'Students' | 'Courses' | 'Faculty' | 'Relational'
}

const SAMPLE_QUERIES: QuerySuggestion[] = [
  {
    id: 'top-students',
    label: 'Top 5 Students by GPA',
    query: 'Show the top 5 students with the highest GPA, including their full name and enrollment year.',
    category: 'Students',
  },
  {
    id: 'count-courses',
    label: 'Total Courses Count',
    query: 'How many courses are currently offered in the university?',
    category: 'Courses',
  },
  {
    id: 'students-departments',
    label: 'Students & Departments',
    query: 'List all students alongside their department name using a JOIN on department_id.',
    category: 'Relational',
  },
  {
    id: 'faculty-courses',
    label: 'Faculty & Taught Courses',
    query: 'Show each faculty member and the title and code of the courses they teach.',
    category: 'Faculty',
  },
]

interface SampleSuggestionsProps {
  onSelectQuery: (query: string) => void
}

export function SampleSuggestions({ onSelectQuery }: SampleSuggestionsProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400 light:text-slate-500">
        <Sparkles className="h-3 w-3 text-cyan-400" />
        <span>Grounded prompt suggestions for Campus Intelligence:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {SAMPLE_QUERIES.map((sample) => (
          <button
            key={sample.id}
            type="button"
            onClick={() => onSelectQuery(sample.query)}
            className="group flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-300 transition-all duration-150 hover:border-cyan-500/50 hover:bg-slate-800 hover:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/40 light:border-slate-200 light:bg-slate-50 light:text-slate-700 light:hover:bg-slate-100 light:hover:text-slate-900"
            title={sample.query}
          >
            <span className="rounded-[4px] bg-slate-800 px-1.5 py-0.5 text-[9px] font-semibold text-cyan-400 border border-slate-700/60 light:bg-slate-200 light:text-cyan-700 light:border-slate-300">
              {sample.category}
            </span>
            <span className="truncate max-w-[220px] sm:max-w-xs">{sample.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
