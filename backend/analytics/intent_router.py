"""Lightweight routing for non-analytical Copilot interactions."""

import re

INTENT_ROUTER_VERSION = "1.0.0"


def answer_conversational_message(question: str) -> str | None:
    """Handle simple conversational messages without LLM inference."""

    text = " ".join(question.casefold().strip().split())
    text = re.sub(r"[.!?]+$", "", text).strip()

    if text in {
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there",
        "good morning",
        "good afternoon",
        "good evening",
    }:
        return (
            "Hello! I'm EIP Copilot, your engineering "
            "intelligence assistant. How can I help you today?"
        )

    if text in {
        "thanks",
        "thank you",
        "thank you so much",
        "thanks a lot",
        "okay",
        "ok",
        "great",
        "cool",
    }:
        return (
            "Happy to help! Let me know if you have another question about engineering performance."
        )

    if text in {
        "help",
        "what can you do",
        "how can you help me",
        "who are you",
        "what are you",
        "what is eip",
        "how does this work",
    }:
        return (
            "I can retrieve engineering metrics, compare reporting "
            "periods, explore historical benchmarks, and investigate "
            "changes in pull request lifecycle and review performance. "
            "My analytical answers use governed evidence from EIP."
        )

    from backend.analytics.platform_knowledge import (
        PLATFORM_KNOWLEDGE,
    )

    if text in {
        "how does this dashboard work",
        "how does the dashboard work",
        "how does this platform work",
        "how does eip work",
        "explain this dashboard",
        "explain this platform",
        "tell me about this platform",
        "tell me about eip",
    }:
        return PLATFORM_KNOWLEDGE["overview"]

    if text in {
        "what pages are available",
        "what are the available dashboards",
        "what dashboards are available",
        "what workspaces are available",
        "what can i explore",
    }:
        return "\\n".join(
            f"{name}: {description}"
            for name, description in PLATFORM_KNOWLEDGE["workspaces"].items()
        )

    for name, description in PLATFORM_KNOWLEDGE["workspaces"].items():
        normalized = name.casefold()

        if text in {
            f"what is {normalized}",
            f"what is the {normalized}",
            f"explain {normalized}",
            f"how does {normalized} work",
            f"how does the {normalized} work",
        }:
            return description

    if text in {
        "how does copilot work",
        "how does the copilot work",
        "how do you work",
    }:
        return PLATFORM_KNOWLEDGE["copilot"]

    if text in {
        "how is intelligence validated",
        "how are ai responses validated",
        "can i trust the ai responses",
    }:
        return PLATFORM_KNOWLEDGE["governance"]

    return None
