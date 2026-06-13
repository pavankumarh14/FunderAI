from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    eligibility_node,
    gap_analysis_node,
    opportunity_discovery_node,
    proposal_drafting_node,
    submission_roadmap_node,
)
from app.agents.state import GrantFlowState

# ---------------------------------------------------------------------------
# Build the LangGraph multi-agent pipeline
# ---------------------------------------------------------------------------

builder = StateGraph(GrantFlowState)

# Register nodes
builder.add_node("opportunity_discovery", opportunity_discovery_node)
builder.add_node("eligibility", eligibility_node)
builder.add_node("gap_analysis", gap_analysis_node)
builder.add_node("proposal_drafting", proposal_drafting_node)
builder.add_node("submission_roadmap", submission_roadmap_node)

# Sequential pipeline:
# START -> opportunity_discovery -> eligibility -> gap_analysis
#       -> proposal_drafting -> submission_roadmap -> END
builder.add_edge(START, "opportunity_discovery")
builder.add_edge("opportunity_discovery", "eligibility")
builder.add_edge("eligibility", "gap_analysis")
builder.add_edge("gap_analysis", "proposal_drafting")
builder.add_edge("proposal_drafting", "submission_roadmap")
builder.add_edge("submission_roadmap", END)

# Compile the graph
graph = builder.compile(name="grantflow")
