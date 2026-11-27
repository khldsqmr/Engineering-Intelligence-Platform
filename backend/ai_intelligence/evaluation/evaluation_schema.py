"""Structured contracts for AI evaluation and governance."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvaluationScores(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    factualConsistency: int = Field(ge=0, le=100)
    evidenceGrounding: int = Field(ge=0, le=100)
    analyticalReasoning: int = Field(ge=0, le=100)
    counterEvidence: int = Field(ge=0, le=100)
    uncertaintyHandling: int = Field(ge=0, le=100)
    businessRelevance: int = Field(ge=0, le=100)


class JudgeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: EvaluationScores

    criticalErrors: list[str] = Field(max_length=3)

    explanation: str = Field(
        min_length=1,
        max_length=500,
    )


class EvaluationOutcome(BaseModel):
    evaluationVersion: str = "1.0.0"

    approvalStatus: Literal[
        "AUTO_APPROVED",
        "REGENERATE",
        "REJECTED",
        "EVALUATION_FAILED",
    ]

    evaluationScore: float | None = None

    deterministicValidationPassed: bool

    eligibleForHistoricalContext: bool = False

    evaluatorModel: str | None = None
    evaluatorPromptVersion: str | None = None
    evaluatorLatencySeconds: float | None = None

    judgeResult: JudgeOutput | None = None

    findings: list[str] = Field(default_factory=list)
