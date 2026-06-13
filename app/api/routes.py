from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.agents.graph import graph
from app.agents.nodes import ingest_pdf_to_grant
from app.agents.state import ApplicantProfile, GrantFlowState, GrantOpportunity

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models (Pydantic — separate from the dataclasses used
# internally by LangGraph so FastAPI can auto-generate OpenAPI docs)
# ---------------------------------------------------------------------------


class ApplicantProfileRequest(BaseModel):
    name: str = ""
    organization_type: str = ""
    domain: str = ""
    team_size: int = 0
    previous_grants: list[str] = []
    project_description: str = ""
    budget_requested: float = 0.0


class GrantOpportunityRequest(BaseModel):
    grant_id: str = ""
    title: str = ""
    funder: str = ""
    deadline: str = ""
    amount: str = ""
    requirements: list[str] = []
    description: str = ""


class EvaluateRequest(BaseModel):
    applicant: ApplicantProfileRequest
    grants: list[GrantOpportunityRequest]


class EvaluateResponse(BaseModel):
    matched_opportunities: list[dict]
    eligibility_results: list[dict]
    gap_analysis: list[dict]
    proposal_drafts: list[dict]
    submission_roadmap: dict
    error: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_initial_state(
    applicant_req: ApplicantProfileRequest,
    grants_req: list[GrantOpportunityRequest],
) -> GrantFlowState:
    applicant = ApplicantProfile(
        name=applicant_req.name,
        organization_type=applicant_req.organization_type,
        domain=applicant_req.domain,
        team_size=applicant_req.team_size,
        previous_grants=applicant_req.previous_grants,
        project_description=applicant_req.project_description,
        budget_requested=applicant_req.budget_requested,
    )
    available_grants = [
        GrantOpportunity(
            grant_id=g.grant_id,
            title=g.title,
            funder=g.funder,
            deadline=g.deadline,
            amount=g.amount,
            requirements=g.requirements,
            description=g.description,
        )
        for g in grants_req
    ]
    return GrantFlowState(applicant=applicant, available_grants=available_grants)


def _state_to_response(final_state) -> EvaluateResponse:
    # Handle both dict and GrantFlowState object
    if isinstance(final_state, dict):
        state_dict = final_state
    else:
        state_dict = {
            "available_grants": final_state.available_grants,
            "matched_opportunities": final_state.matched_opportunities,
            "eligibility_results": final_state.eligibility_results,
            "gap_analysis": final_state.gap_analysis,
            "proposal_drafts": final_state.proposal_drafts,
            "submission_roadmap": final_state.submission_roadmap,
            "error": final_state.error,
        }
    
    # Create a map of grant_id to grant details for enrichment
    grant_map = {}
    available_grants = state_dict.get("available_grants", [])
    for g in available_grants:
        if isinstance(g, dict):
            grant_map[g.get("grant_id")] = g
        else:
            grant_map[g.grant_id] = g
    
    # Enrich matched opportunities with grant details
    enriched_matches = []
    for match in state_dict.get("matched_opportunities", []):
        grant = grant_map.get(match.get("grant_id"))
        enriched = {**match}
        if grant:
            if isinstance(grant, dict):
                enriched["title"] = grant.get("title")
                enriched["funder"] = grant.get("funder")
                enriched["amount"] = grant.get("amount")
                enriched["deadline"] = grant.get("deadline")
            else:
                enriched["title"] = grant.title
                enriched["funder"] = grant.funder
                enriched["amount"] = grant.amount
                enriched["deadline"] = grant.deadline
        enriched_matches.append(enriched)
    
    # Enrich eligibility results with grant details
    enriched_eligibility = []
    for result in state_dict.get("eligibility_results", []):
        grant = grant_map.get(result.get("grant_id"))
        enriched = {**result}
        if grant:
            if isinstance(grant, dict):
                enriched["title"] = grant.get("title")
                enriched["funder"] = grant.get("funder")
            else:
                enriched["title"] = grant.title
                enriched["funder"] = grant.funder
        enriched_eligibility.append(enriched)
    
    # Enrich gap analysis with grant details
    enriched_gaps = []
    for gap in state_dict.get("gap_analysis", []):
        grant = grant_map.get(gap.get("grant_id"))
        enriched = {**gap}
        if grant:
            if isinstance(grant, dict):
                enriched["grant_title"] = grant.get("title")
            else:
                enriched["grant_title"] = grant.title
        enriched_gaps.append(enriched)
    
    return EvaluateResponse(
        matched_opportunities=enriched_matches,
        eligibility_results=enriched_eligibility,
        gap_analysis=enriched_gaps,
        proposal_drafts=state_dict.get("proposal_drafts", []),
        submission_roadmap=state_dict.get("submission_roadmap", {}),
        error=state_dict.get("error"),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/health")
async def health() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "service": "funderai"}


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(body: EvaluateRequest) -> EvaluateResponse:
    """
    Run the full FunderAI pipeline for the provided applicant and grant list.

    The pipeline runs five agents in sequence:
    OpportunityDiscovery -> Eligibility -> GapAnalysis -> ProposalDrafting -> SubmissionRoadmap
    """
    if not body.grants:
        raise HTTPException(status_code=422, detail="At least one grant opportunity is required.")

    initial_state = _build_initial_state(body.applicant, body.grants)
    try:
        final_state: GrantFlowState = await graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Graph execution failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _state_to_response(final_state)


@router.get("/demo", response_model=EvaluateResponse)
async def demo() -> EvaluateResponse:
    """
    Run the pipeline with a synthetic AI/cleantech startup and two grant opportunities.
    Use this endpoint to verify the system is working without supplying your own data.
    """
    applicant = ApplicantProfileRequest(
        name="Aurora AI Labs",
        organization_type="startup",
        domain="cleantech",
        team_size=8,
        previous_grants=["NSF SBIR Phase I 2022"],
        project_description=(
            "We develop AI-driven energy optimization software for commercial buildings, "
            "reducing carbon emissions by up to 35% through real-time demand forecasting "
            "and adaptive HVAC control."
        ),
        budget_requested=750_000.0,
    )

    grants = [
        GrantOpportunityRequest(
            grant_id="doe-iija-2025",
            title="DOE Building Efficiency Innovation Grant 2025",
            funder="U.S. Department of Energy",
            deadline="2025-09-30",
            amount="$500,000 – $2,000,000",
            requirements=[
                "U.S.-incorporated entity",
                "Minimum 3 FTE dedicated to project",
                "Demonstrated prototype or pilot deployment",
                "Focus on commercial or industrial building efficiency",
                "Cost-share of 20% required",
            ],
            description=(
                "Supports innovative technology solutions that reduce energy consumption "
                "in commercial and industrial buildings by at least 25% compared to baseline."
            ),
        ),
        GrantOpportunityRequest(
            grant_id="nsf-sbir-2025",
            title="NSF SBIR Phase II — Climate Technology",
            funder="National Science Foundation",
            deadline="2025-11-15",
            amount="Up to $1,000,000",
            requirements=[
                "Must have completed NSF SBIR Phase I",
                "Small business (fewer than 500 employees)",
                "Principal investigator holds a doctorate or equivalent research experience",
                "Technology must have clear commercialization pathway",
            ],
            description=(
                "Phase II award to scale research findings from a Phase I project into a "
                "commercially viable climate technology product or service."
            ),
        ),
    ]

    initial_state = _build_initial_state(applicant, grants)
    try:
        final_state: GrantFlowState = await graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Demo graph execution failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _state_to_response(final_state)


@router.post("/ingest")
async def ingest_pdf(file: UploadFile = File(...)) -> GrantOpportunityRequest:
    """
    Upload a grant PDF/RFP and extract structured data into a GrantOpportunity.
    Uses LLM to parse the document, falls back to demo stub if LLM fails or isn't configured.
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        
        # Read file bytes
        pdf_bytes = await file.read()
        
        # Ingest PDF and create grant opportunity
        grant = await ingest_pdf_to_grant(pdf_bytes)
        
        # Convert to Pydantic model for response
        return GrantOpportunityRequest(
            grant_id=grant.grant_id,
            title=grant.title,
            funder=grant.funder,
            deadline=grant.deadline,
            amount=grant.amount,
            requirements=grant.requirements,
            description=grant.description,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PDF ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
