"""Compact inference contract and application response adapter."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

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


class CompactReportOutput(BaseModel):
    """AI selects observations rather than writing numerical prose."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ANSWERED", "INSUFFICIENT_EVIDENCE"]

    observationRefs: list[EvidenceCode] = Field(max_length=1)

    hypothesis: str | None = Field(max_length=200)
    hypothesisRefs: list[EvidenceCode] = Field(max_length=4)
    counterRefs: list[EvidenceCode] = Field(max_length=3)

    alternative: str | None = Field(max_length=200)
    investigation: str | None = Field(max_length=200)


def build_grounded_response_schema(facts, *, report_only=False):
    """Constrain model references to authoritative evidence codes."""

    symbols = {
        "INCREASED": "+",
        "DECREASED": "-",
        "UNCHANGED": "=",
    }

    codes = sorted(
        {
            f"{fact.evidenceRef}:{symbols[fact.direction]}"
            for fact in facts
            if fact.direction in symbols
            and fact.currentValue is not None
            and fact.previousValue is not None
        }
    )

    allowed_code = Literal[tuple(codes)] if codes else str

    return create_model(
        "GroundedCompactNarrativeOutput",
        __base__=CompactReportOutput if report_only else CompactNarrativeOutput,
        observationRefs=(
            list[allowed_code],
            Field(max_length=(1 if report_only else 4) if codes else 0),
        ),
        hypothesisRefs=(
            list[allowed_code],
            Field(max_length=4 if codes else 0),
        ),
        counterRefs=(
            list[allowed_code],
            Field(max_length=3 if codes else 0),
        ),
    )


def expand_report_output(compact, context):
    """Render the selected observation from authoritative evidence."""

    payload = compact.model_dump()
    observation = None

    if compact.status == "ANSWERED":
        if len(compact.observationRefs) != 1:
            raise ValueError("Select exactly one observation.")

        code = compact.observationRefs[0]
        evidence_ref = code.split(":")[0]

        facts = {fact.evidenceRef: fact for fact in context.analyticalContext}

        semantics = {metric.metricId: metric for metric in context.semanticContext}

        fact = facts.get(evidence_ref)

        if fact is None or fact.currentValue is None or fact.previousValue is None:
            raise ValueError("Selected observation is unavailable.")

        symbols = {
            "INCREASED": "+",
            "DECREASED": "-",
            "UNCHANGED": "=",
        }

        if code != f"{evidence_ref}:{symbols.get(fact.direction)}":
            raise ValueError("Invalid observation direction.")

        name = semantics[fact.metricId].metricName

        current = "{{" + evidence_ref + ".currentValue}}"
        previous = "{{" + evidence_ref + ".previousValue}}"

        if fact.direction == "UNCHANGED":
            observation = f"{name} remained unchanged at {current}."
        else:
            observation = f"{name} {fact.direction.lower()} from {previous} to {current}"

            if fact.changePct is not None:
                change = "{{" + evidence_ref + ".changePct}}"
                observation += f" (relative change: {change})"

            observation += "."

    else:
        if compact.observationRefs or compact.investigation is not None:
            raise ValueError("Invalid abstention response.")

    payload["observation"] = observation

    return expand_output(CompactNarrativeOutput.model_validate(payload))
