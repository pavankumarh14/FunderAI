from __future__ import annotations

import json
import logging
from io import BytesIO
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pypdf import PdfReader

from app.agents.prompts import (
    ELIGIBILITY_PROMPT,
    GAP_ANALYSIS_PROMPT,
    OPPORTUNITY_DISCOVERY_PROMPT,
    PROPOSAL_DRAFTING_PROMPT,
    SUBMISSION_ROADMAP_PROMPT,
    PDF_INGESTION_PROMPT,
)
from app.agents.state import GrantFlowState, GrantOpportunity
from app.config.settings import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------


def _get_llm() -> BaseChatModel:
    """Instantiate a chat model from the configured LLM provider. Raises exception if not configured properly."""
    provider = settings.llm_provider.lower()
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_chat_model,
            temperature=0.2,
        )
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            google_api_key=settings.gemini_api_key,
            model=settings.gemini_chat_model,
            temperature=0.2,
        )
    if provider == "grok":
        if not settings.grok_api_key:
            raise ValueError("GROK_API_KEY is not configured")
        return ChatOpenAI(
            api_key=settings.grok_api_key,
            base_url="https://api.x.ai/v1",
            model=settings.grok_chat_model,
            temperature=0.2,
        )
    # Default: Azure OpenAI
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        raise ValueError("Azure OpenAI credentials are not configured")
    return AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,  # type: ignore[arg-type]
        api_version=settings.azure_openai_api_version,
        azure_deployment=settings.azure_openai_chat_deployment,
        temperature=0.2,
    )


def _profile_to_text(applicant) -> str:
    """Render an ApplicantProfile as a readable string for prompt injection."""
    return (
        f"Name: {applicant.name}\n"
        f"Organization type: {applicant.organization_type}\n"
        f"Domain: {applicant.domain}\n"
        f"Team size: {applicant.team_size}\n"
        f"Previous grants: {', '.join(applicant.previous_grants) or 'None'}\n"
        f"Project description: {applicant.project_description}\n"
        f"Budget requested: ${applicant.budget_requested:,.0f}"
    )


def _grants_to_text(grants) -> str:
    """Render a list of GrantOpportunity objects as readable text."""
    lines = []
    for g in grants:
        lines.append(
            f"[{g.grant_id}] {g.title} | Funder: {g.funder} | Deadline: {g.deadline} | "
            f"Amount: {g.amount}\n"
            f"  Description: {g.description}\n"
            f"  Requirements: {'; '.join(g.requirements) or 'Not specified'}"
        )
    return "\n\n".join(lines)


def _safe_parse_json(text: str) -> list | dict:
    """Attempt to extract and parse JSON from an LLM response string."""
    # Strip markdown code fences if present
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        # Remove first and last fence lines
        stripped = "\n".join(lines[1:-1]) if len(lines) > 2 else stripped
    return json.loads(stripped)


# ---------------------------------------------------------------------------
# Agent nodes
# ---------------------------------------------------------------------------


async def opportunity_discovery_node(state: GrantFlowState) -> dict:
    """
    OpportunityDiscoveryAgent — scores each available grant against the applicant profile.
    """
    try:
        llm = _get_llm()
        prompt = OPPORTUNITY_DISCOVERY_PROMPT.format(
            applicant_profile=_profile_to_text(state.applicant),
            available_grants=_grants_to_text(state.available_grants),
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        try:
            matched = _safe_parse_json(response.content)
            if isinstance(matched, dict):
                matched = [matched]
            if not isinstance(matched, list):
                raise ValueError("Expected JSON list")
            return {"matched_opportunities": matched}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("opportunity_discovery_node: JSON parse failed – %s", exc)
            # Fall through to demo stub
    except Exception as exc:
        logger.warning("opportunity_discovery_node: LLM call failed (%s) — using demo stub", exc)
        # Fall through to demo stub

    # Demo stub fallback
    demo_matches = []
    for i, grant in enumerate(state.available_grants[:2]):
        demo_matches.append(
            {
                "grant_id": grant.grant_id,
                "match_score": 92 - i * 15,
                "rationale": (
                    f"Strong domain alignment between '{state.applicant.domain}' and grant "
                    f"objectives — placeholder result, implement LLM call to score accurately."
                ),
            }
        )
    if not demo_matches:
        demo_matches = [
            {
                "grant_id": "demo-grant-1",
                "match_score": 92,
                "rationale": "Strong domain alignment - placeholder result",
            }
        ]
    return {"matched_opportunities": demo_matches}


async def eligibility_node(state: GrantFlowState) -> dict:
    """
    EligibilityAgent — determines whether the applicant meets each grant's
    eligibility criteria and flags hard disqualifiers.
    """
    try:
        llm = _get_llm()
        # Build a combined view of matched grants with their full requirements
        matched_ids = {m["grant_id"] for m in state.matched_opportunities}
        matched_grants = [g for g in state.available_grants if g.grant_id in matched_ids]
        prompt = ELIGIBILITY_PROMPT.format(
            applicant_profile=_profile_to_text(state.applicant),
            matched_grants_with_requirements=_grants_to_text(matched_grants),
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        try:
            results = _safe_parse_json(response.content)
            if isinstance(results, dict):
                results = [results]
            if not isinstance(results, list):
                raise ValueError("Expected JSON list")
            return {"eligibility_results": results}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("eligibility_node: JSON parse failed – %s", exc)
            # Fall through to demo stub
    except Exception as exc:
        logger.warning("eligibility_node: LLM call failed (%s) — using demo stub", exc)
        # Fall through to demo stub

    # Demo stub fallback
    demo_results = []
    for match in state.matched_opportunities:
        demo_results.append(
            {
                "grant_id": match["grant_id"],
                "eligible": True,
                "reasons": [
                    "Meets domain requirements",
                    "Organization type is eligible",
                    "Budget request within funder range",
                ],
                "disqualifiers": [],
            }
        )
    if not demo_results:
        demo_results = [
            {
                "grant_id": "demo-grant-1",
                "eligible": True,
                "reasons": ["Meets domain requirements"],
                "disqualifiers": [],
            }
        ]
    return {"eligibility_results": demo_results}


async def gap_analysis_node(state: GrantFlowState) -> dict:
    """
    GapAnalysisAgent — identifies missing documents and requirements for each
    eligible grant opportunity.
    """
    try:
        llm = _get_llm()
        eligible_ids = {r["grant_id"] for r in state.eligibility_results if r.get("eligible")}
        eligible_grants = [g for g in state.available_grants if g.grant_id in eligible_ids]
        prompt = GAP_ANALYSIS_PROMPT.format(
            applicant_profile=_profile_to_text(state.applicant),
            eligible_grants=_grants_to_text(eligible_grants),
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        try:
            analysis = _safe_parse_json(response.content)
            if isinstance(analysis, dict):
                analysis = [analysis]
            if not isinstance(analysis, list):
                raise ValueError("Expected JSON list")
            return {"gap_analysis": analysis}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("gap_analysis_node: JSON parse failed – %s", exc)
            # Fall through to demo stub
    except Exception as exc:
        logger.warning("gap_analysis_node: LLM call failed (%s) — using demo stub", exc)
        # Fall through to demo stub

    # Demo stub fallback
    demo_analysis = []
    for result in state.eligibility_results:
        if result.get("eligible"):
            demo_analysis.append(
                {
                    "grant_id": result["grant_id"],
                    "missing_items": [
                        "Budget justification sheet",
                        "Impact metrics data",
                        "Letters of support (minimum 2)",
                        "Proof of non-profit or incorporation status",
                        "CV / bios for all key personnel",
                    ],
                    "completeness_score": 65,
                }
            )
    if not demo_analysis:
        demo_analysis = [
            {
                "grant_id": "demo-grant-1",
                "missing_items": [
                    "Budget justification sheet",
                    "Impact metrics data",
                    "Letters of support",
                ],
                "completeness_score": 65,
            }
        ]
    return {"gap_analysis": demo_analysis}


async def proposal_drafting_node(state: GrantFlowState) -> dict:
    """
    ProposalDraftingAgent — drafts an executive summary and project narrative for
    the best-matched eligible grant.
    """
    try:
        llm = _get_llm()
        # Pick the top matched + eligible grant
        eligible_ids = {r["grant_id"] for r in state.eligibility_results if r.get("eligible")}
        top_match = next(
            (m for m in state.matched_opportunities if m["grant_id"] in eligible_ids), None
        )
        if top_match is None:
            return {"proposal_drafts": []}
        target_grant = next(
            (g for g in state.available_grants if g.grant_id == top_match["grant_id"]), None
        )
        gap = next(
            (ga for ga in state.gap_analysis if ga["grant_id"] == top_match["grant_id"]), {}
        )
        prompt = PROPOSAL_DRAFTING_PROMPT.format(
            applicant_profile=_profile_to_text(state.applicant),
            target_grant=_grants_to_text([target_grant]) if target_grant else "N/A",
            gap_analysis=json.dumps(gap, indent=2),
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        try:
            draft = _safe_parse_json(response.content)
            if isinstance(draft, dict):
                draft["grant_id"] = top_match["grant_id"]
            drafts = [draft]
            return {"proposal_drafts": drafts}
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("proposal_drafting_node: JSON parse failed – %s", exc)
            # Fall through to demo stub
    except Exception as exc:
        logger.warning("proposal_drafting_node: LLM call failed (%s) — using demo stub", exc)
        # Fall through to demo stub

    # Demo stub fallback
    target_id = (
        state.matched_opportunities[0]["grant_id"]
        if state.matched_opportunities
        else "demo-grant-1"
    )
    return {
        "proposal_drafts": [
            {
                "grant_id": target_id,
                "executive_summary": "Placeholder draft - implement LLM call",
                "project_narrative": "TODO: generate with GPT-4o",
            }
        ]
    }


async def submission_roadmap_node(state: GrantFlowState) -> dict:
    """
    SubmissionRoadmapAgent — terminal node that creates a week-by-week submission
    timeline working backward from the grant deadline.

    This node performs the actual LLM call when Azure credentials are configured.
    """
    # Resolve the target grant from the best eligible match
    eligible_ids = {r["grant_id"] for r in state.eligibility_results if r.get("eligible")}
    top_match = next(
        (m for m in state.matched_opportunities if m["grant_id"] in eligible_ids),
        state.matched_opportunities[0] if state.matched_opportunities else None,
    )

    target_grant_id = top_match["grant_id"] if top_match else "demo-grant-1"
    target_grant = next(
        (g for g in state.available_grants if g.grant_id == target_grant_id), None
    )
    gap = next(
        (ga for ga in state.gap_analysis if ga["grant_id"] == target_grant_id), {}
    )
    missing_items = gap.get("missing_items", [])

    grant_title = target_grant.title if target_grant else "Unknown Grant"
    grant_funder = target_grant.funder if target_grant else "Unknown Funder"
    grant_deadline = target_grant.deadline if target_grant else "TBD"
    grant_amount = target_grant.amount if target_grant else "TBD"

    # LLM call
    try:
        llm = _get_llm()
        prompt = SUBMISSION_ROADMAP_PROMPT.format(
            applicant_profile=_profile_to_text(state.applicant),
            grant_title=grant_title,
            grant_funder=grant_funder,
            grant_deadline=grant_deadline,
            grant_amount=grant_amount,
            missing_items="\n".join(f"- {item}" for item in missing_items) or "None identified",
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])

        # TODO: parse LLM output into structured milestones with dates
        # Currently we attempt JSON parsing with a fallback to a raw text milestone.
        try:
            roadmap_data = _safe_parse_json(response.content)
            roadmap = {
                "grant_id": target_grant_id,
                "deadline": grant_deadline,
                **roadmap_data,
            }
        except (json.JSONDecodeError, ValueError):
            logger.warning("submission_roadmap_node: JSON parse failed, storing raw output")
            roadmap = {
                "grant_id": target_grant_id,
                "deadline": grant_deadline,
                "milestones": [{"week": 1, "task": response.content}],
                "submission_checklist": [],
            }

    except Exception as exc:
        logger.warning("submission_roadmap_node: LLM call failed (%s) — using demo stub", exc)
        # Demo fallback when Azure is not configured
        roadmap = {
            "grant_id": target_grant_id,
            "deadline": grant_deadline,
            "milestones": [
                {"week": 1, "task": "Gather missing documents", "owner": "applicant", "priority": "high"},
                {"week": 2, "task": "Prepare budget justification", "owner": "finance team", "priority": "high"},
                {"week": 3, "task": "Collect letters of support", "owner": "applicant", "priority": "medium"},
                {"week": 4, "task": "Draft and review proposal sections", "owner": "applicant", "priority": "high"},
                {"week": 5, "task": "Internal review and sign-off", "owner": "legal", "priority": "medium"},
                {"week": 6, "task": "Final submission", "owner": "applicant", "priority": "high"},
            ],
            "submission_checklist": [
                "Completed application form",
                "Budget justification sheet",
                "Impact metrics data",
                "Letters of support (minimum 2)",
                "Proof of incorporation / non-profit status",
                "CV / bios for all key personnel",
                "Signed cover letter",
            ],
        }

    return {"submission_roadmap": roadmap}


# ---------------------------------------------------------------------------
# PDF Ingestion Functions
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    text_parts = []
    pdf_reader = PdfReader(BytesIO(pdf_bytes))
    for page in pdf_reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


async def ingest_pdf_to_grant(pdf_bytes: bytes) -> GrantOpportunity:
    """
    Ingest a PDF grant document and extract structured data into a GrantOpportunity.
    Falls back to a demo stub if LLM is not configured or fails.
    """
    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_bytes)
        
        # Use LLM to parse structured data
        llm = _get_llm()
        prompt = PDF_INGESTION_PROMPT.format(document_text=pdf_text[:30000])  # Limit to first 30k chars to avoid token issues
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        # Parse JSON response
        parsed_data = _safe_parse_json(response.content)
        
        # Create GrantOpportunity from parsed data
        grant = GrantOpportunity(
            grant_id=parsed_data.get("grant_id", "unknown-grant"),
            title=parsed_data.get("title", "Unknown Grant Opportunity"),
            funder=parsed_data.get("funder", "Unknown Funder"),
            deadline=parsed_data.get("deadline", ""),
            amount=parsed_data.get("amount", ""),
            requirements=parsed_data.get("requirements", []),
            description=parsed_data.get("description", ""),
        )
        return grant
        
    except Exception as exc:
        logger.warning("PDF ingestion failed (%s) — using demo stub", exc)
        # Demo fallback
        return GrantOpportunity(
            grant_id="demo-ingested-grant",
            title="Demo Grant Opportunity (Ingested)",
            funder="Demo Funding Agency",
            deadline="2025-12-31",
            amount="$100,000 - $500,000",
            requirements=[
                "Non-profit or academic institution",
                "Project summary (2 pages)",
                "Budget justification",
            ],
            description="A demo grant opportunity generated as a fallback when PDF ingestion fails.",
        )
