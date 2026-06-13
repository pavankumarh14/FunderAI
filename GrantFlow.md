## GrantFlow — Funding Opportunity 

**From backlog of RFPs to a ranked match list, eligibility verdict, and ready-to-review proposal draft — in one pipeline call** 

Theme: 04 — AI Meets Data  ·  Function: AI-Powered Grant Lifecycle Management 

Suggested stack: LLM (Azure OpenAI GPT-4o) · LangGraph · Embeddings · FastAPI · React  · Optional MS: Azure OpenAI · Azure Cognitive Search · Grants.gov / NIH Reporter APIs 

## **Problem Statement** 

## **Problem Background** 

Securing grant funding is one of the highest-leverage activities for a research group or early-stage startup — and one of the most time-consuming. A typical applicant must discover relevant opportunities from fragmented sources (Grants.gov, NIH Reporter, foundation websites, agency RFP emails), manually screen dozens of RFPs for eligibility, assemble supporting documents, and draft a proposal under a hard deadline with limited staff. The discovery and triage steps alone — reading every RFP to decide whether it is worth pursuing — can consume days of a researcher's time that could have been spent on the work the grant is meant to fund. The result is that promising applicants miss opportunities they were eligible for simply because the overhead of evaluating them was too high. 

## **Why It Matters** 

Grant funding is not evenly distributed. Well-resourced institutions with dedicated grants offices have staff to manage the discovery, triage, and drafting pipeline. Smaller research groups and startups do not. AI-powered grant management levels that playing field: a five-person team can now evaluate and respond to opportunities at the same speed as a twenty-person grants office. Beyond access, the downstream impact is real — every incremental piece of research or startup that reaches funding represents work that would otherwise not have happened. 

## **Solution Summary** 

## **Why This Problem Was Chosen** 

Grant lifecycle management decomposes cleanly into five sequential reasoning steps — discover, qualify, identify gaps, draft, plan — each of which is a natural LLM task. The inputs (applicant profile, grant requirements) are structured and bounded. The outputs (ranked 

matches, eligibility decisions, proposal drafts) are high-value and directly usable. It is a domain where the AI does the tedious analytical work and the human does the judgement and writing refinement. 

## **Proposed Solution** 

GrantFlow ingests an applicant profile (organisation type, domain, team size, project description, budget) alongside a list of grant opportunities (title, funder, deadline, requirements, description) and runs them through a five-agent LangGraph pipeline. The 

OpportunityDiscoveryAgent scores each grant 0–100 against the applicant profile. The EligibilityAgent flags hard disqualifiers and confirms which grants the applicant can legally pursue. The GapAnalysisAgent lists missing documents or data for each eligible grant. The ProposalDraftingAgent writes an executive summary and project narrative for the top-ranked match. The SubmissionRoadmapAgent builds a week-by-week milestone plan and submission checklist for each viable grant. The full pipeline runs in a single API call and returns all five outputs together. 

## **Expected Impact** 

- Hours of manual RFP triage replaced by a ranked match list with score rationale. 

- Hard eligibility disqualifiers surfaced before any drafting work begins. 

- A first proposal draft produced in seconds — the human's job shifts from writing from scratch to reviewing and refining. 

- A concrete, week-by-week submission roadmap so deadlines are not missed. 

## **Technical Approach & Implementation** 

## **Solution Workflow** 

The applicant submits their profile and a list of grant opportunities via POST /api/evaluate. The five agents run sequentially through the LangGraph pipeline. OpportunityDiscoveryAgent scores each grant using the applicant profile as context. EligibilityAgent checks each positively-scored grant against hard eligibility criteria (entity type, budget range, geography, prior grant requirements). GapAnalysisAgent maps each eligible grant's requirements against the applicant's stated capabilities and lists what is missing. ProposalDraftingAgent generates draft text for the top eligible grant. SubmissionRoadmapAgent produces a milestone plan working backwards from the deadline. A GET /api/demo endpoint runs the full pipeline against Aurora AI Labs (a synthetic AI/cleantech startup) evaluated against DOE and NSF SBIR grants. 

## **Key Features** 

- **Opportunity Scoring —** Each grant receives a 0–100 match score with a brief rationale, so the applicant can triage quickly. 

- **Eligibility Gate —** Hard disqualifiers (wrong entity type, out-of-range budget, geography) are flagged before any drafting work begins. 

- **Gap Analysis —** A checklist of missing documents or data per grant — so the applicant knows exactly what to gather. 

- **Proposal Draft Generation —** Executive summary and project narrative drafted for the top-ranked match, preserving the applicant's voice from the profile description. 

- **Week-by-Week Submission Roadmap —** Milestone plan with specific tasks, owners, and dependencies anchored to the grant deadline. 

## **Technology Stack** 

## **Frontend** 

- React + TypeScript 

- Tailwind CSS 

- DemoView, EvaluateView, ResultTabs (matches / eligibility / gaps / proposal / roadmap) 

- Tabbed result display for multi-output pipeline 

## **Backend** 

- Python 3.11 + FastAPI 

- LangGraph for five-agent sequential pipeline 

- LangChain (Azure OpenAI, OpenAI, Gemini adapters) 

- structlog 

## **AI / ML** 

- GPT-4o for all five agent reasoning steps 

- Embeddings for nearest-neighbour grant matching against a vector store of RFPs (future) 

- Structured JSON output parsing for reliable score and gap extraction 

## **Data & Integrations** 

- Grants.gov API — federal grant database (future) 

- NIH Reporter — NIH-funded research grants (future) 

- Azure Cognitive Search — vector store over scraped RFP corpus (future) 

- PDF ingestion for grant documents via pypdf (future) 

## **Models & Algorithms** 

OpportunityDiscoveryAgent uses a scoring prompt that evaluates alignment across five dimensions (domain match, entity type, budget fit, stage fit, geographic eligibility) and returns a weighted composite score. EligibilityAgent applies a deterministic rules check first (entity type allowlists, budget range comparisons) before the LLM handles ambiguous eligibility language. GapAnalysisAgent performs a structured diff between the grant's requirements list and the applicant's capabilities, producing a prioritised missing-items list. ProposalDraftingAgent receives the applicant profile, the gap analysis, and the grant description and uses 

chain-of-thought prompting to produce a coherent narrative that addresses the funder's priorities. SubmissionRoadmapAgent works backwards from the deadline to assign milestones with buffer time for review and revision cycles. 

## **Innovation** 

End-to-end pipeline in a single call — the applicant does not manage five separate tools; they submit a profile and receive a complete grant strategy package. The eligibility gate before drafting is a key design decision: it prevents the system from wasting drafting compute on grants the applicant cannot win. The roadmap is deadline-anchored rather than generic, so the output is immediately actionable as a project plan rather than a list of suggestions. 

## **Future Scope** 

## **Near-term** 

- Real grant database integration — connect to Grants.gov and NIH Reporter so available_grants is populated automatically. 

- PDF / RFP ingestion — a /ingest endpoint that parses uploaded grant PDFs into GrantOpportunity objects. 

- Uncomment all five LLM agent calls once Azure credentials are configured. 

## **Medium-term** 

- Deterministic eligibility rules engine layered before the LLM check for speed and reliability. 

- Streaming responses via Server-Sent Events so the UI shows each agent result as it completes. 

- Persistent sessions with Redis so applicants can resume or iterate on a proposal draft. 

## **Long-term** 

- Submission success tracking — correlate proposal characteristics with funding outcomes to improve the scoring model over time. 

- Collaborative drafting — multiple team members can annotate and refine the AI-generated proposal draft in a shared editor. 

- Portfolio view — manage multiple simultaneous grant applications across a research group or portfolio company. 

## **Scalability & Larger Vision** 

## **How It Scales** 

Each pipeline call is stateless and independently parallelisable. A single applicant evaluating fifty grants in one call runs the same agent graph as one evaluating two — the LangGraph pipeline handles the list iteration. Across an organisation, each team or project maintains its own applicant profile, and the same pipeline logic serves every profile without per-tenant customisation. Adding a vector store of RFPs enables opportunistic matching — the system suggests relevant grants the applicant did not know to submit, scaling discovery beyond what any individual can monitor. 

## **How It Expands** 

The near-term priority is connecting to live grant databases so the opportunity list is populated automatically rather than manually entered. Medium term, streaming responses and persistent sessions make the tool interactive — an applicant can refine their profile, see scores update in real time, and iterate on draft text. Long term, submission outcome tracking creates a feedback loop: successful proposals improve the drafting model, and funding rate data refines the opportunity-scoring weights. 

## **The Larger Vision** 

Grant management stops being a specialist skill that only well-resourced institutions can afford and becomes infrastructure that any research team or startup can access. The end state is an organisation where no eligible funding opportunity is missed because of bandwidth, where proposals are drafted in minutes not weeks, and where the entire submission pipeline — from discovery to filing — is managed by a system that surfaces what needs human attention and handles the rest. 

## **Potential Impact** 

For a single research group, GrantFlow replaces days of manual triage with a ranked shortlist and a first draft, freeing researchers to focus on the science. For a university grants office, it scales the capacity to evaluate and respond to opportunities without proportionally scaling headcount. At sector level, lowering the barrier to grant application increases the diversity of organisations that successfully compete for public and private funding — directing more resources toward high-quality work that might otherwise go unfunded. 

