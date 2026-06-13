from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


@dataclass
class ApplicantProfile:
    """Profile of the grant applicant."""

    name: str = ""
    organization_type: str = ""  # "researcher", "startup", "ngo"
    domain: str = ""  # "biotech", "cleantech", "ai", etc.
    team_size: int = 0
    previous_grants: list[str] = field(default_factory=list)
    project_description: str = ""
    budget_requested: float = 0.0


@dataclass
class GrantOpportunity:
    """A single grant opportunity."""

    grant_id: str = ""
    title: str = ""
    funder: str = ""
    deadline: str = ""
    amount: str = ""
    requirements: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class GrantFlowState:
    messages: Annotated[list[AnyMessage], add_messages] = field(default_factory=list)
    applicant: ApplicantProfile = field(default_factory=ApplicantProfile)
    available_grants: list[GrantOpportunity] = field(
        default_factory=list
    )  # input: list of grants to evaluate
    matched_opportunities: list[dict] = field(
        default_factory=list
    )  # from OpportunityDiscoveryAgent: [{grant_id, match_score, rationale}]
    eligibility_results: list[dict] = field(
        default_factory=list
    )  # from EligibilityAgent: [{grant_id, eligible, reasons}]
    gap_analysis: list[dict] = field(
        default_factory=list
    )  # from GapAnalysisAgent: [{grant_id, missing_items}]
    proposal_drafts: list[dict] = field(
        default_factory=list
    )  # from ProposalDraftingAgent
    submission_roadmap: dict = field(
        default_factory=dict
    )  # from SubmissionRoadmapAgent
    error: str | None = None
