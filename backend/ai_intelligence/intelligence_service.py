"""Production orchestration of governed engineering intelligence."""

from dataclasses import dataclass
from pathlib import Path

from backend.ai_intelligence.caching.intelligence_cache import (
    find_cached_intelligence,
)
from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.history.history_retrieval import (
    enrich_with_historical_context,
)
from backend.ai_intelligence.history.history_store import (
    get_intelligence_record,
    save_intelligence,
)
from backend.ai_intelligence.providers.ollama import (
    OllamaProvider,
)
from backend.ai_intelligence.reasoning.intelligence_workflow import (
    run_intelligence,
)


@dataclass(frozen=True)
class IntelligenceServiceResult:
    record: dict
    cacheHit: bool


def retrieve_intelligence(
    context: IntelligenceContext,
    database_path: str | Path,
    *,
    generator_model: str,
    evaluator_model: str,
) -> IntelligenceServiceResult | None:
    """Retrieve compatible intelligence without invoking an LLM."""

    enriched_context = enrich_with_historical_context(
        context,
        database_path,
    )

    record = find_cached_intelligence(
        enriched_context,
        database_path,
        generator_model=generator_model,
        evaluator_model=evaluator_model,
    )

    if record is None:
        return None

    return IntelligenceServiceResult(
        record=record,
        cacheHit=True,
    )


def execute_intelligence(
    context: IntelligenceContext,
    database_path: str | Path,
    generator: OllamaProvider,
    evaluator: OllamaProvider,
    *,
    force_refresh: bool = False,
) -> IntelligenceServiceResult:
    """Reuse or generate and persist governed intelligence."""

    # 01. Attach compatible historical observations.
    enriched_context = enrich_with_historical_context(
        context,
        database_path,
    )

    # 02. Check persistent intelligence cache.
    if not force_refresh:
        cached = find_cached_intelligence(
            enriched_context,
            database_path,
            generator_model=generator.model,
            evaluator_model=evaluator.model,
        )

        if cached is not None:
            return IntelligenceServiceResult(
                record=cached,
                cacheHit=True,
            )

    # 03. Execute bounded intelligence generation.

    max_attempts = 2 if enriched_context.userIntent.mode == "narrative" else 1

    retry_feedback: tuple[str, ...] = ()

    for attempt in range(max_attempts):
        result = run_intelligence(
            enriched_context,
            generator,
            evaluator,
            **({"retry_feedback": retry_feedback} if retry_feedback else {}),
        )

        # Persist every execution, including failed attempts.
        intelligence_id = save_intelligence(
            result,
            database_path,
            generator_model=generator.model,
        )

        record = get_intelligence_record(
            intelligence_id,
            database_path,
        )

        if record is None:
            raise RuntimeError("Persisted intelligence record could not be retrieved.")

        retryable = result.evaluation.approvalStatus == "REGENERATE" or (
            result.evaluation.approvalStatus == "REJECTED"
            and result.draft is not None
            and not result.draft.validationPassed
        )

        if retryable and attempt + 1 < max_attempts:
            retry_feedback = (
                "The previous draft failed governance checks.",
                "Use numerical placeholders instead of literal numbers.",
                "Never use the same evidence reference as both supporting and counter-evidence.",
                "Respect metric definitions, aggregation and direction.",
                "Treat historical observations as prior-period context.",
                "Do not repeat the observation as a hypothesis.",
                "Use a null hypothesis when no defensible explanation is supported.",
                "Keep all claims concise and complete.",
            )
            continue

        return IntelligenceServiceResult(
            record=record,
            cacheHit=False,
        )

    raise RuntimeError("Intelligence workflow did not return a result.")
