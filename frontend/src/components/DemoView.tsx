import { useState } from 'react'
import { Play, Loader2 } from 'lucide-react'
import { EvaluateResponse } from '../types'
import { runDemo } from '../api'
import ResultTabs from './ResultTabs'

const PROFILE = {
  name: 'Aurora AI Labs',
  type: 'Research Institute',
  domain: 'AI Safety & Energy Efficiency',
  size: '22 FTE',
  budget: '$3.5M',
}

const GRANTS = [
  { id: 'DOE-2024-AI', funder: 'Dept. of Energy', title: 'AI for Energy Efficiency', amount: '$750K', tag: 'STEM' },
  { id: 'NSF-2024-CS',  funder: 'NSF',            title: 'Responsible AI Research',  amount: '$500K', tag: 'Research' },
]

export default function DemoView() {
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState<EvaluateResponse | null>(null)
  const [error,   setError]   = useState<string | null>(null)

  const go = async () => {
    setLoading(true); setError(null); setResult(null)
    try { setResult(await runDemo()) }
    catch (e: unknown) { setError(e instanceof Error ? e.message : 'Unknown error') }
    finally { setLoading(false) }
  }

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      {/* Scenario card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-8">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#7C3AED] to-[#4F46E5] flex items-center justify-center text-white font-black text-lg shrink-0">
            A
          </div>
          <div>
            <p className="font-extrabold text-slate-900 text-lg">{PROFILE.name}</p>
            <p className="text-sm text-slate-400 font-semibold">{PROFILE.type} · {PROFILE.domain}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Type',   val: PROFILE.type   },
            { label: 'Domain', val: PROFILE.domain  },
            { label: 'Team',   val: PROFILE.size    },
            { label: 'Budget', val: PROFILE.budget  },
          ].map(item => (
            <div key={item.label} className="bg-purple-50 border border-purple-100 rounded-xl p-3">
              <p className="text-[10px] font-black text-purple-400 uppercase tracking-widest">{item.label}</p>
              <p className="text-sm font-bold text-slate-700 mt-0.5 leading-tight">{item.val}</p>
            </div>
          ))}
        </div>

        <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-3">Evaluating Against</p>
        <div className="flex flex-col gap-2.5 mb-6">
          {GRANTS.map(g => (
            <div key={g.id} className="flex items-center justify-between border border-slate-200 rounded-xl px-4 py-3">
              <div>
                <p className="font-bold text-slate-800 text-sm">{g.title}</p>
                <p className="text-xs text-slate-400 font-semibold mt-0.5">{g.funder} · {g.id}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full bg-purple-50 border border-purple-200 text-purple-600 text-[10px] font-bold">{g.tag}</span>
                <span className="text-sm font-extrabold text-emerald-600">{g.amount}</span>
              </div>
            </div>
          ))}
        </div>

        <button onClick={go} disabled={loading}
          className="flex items-center justify-center gap-2 px-8 py-3 rounded-xl
            bg-gradient-to-r from-[#7C3AED] to-[#4F46E5] text-white font-bold text-sm
            shadow-lg shadow-purple-900/20 hover:-translate-y-0.5 transition-all
            disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none">
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          {loading ? 'Running pipeline…' : 'Run Full Pipeline Demo'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-5 text-sm font-semibold">
          ⚠ {error}<br />
          <span className="font-normal mt-1 block text-slate-400">Start the backend: <code className="font-mono text-xs">uv run uvicorn app.main:app --reload</code></span>
        </div>
      )}

      {result && !loading && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6">
          <ResultTabs data={result} />
        </div>
      )}
    </div>
  )
}
