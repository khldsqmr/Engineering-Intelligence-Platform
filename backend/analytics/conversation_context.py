"""Resolve bounded conversational follow-ups using governed context."""

from backend.ai_intelligence.context.context_schema import IntelligenceContext
from backend.ai_intelligence.numerical_grounding import format_grounded_value
from backend.analytics.factual_answers import (
    FACTUAL_ANSWER_VERSION,
    answer_factual_question,
)
from backend.analytics.intent_router import answer_conversational_message
from backend.analytics.platform_knowledge import PLATFORM_KNOWLEDGE

CONVERSATION_CONTEXT_VERSION = "1.0.0"


def normalize(text: str) -> str:
    return " ".join(text.casefold().split()).rstrip(".!?")


def chat_response(text: str) -> dict:
    return {
        "status": "CHAT_ANSWERED",
        "chatAnswer": text,
        "conversationContextVersion": CONVERSATION_CONTEXT_VERSION,
    }


def answer_followup(
    context: IntelligenceContext,
    question: str,
    previous_questions: list[str],
) -> dict | None:
    """Resolve supported follow-ups without trusting earlier AI answers."""

    text = normalize(question)

    intents = {
        "next": {
            "what do i do next",
            "what should i do next",
            "where should i start",
            "what next",
            "what should i explore next",
        },
        "previous": {
            "what about the previous week",
            "what about last week",
            "and last week",
            "what was it last week",
            "what was the previous value",
        },
        "benchmark": {
            "how does that compare with the historical benchmark",
            "what about the historical benchmark",
            "what is the benchmark",
            "how does that compare historically",
        },
        "definition": {
            "how is that calculated",
            "how is it calculated",
            "how is that metric calculated",
            "what does that metric mean",
        },
    }

    intent = next(
        (key for key, phrases in intents.items() if text in phrases),
        None,
    )

    if intent is None:
        return None

    for previous in reversed(previous_questions[-3:]):
        reference = answer_conversational_message(previous)

        platform_topic = reference and (
            reference == PLATFORM_KNOWLEDGE["overview"]
            or reference == PLATFORM_KNOWLEDGE["copilot"]
            or reference.startswith("I can retrieve engineering metrics")
            or reference in PLATFORM_KNOWLEDGE["workspaces"].values()
        )

        if platform_topic:
            if intent == "next":
                return chat_response(
                    "Start with Executive Overview to understand "
                    "weekly engineering performance. Then explore "
                    "Engineering Lifecycle for merge duration and "
                    "review engagement. Visit Data Quality to check "
                    "data reliability, and AI Insights for potential "
                    "explanations and recommended investigations."
                )

            break

        prior_context = context.model_copy(
            update={
                "userIntent": context.userIntent.model_copy(update={"question": previous}),
            }
        )

        prior = answer_factual_question(prior_context)

        if not prior or len(prior["evidence"]) != 1:
            continue

        evidence = prior["evidence"][0]
        semantic = evidence["semanticContext"]
        name = semantic["metricName"]
        unit = semantic["metricUnit"]

        if intent == "previous":
            value = evidence["previousValue"]

            answer = (
                f"The previous reporting-period value of {name} "
                f"was {format_grounded_value(value, 'previousValue', unit)}."
                if value is not None
                else f"The previous value of {name} is unavailable."
            )

        elif intent == "benchmark":
            benchmark_context = context.model_copy(
                update={
                    "userIntent": context.userIntent.model_copy(
                        update={"question": (f"What is the historical benchmark for {name}?")}
                    )
                }
            )

            result = answer_factual_question(benchmark_context)

            if result:
                return {
                    **result,
                    "status": "FACT_ANSWERED",
                    "conversationContextVersion": (CONVERSATION_CONTEXT_VERSION),
                }

            break

        elif intent == "definition":
            answer = (
                f"{name}: {semantic['metricDescription']}. "
                f"Calculation: {semantic['calculationDefinition']}. "
                f"{semantic['interpretationGuidance']}."
            )

        else:
            return chat_response(
                f"Explore {name} in the analytics workspaces to "
                "compare reporting periods. Open Metric Catalog "
                "for its calculation methodology, and Data Quality "
                "to understand evidence coverage."
            )

        return {
            "status": "FACT_ANSWERED",
            "factAnswer": answer,
            "factAnswerVersion": FACTUAL_ANSWER_VERSION,
            "conversationContextVersion": CONVERSATION_CONTEXT_VERSION,
            "evidence": [evidence],
        }

    return chat_response(
        "Could you clarify which engineering metric or part of the platform you are referring to?"
    )
