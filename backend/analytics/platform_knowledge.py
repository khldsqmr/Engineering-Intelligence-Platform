"""Governed reference knowledge about EIP."""

PLATFORM_KNOWLEDGE_VERSION = "1.0.0"

PLATFORM_KNOWLEDGE = {
    "overview": (
        "The Engineering Intelligence Platform collects GitHub "
        "pull request and review data, processes it through "
        "Bronze, Silver and Gold analytical layers, and presents "
        "governed engineering metrics across reporting periods. "
        "The platform also supports AI-generated interpretations "
        "subject to evidence validation and evaluation."
    ),
    "workspaces": {
        "Executive Overview": (
            "High-level engineering performance, key metrics and historical trends."
        ),
        "Engineering Lifecycle": (
            "Pull request merge durations, review engagement and lifecycle performance."
        ),
        "Performance Management": ("Daily and weekly engineering metric comparisons."),
        "AI Insights": (
            "AI-generated observations, hypotheses and "
            "recommended investigations subject to validation."
        ),
        "Context Explorer": ("Inspect the structured context supplied to the intelligence engine."),
        "Intelligence History": (
            "Explore saved intelligence, approval decisions, "
            "historical reuse and original execution artifacts."
        ),
        "Data Quality": (
            "Inspect data freshness, availability, source coverage and analytical readiness."
        ),
        "Metric Catalog": (
            "Explore governed metric definitions, calculations and interpretation guidance."
        ),
        "Glossary & Methodology": (
            "Reference terminology, analytical concepts and illustrative calculation examples."
        ),
    },
    "copilot": (
        "Copilot retrieves factual answers directly from "
        "governed analytical evidence and uses an LLM for "
        "interpretive questions. Unvalidated interpretations "
        "are withheld."
    ),
    "governance": (
        "Numerical values are sourced from governed analytical "
        "facts. AI-generated interpretations undergo deterministic "
        "validation and automated evaluation. Evaluation scores "
        "do not guarantee factual correctness."
    ),
}
