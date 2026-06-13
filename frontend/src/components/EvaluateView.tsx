import { useState } from 'react'
import { Plus, Trash2, Loader2, ChevronRight, Upload } from 'lucide-react'
import { EvaluateResponse, GrantInput, EvaluateRequest, GrantOpportunityRequest } from '../types'
import { evaluate, ingestPdf } from '../api'
import ResultTabs from './ResultTabs'

const BLANK_GRANT = (): GrantInput => ({
  grant_id: '', title: '', funder: '', deadline: '', amount: '', requirements: '', description: '',
})

const PIPELINE_STEPS = ['Match Grants', 'Check Eligibility', 'Analyze Gaps', 'Draft Proposals']

export default function EvaluateView() {
  const [orgName,      setOrgName]      = useState('')
  const [orgType,      setOrgType]      = useState('')
  const [domain,       setDomain]       = useState('')
  const [teamSize,     setTeamSize]     = useState('')
  const [budget,       setBudget]       = useState('')
  const [description,  setDescription]  = useState('')
  const [grants,       setGrants]       = useState<GrantInput[]>([BLANK_GRANT()])
  const [loading,      setLoading]      = useState(false)
  const [ingesting,    setIngesting]    = useState(false)
  const [result,       setResult]       = useState<EvaluateResponse | null>(null)
  const [error,        setError]        = useState<string | null>(null)
  const [activeStep,   setActiveStep]   = useState<number>(-1)

  const updateGrant = (i: number, field: keyof GrantInput, val: string) =>
    setGrants(gs => gs.map((g, idx) => idx === i ? { ...g, [field]: val } : g))

  const parseBudget = (s: string): number => {
    const num = parseFloat(s.replace(/[^0-9.]/g, ''))
    return isNaN(num) ? 0 : num
  }

  const parseTeamSize = (s: string): number => {
    const num = parseInt(s.replace(/[^0-9]/g, ''))
    return isNaN(num) ? 0 : num
  }

  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    setIngesting(true)
    setError(null)
    
    try {
      const ingestedGrant = await ingestPdf(file)
      
      // Convert from backend format (requirements as array) to frontend format (comma-separated string)
      const frontendGrant: GrantInput = {
        grant_id: ingestedGrant.grant_id,
        title: ingestedGrant.title,
        funder: ingestedGrant.funder,
        deadline: ingestedGrant.deadline,
        amount: ingestedGrant.amount,
        requirements: ingestedGrant.requirements.join(', '),
        description: ingestedGrant.description,
      }
      
      // Add to grants list
      setGrants(gs => [...gs, frontendGrant])
      
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to ingest PDF')
    } finally {
      setIngesting(false)
      // Clear file input
      e.target.value = ''
    }
  }

  const submit = async () => {
    setLoading(true); setError(null); setResult(null); setActiveStep(0)
    try {
      const tick = setInterval(() => setActiveStep(s => Math.min(s + 1, 3)), 1800)
      
      // Transform grants to backend format (requirements as array)
      const backendGrants = grants.filter(g => g.title || g.grant_id).map(g => ({
        grant_id: g.grant_id,
        title: g.title,
        funder: g.funder,
        deadline: g.deadline,
        amount: g.amount,
        requirements: g.requirements.split(',').map(r => r.trim()).filter(r => r.length > 0),
        description: g.description,
      }))

      const payload: EvaluateRequest = {
        applicant: {
          name: orgName,
          organization_type: orgType,
          domain,
          team_size: parseTeamSize(teamSize),
          previous_grants: [],
          project_description: description,
          budget_requested: parseBudget(budget),
        },
        grants: backendGrants,
      }

      const res = await evaluate(payload)
      clearInterval(tick)
      setActiveStep(-1)
      setResult(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setActiveStep(-1)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Pipeline bar */}
      <div className="flex items-center gap-0 bg-purple-50 border border-purple-100 rounded-2xl px-6 py-4">
        {PIPELINE_STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-0 flex-1">
            <div className="flex flex-col items-center gap-1.5 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black transition-all
                ${loading && activeStep === i ? 'bg-[#7C3AED] text-white ring-4 ring-purple-200 scale-110' :
                  loading && activeStep > i  ? 'bg-emerald-500 text-white' :
                  'bg-white border-2 border-purple-200 text-purple-400'}`}>
                {loading && activeStep > i ? '✓' : i + 1}
              </div>
              <span className={`text-[10px] font-bold text-center leading-tight
                ${loading && activeStep === i ? 'text-[#7C3AED]' : 'text-slate-400'}`}>{s}</span>
            </div>
            {i < PIPELINE_STEPS.length - 1 && (
              <ChevronRight size={14} className="text-purple-200 shrink-0 -mx-1" />
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Left: Form */}
        <div className="flex flex-col gap-6">
          {/* Applicant Profile */}
          <section className="bg-white border border-slate-200 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-[11px] font-black text-purple-500 uppercase tracking-widest">Applicant Profile</p>
              <button onClick={fillExamples}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-xs font-bold hover:bg-amber-100 transition-colors">
                <Sparkles size={12} /> Fill with Examples
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <Label>Organization Name</Label>
                <Input value={orgName} onChange={setOrgName} placeholder="Acme Nonprofit Inc." />
              </div>
              <div>
                <Label>Org Type</Label>
                <select value={orgType} onChange={e => setOrgType(e.target.value)}
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-purple-200">
                  <option value="">Select…</option>
                  <option>Nonprofit</option>
                  <option>University</option>
                  <option>Startup</option>
                  <option>Government</option>
                  <option>Research Institute</option>
                </select>
              </div>
              <div>
                <Label>Domain / Sector</Label>
                <Input value={domain} onChange={setDomain} placeholder="Clean Energy" />
              </div>
              <div>
                <Label>Team Size</Label>
                <Input value={teamSize} onChange={setTeamSize} placeholder="15 FTE" />
              </div>
              <div>
                <Label>Annual Budget</Label>
                <Input value={budget} onChange={setBudget} placeholder="$2M" />
              </div>
              <div className="col-span-2">
                <Label>Organization Description</Label>
                <textarea value={description} onChange={e => setDescription(e.target.value)}
                  rows={3} placeholder="Brief description of mission, programs, and track record…"
                  className="w-full border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-purple-200 resize-none" />
              </div>
            </div>
          </section>

          {/* Grant Opportunities */}
          <section className="bg-white border border-slate-200 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-[11px] font-black text-purple-500 uppercase tracking-widest">Grant Opportunities</p>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-50 border border-green-200 text-green-600 text-xs font-bold hover:bg-green-100 transition-colors cursor-pointer">
                  {ingesting ? <Loader2 size={12} className="animate-spin" /> : <Upload size={12} />}
                  {ingesting ? 'Ingesting...' : 'Upload PDF'}
                  <input
                    type="file"
                    accept="application/pdf"
                    onChange={handlePdfUpload}
                    disabled={ingesting}
                    className="hidden"
                  />
                </label>
                <button onClick={() => setGrants(gs => [...gs, BLANK_GRANT()])}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-50 border border-purple-200 text-purple-600 text-xs font-bold hover:bg-purple-100 transition-colors">
                  <Plus size={12} /> Add Grant
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-5">
              {grants.map((g, i) => (
                <div key={i} className="border border-slate-200 rounded-xl p-4 relative">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Grant {i + 1}</span>
                    {grants.length > 1 && (
                      <button onClick={() => setGrants(gs => gs.filter((_, idx) => idx !== i))}
                        className="text-slate-300 hover:text-red-400 transition-colors">
                        <Trash2 size={13} />
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2.5">
                    <div>
                      <Label>Grant ID</Label>
                      <Input value={g.grant_id} onChange={v => updateGrant(i, 'grant_id', v)} placeholder="DOE-2024-001" />
                    </div>
                    <div>
                      <Label>Title</Label>
                      <Input value={g.title} onChange={v => updateGrant(i, 'title', v)} placeholder="Clean Energy Grant" />
                    </div>
                    <div>
                      <Label>Funder</Label>
                      <Input value={g.funder} onChange={v => updateGrant(i, 'funder', v)} placeholder="Dept. of Energy" />
                    </div>
                    <div>
                      <Label>Deadline</Label>
                      <Input value={g.deadline} onChange={v => updateGrant(i, 'deadline', v)} placeholder="2024-09-30" />
                    </div>
                    <div>
                      <Label>Amount</Label>
                      <Input value={g.amount} onChange={v => updateGrant(i, 'amount', v)} placeholder="$500,000" />
                    </div>
                    <div>
                      <Label>Requirements</Label>
                      <Input value={g.requirements} onChange={v => updateGrant(i, 'requirements', v)} placeholder="501(c)(3), 3yr history" />
                    </div>
                    <div className="col-span-2">
                      <Label>Description</Label>
                      <Input value={g.description} onChange={v => updateGrant(i, 'description', v)} placeholder="Grant focus area and objectives…" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <button onClick={submit} disabled={loading || !orgName}
            className="flex items-center justify-center gap-2 py-3.5 rounded-xl
              bg-gradient-to-r from-[#7C3AED] to-[#4F46E5] text-white font-bold text-sm
              shadow-lg shadow-purple-900/20 hover:-translate-y-0.5 transition-all
              disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none">
            {loading ? <><Loader2 size={16} className="animate-spin" /> Running pipeline…</> : 'Evaluate Grant Fit'}
          </button>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-4 text-sm font-semibold">
              ⚠ {error}<br />
              <span className="font-normal mt-1 block text-slate-400">Start the backend: <code className="font-mono text-xs">uv run uvicorn app.main:app --reload</code></span>
            </div>
          )}
        </div>

        {/* Right: Results */}
        <div>
          {!result && !loading && (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center gap-3 border-2 border-dashed border-purple-100 rounded-2xl text-center px-8">
              <div className="w-14 h-14 rounded-2xl bg-purple-50 flex items-center justify-center text-2xl">📋</div>
              <p className="text-sm font-bold text-slate-500">Results will appear here</p>
              <p className="text-xs text-slate-400">Fill in the applicant profile and at least one grant, then click Evaluate.</p>
            </div>
          )}
          {loading && (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center gap-4 border border-purple-100 rounded-2xl bg-purple-50/40">
              <Loader2 size={32} className="text-purple-400 animate-spin" />
              <p className="text-sm font-bold text-purple-500">
                {activeStep >= 0 ? PIPELINE_STEPS[activeStep] + '…' : 'Processing…'}
              </p>
            </div>
          )}
          {result && !loading && (
            <div className="bg-white border border-slate-200 rounded-2xl p-6">
              <ResultTabs data={result} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Label({ children }: { children: React.ReactNode }) {
  return <p className="text-[10px] font-black text-slate-400 uppercase tracking-wide mb-1">{children}</p>
}
function Input({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-purple-200 placeholder:text-slate-300" />
  )
}
