from __future__ import annotations

OPPORTUNITY_DISCOVERY_PROMPT = """You are an expert grant matching specialist.

Given an applicant profile and a list of available grant opportunities, score each grant
on a scale of 0–100 based on how well it matches the applicant's profile.

Consider:
- Domain and sector alignment
- Organization type eligibility (researcher / startup / NGO)
- Budget range compatibility
- Project description fit with grant objectives
- Team size and experience level

Applicant Profile:
{applicant_profile}

Available Grants:
{available_grants}

Return a ranked JSON list of objects with the fields:
  grant_id, match_score (0-100), rationale (2–3 sentences explaining the score)

Order by match_score descending. Include ALL grants in the response.
"""

ELIGIBILITY_PROMPT = """You are a grant eligibility analyst.

For each grant in the matched list, determine whether the applicant meets the stated
eligibility criteria. Flag any hard disqualifiers that would prevent the applicant from
applying.

Applicant Profile:
{applicant_profile}

Matched Grants (with requirements):
{matched_grants_with_requirements}

For each grant return a JSON object with:
  grant_id, eligible (true/false), reasons (list of strings), disqualifiers (list of strings)

Be precise. If a requirement is ambiguous, note it in reasons rather than disqualifying.
"""

GAP_ANALYSIS_PROMPT = """You are a grant preparation consultant.

For each eligible grant, identify exactly what the applicant is missing in order to
submit a strong application. Be specific — name concrete documents, data points, or
activities that need to be completed.

Applicant Profile:
{applicant_profile}

Eligible Grants (with full requirements):
{eligible_grants}

For each grant return a JSON object with:
  grant_id,
  missing_items (list of specific strings, e.g. "Audited financial statements for FY2024"),
  completeness_score (0-100, where 100 means fully ready to submit)

Rank missing_items by importance (most critical first).
"""

PROPOSAL_DRAFTING_PROMPT = """You are an expert grant writer with a track record of successful proposals.

Draft two key sections of a grant proposal for the best-matched grant opportunity.
Write in a professional, compelling, and concise style appropriate for scientific or
government funding bodies.

Applicant Profile:
{applicant_profile}

Target Grant:
{target_grant}

Gap Analysis (for context on what to emphasize):
{gap_analysis}

Produce:
1. Executive Summary (250–350 words): Describe the project, its significance, and the
   expected impact. Make a clear case for why this applicant is the right team.
2. Project Narrative (400–500 words): Describe the technical approach, methodology,
   timeline at a high level, and how the work advances the funder's stated objectives.

Return as JSON with keys: executive_summary, project_narrative
"""

SUBMISSION_ROADMAP_PROMPT = """You are a grant submission strategist.

Create a detailed, realistic submission timeline working back from the grant deadline.
Account for the identified gaps that need to be resolved before submission.

Applicant Profile:
{applicant_profile}

Target Grant:
  Title: {grant_title}
  Funder: {grant_funder}
  Deadline: {grant_deadline}
  Amount: {grant_amount}

Outstanding Gaps to Resolve:
{missing_items}

Produce a week-by-week milestone plan covering the period from today to the deadline.
For each milestone specify:
  - week (integer, 1 = this week)
  - task (clear action item)
  - owner (applicant / finance team / legal / external)
  - priority (high / medium / low)

Also include a final "submission checklist" — a flat list of all items that must be
confirmed complete on submission day.

Return as JSON with keys:
  milestones: list of {week, task, owner, priority}
  submission_checklist: list of strings
"""

PDF_INGESTION_PROMPT = """You are a grant opportunity specialist that extracts structured information from grant solicitations/RFPs.

Given the full text of a grant opportunity document, extract the following fields as JSON:
  - grant_id: A unique identifier (e.g., "DOE-2025-001" or similar, use document title/info if no explicit ID)
  - title: Full grant opportunity title
  - funder: Funding agency/organization name
  - deadline: Submission deadline (YYYY-MM-DD format if possible, otherwise raw text)
  - amount: Funding amount/award range (e.g., "$500,000 - $2,000,000")
  - requirements: List of eligibility and submission requirements (bullet points or numbered list items as strings)
  - description: A concise 3-5 sentence summary of the grant opportunity

Return ONLY valid JSON, no markdown or additional text.

Document text:
{document_text}
"""
