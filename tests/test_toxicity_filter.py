"""Unit tests for the ToxicityFilter class."""

import pytest

from rdi.models import ToxicityResult
from rdi.toxicity_filter import ToxicityFilter, _CATEGORIES, _HIGH_RISK_THRESHOLD


@pytest.fixture(scope="module")
def toxicity_filter() -> ToxicityFilter:
    """Module-scoped filter so the detoxify model loads only once."""
    return ToxicityFilter()


class TestToxicityFilterEmptyInput:
    """Empty / blank input handling."""

    def test_empty_string(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("")
        assert result.scores == {cat: 0.0 for cat in _CATEGORIES}
        assert result.is_high_risk is False

    def test_whitespace_only(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("   ")
        assert result.scores == {cat: 0.0 for cat in _CATEGORIES}
        assert result.is_high_risk is False


class TestToxicityFilterCategories:
    """Verify all six categories are present in output."""

    def test_all_categories_present(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("This is a normal sentence.")
        assert set(result.scores.keys()) == set(_CATEGORIES)

    def test_scores_in_valid_range(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("Hello, how are you today?")
        for cat, score in result.scores.items():
            assert 0.0 <= score <= 1.0, f"{cat} score {score} out of [0.0, 1.0]"


class TestToxicityFilterHighRisk:
    """Verify is_high_risk flagging logic."""

    def test_benign_text_not_high_risk(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("The weather is lovely today.")
        assert result.is_high_risk is False

    def test_high_risk_matches_threshold(self, toxicity_filter: ToxicityFilter) -> None:
        """is_high_risk should be True iff any score > 0.8."""
        result = toxicity_filter.score("The weather is lovely today.")
        expected = any(s > _HIGH_RISK_THRESHOLD for s in result.scores.values())
        assert result.is_high_risk == expected

    def test_result_is_toxicity_result(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("Some text.")
        assert isinstance(result, ToxicityResult)


class TestToxicityFilterBenignText:
    """Known benign text should have low scores."""

    def test_benign_greeting(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("Good morning, hope you have a great day!")
        for cat, score in result.scores.items():
            assert score < 0.5, f"Benign text scored {score} for {cat}"

    def test_benign_factual(self, toxicity_filter: ToxicityFilter) -> None:
        result = toxicity_filter.score("The capital of France is Paris.")
        for cat, score in result.scores.items():
            assert score < 0.5, f"Factual text scored {score} for {cat}"
