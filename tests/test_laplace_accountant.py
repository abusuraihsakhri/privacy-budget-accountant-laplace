"""Mathematical and security invariants for the Laplace accountant."""
import math
import pytest

from dp_laplace_budget.accountant import (
    BudgetExceeded, PrivacyBudget, bounded_mean_sensitivity,
    count_sensitivity, laplace_noise,
)


def test_known_inverse_cdf_points():
    assert laplace_noise(2, uniform=0.5) == pytest.approx(0)
    assert laplace_noise(2, uniform=0.25) == pytest.approx(-2 * math.log(2))
    assert laplace_noise(2, uniform=0.75) == pytest.approx(2 * math.log(2))


def test_global_sensitivity_conventions():
    assert count_sensitivity() == 1
    assert bounded_mean_sensitivity(0, 10, 5) == pytest.approx(2)
    with pytest.raises(ValueError):
        bounded_mean_sensitivity(0, 10, 0)
    with pytest.raises(ValueError):
        bounded_mean_sensitivity(10, 0, 5)
    with pytest.raises(ValueError):
        bounded_mean_sensitivity(0, 10, True)


def test_exact_basic_composition_and_rejection():
    ledger = PrivacyBudget(0.3)
    first = ledger.release(20, epsilon=0.1, sensitivity=1)
    second = ledger.release(30, epsilon=0.2, sensitivity=1)
    assert first.scale == pytest.approx(10)
    assert second.spent_epsilon == pytest.approx(0.3)
    assert second.remaining_epsilon == 0
    with pytest.raises(BudgetExceeded):
        ledger.release(40, epsilon=0.01, sensitivity=1)
    assert ledger.spent_epsilon == pytest.approx(0.3)


@pytest.mark.parametrize("v", [0, -1, float("nan"), float("inf"), True])
def test_budget_invalid(v):
    with pytest.raises(ValueError):
        PrivacyBudget(v)


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_release_rejects_invalid_inputs_without_spending(bad):
    ledger = PrivacyBudget(1)
    with pytest.raises(ValueError):
        ledger.release(3, epsilon=bad, sensitivity=1)
    with pytest.raises(ValueError):
        ledger.release(3, epsilon=0.1, sensitivity=bad)
    assert ledger.spent_epsilon == 0


def test_result_is_noised_and_not_cached():
    ledger = PrivacyBudget(1)
    release = ledger.release(10, epsilon=0.5, sensitivity=2)
    assert release.noisy_value == pytest.approx(10 + release.noise)
    assert release.scale == pytest.approx(4)
    assert ledger.spent_epsilon == pytest.approx(0.5)


def test_noise_endpoints_and_scale_rejected():
    for u in [0, 1, -0.1, float("nan")]:
        with pytest.raises(ValueError):
            laplace_noise(1, uniform=u)
    with pytest.raises(ValueError):
        laplace_noise(0)
