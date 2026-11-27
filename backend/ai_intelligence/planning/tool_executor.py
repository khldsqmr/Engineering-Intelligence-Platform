"""Execute validated analytical plans using authoritative context."""

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.numerical_grounding import format_grounded_value
from backend.ai_intelligence.planning.intent_planner import IntentPlan
from backend.analytics.factual_answers import (
    FACTUAL_ANSWER_VERSION,
    KEY_METRIC_IDS,
)
from backend.analytics.platform_knowledge import PLATFORM_KNOWLEDGE

TOOL_EXECUTOR_VERSION = "1.2.0"


def chat_answer(text: str) -> dict:
    return {
        "status": "CHAT_ANSWERED",
        "chatAnswer": text,
    }


def metric_answer(
    context: IntelligenceContext,
    metric_ids: set[str],
    scope: str,
    definitions_only: bool = False,
) -> dict:
    """Retrieve selected facts and definitions without inference."""

    facts = {(fact.metricId, fact.metricVersion): fact for fact in context.analyticalContext}

    evidence = []
    lines = []

    for semantic in context.semanticContext:
        if semantic.metricId not in metric_ids:
            continue

        fact = facts.get((semantic.metricId, semantic.metricVersion))

        if definitions_only:
            lines.append(
                f"{semantic.metricName}\n"
                f"{semantic.metricDescription}\n"
                f"Calculation: {semantic.calculationDefinition}\n"
                f"Interpretation: {semantic.interpretationGuidance}"
            )

        elif fact is None:
            lines.append(f"{semantic.metricName}: unavailable")
            continue

        else:

            def value(field, item=fact, unit=semantic.metricUnit):
                number = getattr(item, field)

                if number is None:
                    return "N/A"

                return format_grounded_value(
                    number,
                    field,
                    unit,
                )

            current = value("currentValue")
            previous = value("previousValue")
            benchmark = value("historicalBenchmarkAvg")

            if scope == "PREVIOUS":
                description = f"Previous period: {previous}"

            elif scope == "BENCHMARK":
                description = f"Historical benchmark: {benchmark}\nCurrent period: {current}"

                if fact.changeVsBenchmarkPct is not None:
                    description += (
                        f"\nRelative difference from benchmark: {value('changeVsBenchmarkPct')}"
                    )

                if fact.benchmarkPeriodCount:
                    description += f"\nBenchmark periods: {fact.benchmarkPeriodCount}"

            elif scope == "COMPARISON":
                description = (
                    f"Current: {current}\nPrevious: {previous}\nDirection: {fact.direction.lower()}"
                )

                if semantic.metricUnit == "PERCENT":
                    description += f"\nChange: {value('changeValue')}"
                else:
                    description += f"\nRelative change: {value('changePct')}"

            else:
                description = f"Current period: {current}"

            lines.append(f"{semantic.metricName}\n{description}")

        if fact is not None:
            evidence.append(
                {
                    **fact.model_dump(mode="json"),
                    "semanticContext": semantic.model_dump(mode="json"),
                }
            )

    if not lines:
        return chat_answer("No matching metrics are available in the selected analytical context.")

    return {
        "status": "FACT_ANSWERED",
        "factAnswer": "\n\n".join(lines),
        "factAnswerVersion": FACTUAL_ANSWER_VERSION,
        "evidence": evidence,
    }


def supported_investigation(
    context: IntelligenceContext,
    metric_ids: set[str],
) -> dict | None:
    """Reuse governed hypothesis patterns for Copilot."""

    from backend.ai_intelligence.reasoning.report_hypotheses import (
        build_supported_hypothesis,
    )

    for metric_id in sorted(metric_ids):
        hypothesis = build_supported_hypothesis(
            context,
            metric_id,
        )

        if hypothesis is None:
            continue

        facts = {fact.evidenceRef: fact for fact in context.analyticalContext}

        semantics = {
            (metric.metricId, metric.metricVersion): metric for metric in context.semanticContext
        }

        supporting = hypothesis.supportingEvidence
        counter = hypothesis.counterEvidence

        references = supporting + counter

        if any(
            ref.evidenceRef not in facts or facts[ref.evidenceRef].direction != ref.direction
            for ref in references
        ):
            continue

        if any(
            (
                facts[ref.evidenceRef].metricId,
                facts[ref.evidenceRef].metricVersion,
            )
            not in semantics
            for ref in references
        ):
            continue

        def describe(ref, facts=facts, semantics=semantics):
            fact = facts[ref.evidenceRef]

            semantic = semantics[(fact.metricId, fact.metricVersion)]

            return f"{semantic.metricName}: {fact.direction.lower()} ({fact.evidenceRef})"

        related_metrics = {facts[ref.evidenceRef].metricId for ref in references}

        result = metric_answer(
            context,
            metric_ids | related_metrics,
            "COMPARISON",
        )

        if result["status"] != "FACT_ANSWERED":
            continue

        sections = [
            "Evidence-backed hypothesis",
            hypothesis.text,
            "Supporting evidence:\n" + "\n".join(describe(ref) for ref in supporting),
        ]

        if counter:
            sections.append("Counter-evidence:\n" + "\n".join(describe(ref) for ref in counter))

        sections.extend(
            [
                "Metric comparisons",
                result["factAnswer"],
                "These observed relationships do not establish "
                "causation. The hypothesis is based on a governed "
                "analytical pattern, not an established root cause.",
            ]
        )

        result["factAnswer"] = "\n\n".join(sections)

        return result

    return None


def execute_plan(
    plan: IntentPlan,
    context: IntelligenceContext,
) -> dict | None:
    """Dispatch an allowed action. None delegates to AI investigation."""

    action = plan.action

    if action == "CONVERSATION":
        return chat_answer(
            "I'm here and ready to help with engineering analytics. What would you like to explore?"
        )

    if action == "CLARIFY":
        return chat_answer(
            "Could you clarify which engineering metric, "
            "reporting period or platform feature you mean?"
        )

    if action == "OUT_OF_SCOPE":
        return chat_answer(
            "That request is outside the information available "
            "to EIP. I can help with repository-level engineering "
            "metrics, pull requests, review performance, "
            "historical trends and platform functionality."
        )

    if action == "PLATFORM_KNOWLEDGE":
        topic = plan.platformTopic

        if topic == "workspaces":
            return chat_answer(
                "\n\n".join(
                    f"{name}: {description}"
                    for name, description in PLATFORM_KNOWLEDGE["workspaces"].items()
                )
            )

        if topic in PLATFORM_KNOWLEDGE["workspaces"]:
            return chat_answer(
                f"Open {topic} from the sidebar.\n\n" + PLATFORM_KNOWLEDGE["workspaces"][topic]
            )

        return chat_answer(PLATFORM_KNOWLEDGE[topic])

    if action == "DATA_QUALITY":
        quality = context.qualityContext

        lines = [
            f"Source coverage: {quality.sourceCoverage}",
            f"Data refreshed at: {quality.dataRefreshedAt}",
        ]

        if quality.limitations:
            lines.append("Limitations:\n" + "\n".join(quality.limitations))

        lines.append(
            "Visit Data Quality for detailed coverage and analytical readiness information."
        )

        return chat_answer("\n\n".join(lines))

    if action == "METRIC_SCREEN":
        from backend.ai_intelligence.planning.metric_queries import (
            select_metrics,
        )

        selected = select_metrics(
            context,
            metric_ids=set(plan.metricIds),
            movement=plan.movement,
            rank_by_change=plan.rankByChange,
            limit=plan.limit,
        )

        if not selected:
            return chat_answer(
                "No available metric comparisons match the requested analytical criteria."
            )

        positions = {metric_id: index for index, metric_id in enumerate(selected)}

        ordered_context = context.model_copy(
            update={
                "semanticContext": sorted(
                    [metric for metric in context.semanticContext if metric.metricId in positions],
                    key=lambda metric: positions[metric.metricId],
                )
            }
        )

        result = metric_answer(
            ordered_context,
            set(selected),
            "COMPARISON",
        )

        if result.get("factAnswer"):
            result["factAnswer"] = (
                f"Metric selection: {plan.movement.lower()}\n"
                f"Matching results: {len(selected)}\n\n" + result["factAnswer"]
            )

        return result

    if action == "METRIC_OVERVIEW":
        return metric_answer(
            context,
            KEY_METRIC_IDS,
            "COMPARISON",
        )

    if action == "METRIC_DEFINITION":
        return metric_answer(
            context,
            set(plan.metricIds),
            plan.valueScope,
            definitions_only=True,
        )

    if action == "METRIC_FACTS":
        return metric_answer(
            context,
            set(plan.metricIds),
            plan.valueScope,
        )

    if action == "INVESTIGATE":
        if plan.valueScope in {"PREVIOUS", "BENCHMARK"}:
            return chat_answer(
                "Please select the reporting period you want "
                "to investigate using the reporting period filter."
            )

        size_metrics = {
            "medianMergeHours",
            "medianLinesChanged",
            "medianFilesChanged",
        }

        if set(plan.metricIds) == size_metrics:
            result = metric_answer(
                context,
                size_metrics,
                "COMPARISON",
            )

            if result["status"] == "FACT_ANSWERED":
                result["factAnswer"] += (
                    "\n\nPR size assessment\n"
                    "These size metrics describe merged PRs, "
                    "not all submitted PRs. Lines and files "
                    "changed are size proxies, not direct "
                    "measurements of complexity. "
                    "Aggregate comparisons cannot establish "
                    "whether PR size caused a change in "
                    "merge duration."
                )

            return result

        supported = supported_investigation(
            context,
            set(plan.metricIds),
        )

        if supported is not None:
            return supported

        # Existing governed AI reasoning workflow.
        return None

    raise ValueError("Unsupported execution action.")
