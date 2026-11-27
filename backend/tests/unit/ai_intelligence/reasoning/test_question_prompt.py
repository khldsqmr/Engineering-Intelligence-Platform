"""Tests for question-specific reasoning instructions."""

from backend.ai_intelligence.reasoning.intelligence_engine import (
    build_generation_system_prompt,
)


def test_narrative_prompt_remains_unchanged():
    original = "Existing engineering analyst prompt."

    result = build_generation_system_prompt(
        original,
        "narrative",
    )

    assert result == original


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
