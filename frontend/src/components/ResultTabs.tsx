import { useState } from 'react'
import { EvaluateResponse, ResultTab, MatchedOpportunity, EligibilityResult, GapItem, ProposalDraft, RoadmapMilestone } from '../types'

interface Props { data: EvaluateResponse }

const TABS: { id: ResultTab; label: string }[] = [
  { id: 'matches',     label: 'Matches'     },
  { id: 'eligibility', label: 'Eligibility' },
  { id: 'gaps',        label: 'Gaps'        },
  { id: 'proposal',    label: 'Proposal'    },
  { id: 'roadmap',     label: 'Roadmap'     },
]

export default function ResultTabs({ data }: Props) {
  const [tab, setTab] = useState<ResultTab>('matches')

  return (
    <div className="flex flex-col gap-0">
      {/* Tab bar */}
      <div className="flex gap-0 border-b border-slate-200 mb-5">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-sm font-bold border-b-2 transition-all -mb-px
              ${tab === t.id
                ? 'border-[#7C3AED] text-[#7C3AED]'
                : 'border-transparent text-slate-400 hover:text-slate-600'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Matches */}
      {tab === 'matches' && (
        <div className="flex flex-col gap-3">
          {data.matched_opportunities.length === 0
            ? <Empty text="No match data returned." />
            : data.matched_opportunities.map((m: MatchedOpportunity, i) => {
              const score = m.match_score ?? m.score ?? 0
              const scoreStyle = score >= 70 ? 'bg-emerald-100 text-emerald-700' : score >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-600'
              return (
                <div key={i} className="border border-slate-200 rounded-xl p-5 hover:border-purple-300 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-bold text-slate-800">{m.grant_title ?? m.title ?? m.grant_id}</p>
                      {m.funder && <p className="text-xs text-slate-400 font-semibold mt-0.5">{m.funder}</p>}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-extrabold shrink-0 ${scoreStyle}`}>
                      {score}/100
                    </span>
                  </div>
                  {m.rationale && <p className="text-sm text-slate-500 mt-2 leading-relaxed">{m.rationale}</p>}
                  <div className="flex gap-4 mt-2.5">
                    {m.amount   && <Meta label="Amount"   val={String(m.amount)}   />}
                    {m.deadline && <Meta label="Deadline" val={String(m.deadline)} />}
                  </div>
                </div>
              )
            })}
        </div>
      )}

      {/* Eligibility */}
      {tab === 'eligibility' && (
        <div className="flex flex-col gap-3">
          {data.eligibility_results.length === 0
            ? <Empty text="No eligibility data returned." />
            : data.eligibility_results.map((e: EligibilityResult, i) => {
              const ok = e.eligible !== false && e.status !== 'ineligible'
              return (
                <div key={i} className={`border rounded-xl p-5 flex gap-4 ${ok ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
                  <span className="text-2xl mt-0.5">{ok ? '✅' : '❌'}</span>
                  <div className="flex-1">
                    <p className="font-bold text-slate-800">{e.grant_title ?? e.title ?? e.grant_id}</p>
                    <p className={`text-sm font-bold mt-0.5 ${ok ? 'text-emerald-600' : 'text-red-600'}`}>
                      {ok ? 'Eligible' : 'Not Eligible'}{e.status ? ` — ${e.status}` : ''}
                    </p>
                    {Array.isArray(e.notes) ? e.notes.map((n, j) => (
                      <p key={j} className="text-xs text-slate-500 mt-1 pl-2 border-l-2 border-slate-200">{n}</p>
                    )) : e.notes ? (
                      <p className="text-xs text-slate-500 mt-1 pl-2 border-l-2 border-slate-200">{e.notes}</p>
                    ) : null}
                  </div>
                </div>
              )
            })}
        </div>
      )}

      {/* Gaps */}
      {tab === 'gaps' && (
        <div className="flex flex-col gap-4">
          {data.gap_analysis.length === 0
            ? <Empty text="No gap analysis returned." />
            : data.gap_analysis.map((g: GapItem, i) => {
              const items = g.gaps ?? g.missing ?? []
              return (
                <div key={i}>
                  <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">
                    {g.grant_id ?? g.grant_title ?? `Grant ${i + 1}`}
                  </p>
                  <div className="flex flex-col gap-1.5">
                    {items.map((item, j) => (
                      <div key={j} className="flex items-start gap-2 border-l-4 border-amber-400 bg-amber-50 rounded-r-xl px-4 py-2.5">
                        <span className="text-amber-500 mt-0.5">⚠</span>
                        <p className="text-sm text-slate-700 font-semibold">{item}</p>
                      </div>
                    ))}
                    {items.length === 0 && <p className="text-sm text-slate-400 italic">No gaps identified</p>}
                  </div>
                </div>
              )
            })}
        </div>
      )}

      {/* Proposal */}
      {tab === 'proposal' && (
        <div className="flex flex-col gap-5">
          {data.proposal_drafts.length === 0
            ? <Empty text="No proposal drafts returned." />
            : data.proposal_drafts.map((p: ProposalDraft, i) => (
              <div key={i} className="flex flex-col gap-4">
                {(p.executive_summary ?? p.summary) && (
                  <ProposalBlock title="Executive Summary" text={p.executive_summary ?? p.summary ?? ''} />
                )}
                {(p.project_narrative ?? p.narrative) && (
                  <ProposalBlock title="Project Narrative" text={p.project_narrative ?? p.narrative ?? ''} />
                )}
                {!p.executive_summary && !p.summary && !p.project_narrative && !p.narrative && (
                  <pre className="bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-slate-600 whitespace-pre-wrap leading-relaxed">
                    {JSON.stringify(p, null, 2)}
                  </pre>
                )}
              </div>
            ))}
        </div>
      )}

      {/* Roadmap */}
      {tab === 'roadmap' && (
        <div>
          {!data.submission_roadmap || Object.keys(data.submission_roadmap).length === 0
            ? <Empty text="No roadmap returned." />
            : (() => {
              const rm = data.submission_roadmap
              const milestones = rm.milestones ?? rm.weeks ?? rm.steps ?? []
              return (
                <div className="flex flex-col gap-2.5">
                  {milestones.map((m: RoadmapMilestone, i: number) => {
                    const week  = m.week ?? m.timeframe ?? `Step ${i + 1}`
                    const title = m.milestone ?? m.task ?? m.action ?? m.description ?? ''
                    const detail = m.details ?? (m.description !== title ? m.description : '') ?? ''
                    return (
                      <div key={i} className="flex items-start gap-3 border border-slate-200 rounded-xl px-4 py-3">
                        <span className="shrink-0 bg-[#7C3AED] text-white text-[11px] font-black rounded-lg px-2.5 py-1.5 leading-tight min-w-[48px] text-center">
                          {String(week)}
                        </span>
                        <div>
                          <p className="text-sm font-bold text-slate-800">{title}</p>
                          {detail && <p className="text-xs text-slate-400 mt-0.5">{String(detail)}</p>}
                        </div>
                      </div>
                    )
                  })}
                  {rm.checklist && rm.checklist.length > 0 && (
                    <div className="mt-2">
                      <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">Checklist</p>
                      {rm.checklist.map((item, i) => (
                        <div key={i} className="flex items-center gap-2 py-1.5">
                          <span className="w-4 h-4 rounded border-2 border-purple-300 flex-shrink-0" />
                          <p className="text-sm text-slate-600">{item}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })()}
        </div>
      )}
    </div>
  )
}

function Meta({ label, val }: { label: string; val: string }) {
  return <span className="text-xs text-slate-400 font-semibold"><strong className="text-slate-600">{label}:</strong> {val}</span>
}
function ProposalBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
      <p className="text-[11px] font-black text-purple-500 uppercase tracking-widest mb-2">{title}</p>
      <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  )
}
function Empty({ text }: { text: string }) {
  return <p className="text-sm text-slate-400 italic py-4">{text}</p>
}
