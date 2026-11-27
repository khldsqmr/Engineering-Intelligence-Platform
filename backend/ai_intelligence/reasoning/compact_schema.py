"""Compact inference contract and application response adapter."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.ai_intelligence.reasoning.reasoning_schema import (
    AnalyticalClaim,
    EvidenceReference,
    NarrativeOutput,
    RootCauseHypothesis,
)

EvidenceCode = Annotated[
    str,
    Field(pattern=r"^E[0-9]{2,}:[+=-]$"),
]

DIRECTIONS = {
    "+": "INCREASED",
    "-": "DECREASED",
    "=": "UNCHANGED",
}


class CompactNarrativeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ANSWERED", "INSUFFICIENT_EVIDENCE"]

    observation: str | None = Field(max_length=300)
    observationRefs: list[EvidenceCode] = Field(max_length=4)

    hypothesis: str | None = Field(max_length=200)
    hypothesisRefs: list[EvidenceCode] = Field(max_length=4)
    counterRefs: list[EvidenceCode] = Field(max_length=3)

    alternative: str | None = Field(max_length=200)
    investigation: str | None = Field(max_length=200)


def expand_references(
    codes: list[str],
) -> list[EvidenceReference]:

    references = []

    for code in codes:
        evidence_ref, direction = code.split(":")

        references.append(
            EvidenceReference(
                evidenceRef=evidence_ref,
                direction=DIRECTIONS[direction],
            )
        )

    return references


def expand_output(
    compact: CompactNarrativeOutput,
) -> NarrativeOutput:
    """Convert compact model output into the application contract."""

    if compact.observation is None and compact.observationRefs:
        raise ValueError("Observation evidence without observation.")

    if compact.hypothesis is None and (compact.hypothesisRefs or compact.counterRefs):
        raise ValueError("Hypothesis evidence without hypothesis.")

    narrative = None
    hypothesis = None

    if compact.observation is not None:
        narrative = AnalyticalClaim(
            text=compact.observation,
            supportingEvidence=expand_references(compact.observationRefs),
        )

    if compact.hypothesis is not None:
        hypothesis = RootCauseHypothesis(
            text=compact.hypothesis,
            supportingEvidence=expand_references(compact.hypothesisRefs),
            counterEvidence=expand_references(compact.counterRefs),
        )

    return NarrativeOutput(
        status=compact.status,
        narrative=narrative,
        hypothesis=hypothesis,
        alternativeExplanations=([compact.alternative] if compact.alternative is not None else []),
        recommendedInvestigation=compact.investigation,
    )
