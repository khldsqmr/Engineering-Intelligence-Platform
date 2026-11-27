"""Deterministic validation of AI-generated analytical claims."""

import re

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    NarrativeOutput,
)


def validate_evidence(
    output: NarrativeOutput,
    facts: list[AnalyticalContext],
    *,
    check_numerical_text: bool = True,
) -> list[str]:
    """Return grounding violations without modifying model output."""

    errors = []

    evidence_index = {fact.evidenceRef: fact for fact in facts}

    claims = []

    if output.narrative is not None:
        claims.append(("narrative", output.narrative))

    if output.hypothesis is not None:
        claims.append(("hypothesis", output.hypothesis))

    for claim_name, claim in claims:
        references = list(claim.supportingEvidence)

        if claim_name == "hypothesis":
            references.extend(claim.counterEvidence)

        seen = set()

        for reference in references:
            evidence_ref = reference.evidenceRef

            if evidence_ref in seen:
                errors.append(f"{claim_name}: duplicate evidence {evidence_ref}")

            seen.add(evidence_ref)

            fact = evidence_index.get(evidence_ref)

            if fact is None:
                errors.append(f"{claim_name}: unknown evidence {evidence_ref}")
                continue

            if fact.direction == "UNAVAILABLE":
                errors.append(f"{claim_name}: unavailable evidence {evidence_ref}")
                continue

            if reference.direction != fact.direction:
                errors.append(
                    f"{evidence_ref}: expected {fact.direction}, received {reference.direction}"
                )

    prose = [(claim_name, claim.text) for claim_name, claim in claims]

    prose.extend(
        ("alternativeExplanation", explanation) for explanation in output.alternativeExplanations
    )

    if output.recommendedInvestigation:
        prose.append(
            (
                "recommendedInvestigation",
                output.recommendedInvestigation,
            )
        )

    for field_name, text in prose:
        if not text.strip():
            errors.append(f"{field_name}: empty text")

        if check_numerical_text and re.search(r"\d", text):
            errors.append(f"{field_name}: unexpected numerical text")

    return errors
