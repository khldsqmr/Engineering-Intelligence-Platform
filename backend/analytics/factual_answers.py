"""Answer supported factual questions from governed analytical context."""

import re

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.numerical_grounding import (
    format_grounded_value,
)

FACTUAL_ANSWER_VERSION = "1.0.0"

QUESTION_PATTERNS = (
    (
        "comparison",
        r"what is the (?:current )?(.+?) and how has it changed "
        r"compared to the previous week",
    ),
    (
        "comparison",
        r"how did (?:the )?(.+?) change this week",
    ),
    (
        "benchmark",
        r"what is the historical benchmark for (?:the )?(.+)",
    ),
    (
        "current",
        r"what is the (?:current )?(.+)",
    ),
)

METRIC_ALIASES = {
    "medianMergeHours": {"median merge duration", "median merge time"},
    "p90MergeHours": {"p90 merge duration", "p90 merge time"},
    "prsOpened": {"prs opened", "pull requests opened"},
    "prsMerged": {"prs merged", "merged prs", "merged pull requests"},
    "prsClosed": {"prs closed", "closed prs"},
    "prsClosedWithoutMerge": {"prs closed without merge"},
    "mergedPRReviewCoveragePct": {
        "external review coverage",
        "review coverage",
    },
    "medianFirstReviewHours": {"median time to first review"},
    "meanPreReviewHours": {
        "mean pre-review duration",
        "pre-review duration",
        "pre-review time",
    },
    "meanPostReviewHours": {
        "mean post-review duration",
        "post-review duration",
        "post-review time",
    },
}


def normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def answer_factual_question(
    context: IntelligenceContext,
) -> dict | None:
    """Return a deterministic answer for explicitly supported questions."""

    if context.userIntent.mode != "question":
        return None

    question = normalize(context.userIntent.question or "")
    question = question.removesuffix("?").strip()

    operation = None
    metric_name = None

    for candidate, pattern in QUESTION_PATTERNS:
        match = re.fullmatch(pattern, question)

        if match:
            operation = candidate
            metric_name = match.group(1)
            break

    if operation is None:
        return None

    matches = [
        semantic
        for semantic in context.semanticContext
        if metric_name
        in {
            normalize(semantic.metricName),
            *METRIC_ALIASES.get(semantic.metricId, set()),
        }
    ]

    # Never guess an ambiguous or unknown metric.
    if len(matches) != 1:
        return None

    semantic = matches[0]

    fact = next(
        (
            item
            for item in context.analyticalContext
            if item.metricId == semantic.metricId and item.metricVersion == semantic.metricVersion
        ),
        None,
    )

    if fact is None:
        return None

    def render(field):
        value = getattr(fact, field)

        if value is None:
            return "N/A"

        return format_grounded_value(
            value,
            field,
            semantic.metricUnit,
        )

    current = render("currentValue")

    if operation == "benchmark":
        benchmark = render("historicalBenchmarkAvg")

        if fact.historicalBenchmarkAvg is None:
            text = f"The historical benchmark for {semantic.metricName} is unavailable."
        else:
            text = (
                f"The historical benchmark for "
                f"{semantic.metricName} is {benchmark}. "
                f"The current reporting-period value is {current}."
            )

    elif operation == "comparison":
        previous = render("previousValue")

        text = (
            f"{semantic.metricName} is {current} "
            f"in the current reporting period, compared "
            f"with {previous} in the previous period."
        )

        if semantic.metricUnit == "PERCENT":
            change = render("changeValue")

            if fact.changeValue is not None:
                text += f" The change was {change}."

        elif fact.changePct is not None:
            change = render("changePct")
            text += f" The relative change was {change}."

        else:
            text += " Relative change is unavailable."

    else:
        text = f"The current value of {semantic.metricName} is {current}."

    return {
        "factAnswer": text,
        "factAnswerVersion": FACTUAL_ANSWER_VERSION,
        "evidence": [
            {
                **fact.model_dump(mode="json"),
                "semanticContext": semantic.model_dump(mode="json"),
            },
        ],
    }


def build_factual_fallback(
    context: IntelligenceContext,
) -> dict | None:
    """Retrieve explicitly mentioned metrics without using rejected AI output."""

    if context.userIntent.mode != "question":
        return None

    question = normalize(context.userIntent.question or "")
    evidence = []

    for semantic in context.semanticContext:
        names = {
            normalize(semantic.metricName),
            *METRIC_ALIASES.get(semantic.metricId, set()),
        }

        matched = any(
            re.search(
                r"(?<!\w)" + re.escape(name) + r"(?!\w)",
                question,
            )
            for name in names
        )

        if not matched:
            continue

        fact = next(
            (
                item
                for item in context.analyticalContext
                if item.metricId == semantic.metricId
                and item.metricVersion == semantic.metricVersion
            ),
            None,
        )

        if fact is None or fact.currentValue is None:
            continue

        evidence.append(
            {
                **fact.model_dump(mode="json"),
                "semanticContext": semantic.model_dump(mode="json"),
            }
        )

    if not evidence:
        return None

    return {
        "factFallback": (
            "The AI interpretation could not be validated. "
            "Available facts for the selected reporting period "
            "are shown below."
        ),
        "evidence": evidence[:4],
    }


KEY_METRIC_IDS = {
    "prsOpened",
    "prsMerged",
    "prsClosedWithoutMerge",
    "medianMergeHours",
    "p90MergeHours",
    "medianFirstReviewHours",
    "meanPreReviewHours",
    "mergedPRReviewCoveragePct",
}


def answer_metric_overview(
    context: IntelligenceContext,
    question: str,
) -> dict | None:
    """Retrieve a governed inventory of engineering metrics."""

    text = normalize(question).rstrip(".!?").strip()

    catalog_request = text in {
        "what metrics do you track",
        "what metrics are available",
        "what metrics are tracked",
        "what are all the metrics",
        "list all metrics",
        "show me all metrics",
    }

    overview_request = re.fullmatch(
        r"(?:can you |could you |please )?"
        r"(?:(?:tell|show) me (?:about )?|list |what are |give me )?"
        r"(?:the )?"
        r"(?:(?:major|key|main|core|important|top) )?"
        r"(?:engineering |performance )?"
        r"(?:metrics|kpis)"
        r"(?: (?:for|in) (?:this|the current) "
        r"(?:week|period|reporting period))?",
        text,
    )

    if not catalog_request and not overview_request:
        return None

    facts = {(fact.metricId, fact.metricVersion): fact for fact in context.analyticalContext}

    evidence = []
    lines = []

    for semantic in context.semanticContext:
        if not catalog_request and semantic.metricId not in KEY_METRIC_IDS:
            continue

        fact = facts.get((semantic.metricId, semantic.metricVersion))

        if fact is None:
            continue

        current = (
            format_grounded_value(
                fact.currentValue,
                "currentValue",
                semantic.metricUnit,
            )
            if fact.currentValue is not None
            else "N/A"
        )

        previous = (
            format_grounded_value(
                fact.previousValue,
                "previousValue",
                semantic.metricUnit,
            )
            if fact.previousValue is not None
            else "N/A"
        )

        lines.append(f"{semantic.metricName}: {current} (previous: {previous})")

        evidence.append(
            {
                **fact.model_dump(mode="json"),
                "semanticContext": semantic.model_dump(mode="json"),
            }
        )

    if lines:
        answer = (
            "Here are the engineering metrics for the selected "
            "reporting period:\n\n"
            + "\n".join(lines)
            + "\n\nYou can explore their definitions and "
            "calculations in Metric Catalog."
        )
    else:
        answer = "No matching analytical metrics are available for the selected reporting period."

    return {
        "factAnswer": answer,
        "factAnswerVersion": FACTUAL_ANSWER_VERSION,
        "evidence": evidence,
    }
