from typing import Literal

from pydantic import BaseModel, Field


class TemporalContext(BaseModel):
    periodStart: str
    periodEndExclusive: str
    previousPeriodStart: str
    previousPeriodEndExclusive: str
    timezone: str


class SemanticContext(BaseModel):
    metricId: str
    metricVersion: str
    metricName: str
    metricCategory: str
    metricDescription: str
    metricUnit: str

    # Calculation semantics
    calculationDefinition: str
    analyticalCohort: str
    aggregationType: str
    periodEventAttribute: str

    # Source lineage and dependencies
    sourceDependencies: str
    requiresDetailEnrichment: bool
    requiresReviewEnrichment: bool

    # Analytical interpretation
    performanceDirection: str
    supportsHistoricalBenchmark: bool
    interpretationGuidance: str


class AnalyticalContext(BaseModel):
    evidenceRef: str
    evidenceId: str

    metricId: str
    metricVersion: str

    currentValue: float | None
    previousValue: float | None
    changeValue: float | None
    changePct: float | None

    direction: Literal[
        "INCREASED",
        "DECREASED",
        "UNCHANGED",
        "UNAVAILABLE",
    ]

    historicalBenchmarkAvg: float | None = None
    historicalBenchmarkStd: float | None = None
    changeVsBenchmarkPct: float | None = None
    benchmarkPeriodCount: int = 0

    eligiblePRCount: int | None = None
    enrichedPRCount: int | None = None
    sampleSize: int | None = None
    enrichmentCoveragePct: float | None = None
    coverageStatus: str

    previousSampleSize: int | None = None
    previousEnrichmentCoveragePct: float | None = None
    previousCoverageStatus: str | None = None


class RelationalContext(BaseModel):
    relationshipId: str
    relationshipType: str
    metricIds: list[str]
    interpretation: str


class QualityContext(BaseModel):
    sourceCoverage: str
    dataRefreshedAt: str
    availableHistory: dict[str, str | None]

    limitations: list[str] = Field(default_factory=list)


class UserIntentContext(BaseModel):
    mode: Literal["narrative", "question"] = "narrative"
    question: str | None = Field(
        default=None,
        max_length=500,
    )


class HistoricalIntelligenceContext(BaseModel):
    intelligenceId: str
    periodStart: str
    periodEndExclusive: str

    narrative: str
    metricVersions: dict[str, str]

    evaluationScore: float = Field(ge=0, le=100)
    evaluationVersion: str


class IntelligenceContext(BaseModel):
    contextVersion: str = "1.0.0"

    repository: str
    repositoryId: int
    ingestionRunId: str

    temporalContext: TemporalContext
    semanticContext: list[SemanticContext]
    analyticalContext: list[AnalyticalContext]
    relationalContext: list[RelationalContext]
    qualityContext: QualityContext
    userIntent: UserIntentContext

    historicalContext: list[HistoricalIntelligenceContext] = Field(default_factory=list)
