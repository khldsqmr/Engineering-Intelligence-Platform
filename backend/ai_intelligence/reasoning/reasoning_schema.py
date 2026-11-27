"""Structured output contracts for AI-generated intelligence."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StructuredOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceReference(StructuredOutput):
    evidenceRef: str = Field(pattern=r"^E[0-9]{2,}$")

    direction: Literal[
        "INCREASED",
        "DECREASED",
        "UNCHANGED",
    ]


class AnalyticalClaim(StructuredOutput):
    text: str = Field(min_length=1, max_length=1000)

    supportingEvidence: list[EvidenceReference] = Field(
        min_length=1,
        max_length=4,
    )


class RootCauseHypothesis(AnalyticalClaim):
    counterEvidence: list[EvidenceReference] = Field(
        max_length=3,
    )


class NarrativeOutput(StructuredOutput):
    status: Literal[
        "ANSWERED",
        "INSUFFICIENT_EVIDENCE",
    ]

    narrative: AnalyticalClaim | None
    hypothesis: RootCauseHypothesis | None

    alternativeExplanations: list[str] = Field(
        max_length=2,
    )

    recommendedInvestigation: str | None

    @model_validator(mode="after")
    def validate_response_status(self):
        if self.status == "ANSWERED":
            if self.narrative is None:
                raise ValueError("An answered response requires a narrative.")

        else:
            if self.narrative is not None or self.hypothesis is not None:
                raise ValueError("Insufficient evidence cannot produce analytical claims.")

            if self.alternativeExplanations:
                raise ValueError("Insufficient evidence cannot produce alternative claims.")

        return self


class ReportOutput(NarrativeOutput):
    """Proactive report when comparable analytical facts are available."""

    status: Literal["ANSWERED"]
    narrative: AnalyticalClaim
