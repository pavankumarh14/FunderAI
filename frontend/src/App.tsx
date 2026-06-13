import { useState, useEffect } from 'react'
import EvaluateView from './components/EvaluateView'
import DemoView from './components/DemoView'
import { View } from './types'
import { healthCheck } from './api'

export default function App() {
  const [view,         setView]         = useState<View>('evaluate')
  const [serverOnline, setServerOnline] = useState<boolean | null>(null)

  useEffect(() => {
    healthCheck().then(setServerOnline)
    const id = setInterval(() => healthCheck().then(setServerOnline), 30_000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen bg-[#FAFAF9] flex flex-col">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#7C3AED] to-[#4F46E5] flex items-center justify-center text-white font-black text-sm">
              F
            </div>
            <span className="font-extrabold text-slate-900 text-[15px]">FunderAI</span>
            <span className="px-2 py-0.5 rounded-full bg-purple-50 border border-purple-200 text-purple-600 text-[10px] font-bold uppercase tracking-wide">
              Funding Copilot
            </span>
          </div>

          <nav className="flex gap-1 ml-6">
            {(['evaluate', 'demo'] as View[]).map(v => (
              <button key={v} onClick={() => setView(v)}
                className={`px-4 py-1.5 rounded-lg text-sm font-bold capitalize transition-all
                  ${view === v ? 'bg-[#7C3AED] text-white' : 'text-slate-500 hover:bg-purple-50 hover:text-[#7C3AED]'}`}>
                {v === 'evaluate' ? 'Evaluate Grants' : 'Demo'}
              </button>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${serverOnline ? 'bg-emerald-400' : 'bg-slate-300'}`} />
            <span className="text-xs font-semibold text-slate-400">
              {serverOnline === null ? 'Checking…' : serverOnline ? 'API online' : 'API offline'}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        {view === 'evaluate' && <EvaluateView />}
        {view === 'demo'     && <DemoView />}
      </main>
    </div>
  )
}
