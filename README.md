# FunderAI — Funding Opportunity Copilot

FunderAI is an AI-powered FastAPI service that guides researchers and startups through the entire grant application lifecycle — from discovering matching opportunities to producing a ready-to-submit proposal and timeline.

---

## What FunderAI does

1. **Ingests** an applicant profile (organization type, domain, team size, project description, budget) alongside a list of grant opportunities (title, funder, deadline, requirements).
2. **Runs a 5-agent LangGraph pipeline** that progressively enriches the analysis.
3. **Returns** ranked matches, eligibility verdicts, gap analysis, draft proposal sections, and a week-by-week submission roadmap — all in a single API call.

---

## 5-Agent Pipeline

```
START
  │
  ▼
OpportunityDiscoveryAgent   — scores each grant 0-100 against the applicant profile
  │
  ▼
EligibilityAgent            — flags hard disqualifiers; confirms eligible grants
  │
  ▼
GapAnalysisAgent            — lists missing documents / data for each eligible grant
  │
  ▼
ProposalDraftingAgent       — drafts executive summary + project narrative for top match
  │
  ▼
SubmissionRoadmapAgent      — builds week-by-week milestones and a submission checklist
  │
  ▼
END
```

---

## Current State

| Agent | Status | Notes |
|---|---|---|
| OpportunityDiscoveryAgent | Placeholder | Returns demo scores; LLM call commented in `nodes.py` |
| EligibilityAgent | Placeholder | Returns demo eligibility; LLM call commented in `nodes.py` |
| GapAnalysisAgent | Placeholder | Returns demo gaps; LLM call commented in `nodes.py` |
| ProposalDraftingAgent | Placeholder | Returns stub text; LLM call commented in `nodes.py` |
| SubmissionRoadmapAgent | **LLM-wired** | Makes a real GPT-4o call; falls back to demo stub if Azure is unconfigured |

All five agents have their full LLM implementations written and commented directly in `app/agents/nodes.py`. Enabling them requires only Azure credentials and uncommenting the relevant block.

---

## Frontend

A React + Vite + Tailwind UI is included in the `frontend/` directory.

```
frontend/
└── src/
    ├── components/
    │   ├── DemoView.tsx      # One-click demo using Aurora AI Labs synthetic data
    │   ├── EvaluateView.tsx  # Form for submitting a custom applicant + grant list
    │   └── ResultTabs.tsx    # Tabbed display of matches, eligibility, gaps, proposal, roadmap
    ├── api.ts                # Typed fetch wrappers
    ├── types.ts              # Shared TypeScript types
    └── App.tsx
```

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ and [pnpm](https://pnpm.io/)

### Install backend

```bash
cd D:/Coding/prototypes/grantflow
uv sync
```

### Configure environment

```bash
cp .env.example .env
# Edit .env — set LLM_PROVIDER and credentials for your chosen provider
```

`.env` fields:

| Variable | Description |
|---|---|
| `LLM_PROVIDER` | `azure` (default) \| `openai` \| `gemini` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | API version (default: `2024-02-01`) |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Deployment name for GPT-4o |
| `OPENAI_API_KEY` | OpenAI API key (if using `openai` provider) |
| `GEMINI_API_KEY` | Google Gemini API key (if using `gemini` provider) |
| `APP_ENV` | `development` or `production` |

### Run the backend

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

### Run the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend available at `http://localhost:5173`. The Vite dev server proxies all `/api/*` requests to `http://localhost:8000` automatically.

---

## Test with the demo endpoint

```bash
curl http://localhost:8000/api/demo | python -m json.tool
```

The demo uses a synthetic AI/cleantech startup ("Aurora AI Labs") against two real-world-style grants (DOE Building Efficiency and NSF SBIR Phase II). No credentials required — all agents fall back to demo stubs gracefully.

---

## API Reference

### `GET /api/health`
Liveness probe. Returns `{"status": "ok"}`.

### `GET /api/demo`
Runs the full pipeline with built-in synthetic data. Useful for integration testing.

### `POST /api/evaluate`
Run the pipeline with your own data.

**Request body:**
```json
{
  "applicant": {
    "name": "My Startup",
    "organization_type": "startup",
    "domain": "cleantech",
    "team_size": 5,
    "previous_grants": [],
    "project_description": "...",
    "budget_requested": 500000
  },
  "grants": [
    {
      "grant_id": "grant-001",
      "title": "Example Grant",
      "funder": "DOE",
      "deadline": "2025-12-01",
      "amount": "$250,000 – $1,000,000",
      "requirements": ["U.S. entity", "Pilot deployment required"],
      "description": "..."
    }
  ]
}
```

**Response:** `matched_opportunities`, `eligibility_results`, `gap_analysis`, `proposal_drafts`, `submission_roadmap`.

---

## Next Steps

1. **Real grant database integration** — connect to Grants.gov, NIH Reporter, or a vector store of scraped RFPs so `available_grants` is populated automatically.
2. **PDF / RFP ingestion** — add a `/ingest` endpoint that parses uploaded grant PDFs into `GrantOpportunity` objects using a document extraction pipeline.
3. **Eligibility rules engine** — replace the LLM-only eligibility check with a deterministic rules layer (e.g., organization type allow-list, budget range checks) before the LLM for speed and reliability.
4. **Uncomment LLM calls** — for each placeholder node in `app/agents/nodes.py`, remove the demo stub and uncomment the LLM block once Azure credentials are in place.
5. **Structured output parsing** — use `langchain_core.output_parsers.JsonOutputParser` or Pydantic output schemas to replace the ad-hoc `_safe_parse_json` helper.
6. **Streaming responses** — switch the `/evaluate` endpoint to Server-Sent Events so the UI can show each agent's result as it completes.
7. **Persistent sessions** — add a session ID + Redis/Postgres store so users can resume an evaluation or iterate on a proposal draft.
