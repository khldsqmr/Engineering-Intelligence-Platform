"""Numerical correctness tests for Gold engineering metrics."""

from datetime import date

import pytest

from backend.data_engineering.transformations.gold.github_gold import (
    difference,
    elapsed_hours,
    in_period,
    percentage,
    percentage_change,
    percentile,
    safe_mean,
    safe_median,
)


class TestDurationCalculations:
    def test_elapsed_hours(self):
        assert elapsed_hours(
            "2026-11-20T08:00:00Z",
            "2026-11-21T10:30:00Z",
        ) == pytest.approx(26.5)

    def test_zero_elapsed_hours(self):
        timestamp = "2026-11-20T08:00:00Z"
        assert elapsed_hours(timestamp, timestamp) == 0


class TestStatisticalCalculations:
    def test_median_odd_sample(self):
        assert safe_median([10, 30, 20]) == 20

    def test_median_even_sample(self):
        assert safe_median([10, 20, 30, 40]) == 25

    def test_median_empty_sample(self):
        assert safe_median([]) is None

    def test_mean(self):
        assert safe_mean([10, 20, 30]) == 20

    def test_mean_empty_sample(self):
        assert safe_mean([]) is None

    def test_percentile_linear_interpolation(self):
        assert percentile([10, 20, 30, 40], 0.9) == pytest.approx(37.0)

    def test_percentile_single_observation(self):
        assert percentile([25], 0.9) == 25

    def test_percentile_empty_sample(self):
        assert percentile([], 0.9) is None


class TestPercentageCalculations:
    def test_percentage(self):
        assert percentage(25, 100) == 25

    def test_percentage_zero_denominator(self):
        assert percentage(25, 0) is None

    def test_difference(self):
        assert difference(120, 100) == 20

    def test_negative_difference(self):
        assert difference(80, 100) == -20

    def test_missing_difference(self):
        assert difference(None, 100) is None

    @pytest.mark.parametrize(
        ("current", "previous", "expected"),
        [
            (150, 100, 50),
            (75, 100, -25),
            (100, 100, 0),
            (0, 100, -100),
        ],
    )
    def test_percentage_change(self, current, previous, expected):
        assert percentage_change(current, previous) == pytest.approx(expected)

    def test_percentage_change_zero_baseline(self):
        assert percentage_change(100, 0) is None

    def test_percentage_change_missing_baseline(self):
        assert percentage_change(100, None) is None

    def test_percentage_change_missing_current(self):
        assert percentage_change(None, 100) is None


class TestReportingPeriod:
    START = date(2026, 11, 20)
    END = date(2026, 11, 27)

    @pytest.mark.parametrize(
        ("timestamp", "expected"),
        [
            ("2026-11-19T23:59:59Z", False),
            ("2026-11-20T00:00:00Z", True),
            ("2026-11-23T12:00:00Z", True),
            ("2026-11-26T23:59:59Z", True),
            ("2026-11-27T00:00:00Z", False),
        ],
    )
    def test_period_boundaries(self, timestamp, expected):
        assert (
            in_period(
                timestamp,
                self.START,
                self.END,
            )
            is expected
        )
