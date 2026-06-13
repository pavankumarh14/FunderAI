export type View = 'evaluate' | 'demo'
export type ResultTab = 'matches' | 'eligibility' | 'gaps' | 'proposal' | 'roadmap'

export interface GrantInput {
  grant_id: string
  title: string
  funder: string
  deadline: string
  amount: string
  requirements: string
  description: string
}

export interface ApplicantProfileRequest {
  name: string
  organization_type: string
  domain: string
  team_size: number
  previous_grants: string[]
  project_description: string
  budget_requested: number
}

export interface GrantOpportunityRequest {
  grant_id: string
  title: string
  funder: string
  deadline: string
  amount: string
  requirements: string[]
  description: string
}

export interface EvaluateRequest {
  applicant: ApplicantProfileRequest
  grants: GrantOpportunityRequest[]
}

export interface MatchedOpportunity {
  grant_id?: string
  grant_title?: string
  title?: string
  funder?: string
  match_score?: number
  score?: number
  rationale?: string
  amount?: string
  deadline?: string
  [key: string]: unknown
}

export interface EligibilityResult {
  grant_id?: string
  grant_title?: string
  title?: string
  eligible?: boolean
  status?: string
  notes?: string | string[]
  disqualifiers?: string[]
  [key: string]: unknown
}

export interface GapItem {
  grant_id?: string
  grant_title?: string
  gaps?: string[]
  missing?: string[]
  [key: string]: unknown
}

export interface ProposalDraft {
  grant_id?: string
  executive_summary?: string
  summary?: string
  project_narrative?: string
  narrative?: string
  [key: string]: unknown
}

export interface RoadmapMilestone {
  week?: string | number
  timeframe?: string
  milestone?: string
  task?: string
  action?: string
  description?: string
  details?: string
  [key: string]: unknown
}

export interface SubmissionRoadmap {
  milestones?: RoadmapMilestone[]
  weeks?: RoadmapMilestone[]
  steps?: RoadmapMilestone[]
  checklist?: string[]
  [key: string]: unknown
}

export interface EvaluateResponse {
  matched_opportunities: MatchedOpportunity[]
  eligibility_results: EligibilityResult[]
  gap_analysis: GapItem[]
  proposal_drafts: ProposalDraft[]
  submission_roadmap: SubmissionRoadmap
  error?: string | null
}
