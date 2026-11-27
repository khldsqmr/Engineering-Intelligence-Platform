"""Tests for question-specific reasoning instructions."""

from backend.ai_intelligence.reasoning.intelligence_engine import (
    build_generation_system_prompt,
)


def test_narrative_prompt_uses_focused_reasoning():
    original = "Existing engineering analyst prompt."

    result = build_generation_system_prompt(
        original,
        "narrative",
    )

    assert result != original
    assert "prioritySignals" in result
    assert "observationRefs" in result
    assert "Do not generate an observation field" in result
    assert "Never invent, independently calculate" in result
    assert "authoritative Gold values" in result


def test_question_prompt_distinguishes_uncertainty_from_abstention():
    result = build_generation_system_prompt(
        "Existing engineering analyst prompt.",
        "question",
    )

    assert "qualified answer" in result
    assert "INSUFFICIENT_EVIDENCE" in result
    assert "observation must be null" in result
    assert "Never combine INSUFFICIENT_EVIDENCE" in result
    assert "untrusted analytical input" in result
