"""Tests for safety score computation."""

import pytest
from ml.src.safety_score import compute_safety_score, SafetyResult
from ml.src.tox_predictor import ToxicityResult


def make_tox_result(overall: float = 30.0, herg: float = 20.0, hepato: float = 25.0) -> ToxicityResult:
    """Create a ToxicityResult for testing."""
    return ToxicityResult(
        overall_toxicity=overall,
        herg_inhibition=herg,
        hepatotoxicity=hepato,
        herg_class="low",
    )


def test_compute_safety_score_returns_result():
    """Test that compute_safety_score returns SafetyResult."""
    tox = make_tox_result()
    result = compute_safety_score(
        tox=tox,
        therapeutic_index=5.0,
        cmax_cmin_ratio=3.0,
        bioavailability_f=0.85,
    )

    assert isinstance(result, SafetyResult)
    assert hasattr(result, "score")
    assert hasattr(result, "label")


def test_safety_score_in_range():
    """Test that safety score is within 0-100."""
    tox = make_tox_result()
    result = compute_safety_score(
        tox=tox,
        therapeutic_index=5.0,
        cmax_cmin_ratio=3.0,
        bioavailability_f=0.85,
    )

    assert 0 <= result.score <= 100


def test_high_toxicity_lowers_score():
    """Test that high toxicity produces lower safety score."""
    low_tox = make_tox_result(overall=10.0)
    high_tox = make_tox_result(overall=90.0)

    low_result = compute_safety_score(
        tox=low_tox,
        therapeutic_index=5.0,
        cmax_cmin_ratio=3.0,
        bioavailability_f=0.85,
    )

    high_result = compute_safety_score(
        tox=high_tox,
        therapeutic_index=5.0,
        cmax_cmin_ratio=3.0,
        bioavailability_f=0.85,
    )

    assert low_result.score > high_result.score


def test_safety_labels():
    """Test that safety labels are assigned correctly."""
    tox = make_tox_result(overall=20.0)
    result = compute_safety_score(
        tox=tox,
        therapeutic_index=8.0,
        cmax_cmin_ratio=2.0,
        bioavailability_f=0.9,
    )

    assert result.label in ["SAFE", "ACCEPTABLE", "HIGH RISK"]
