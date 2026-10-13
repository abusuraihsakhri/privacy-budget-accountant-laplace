"""Laplace mechanism and basic (pure) differential-privacy composition.

The caller MUST supply a proven global sensitivity for the query and the
appropriate adjacency model. The accountant is in-memory and session-scoped.
"""
from dataclasses import asdict, dataclass
from decimal import Decimal
import math
import secrets
import threading


class BudgetExceeded(ValueError):
    """A release would exceed the configured epsilon budget."""


def _finite(value: float, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(number) or (positive and number <= 0):
        raise ValueError(f"{label} must be finite" + (" and positive" if positive else ""))
    return number


def count_sensitivity() -> float:
    """Global sensitivity for an unweighted count under add/remove adjacency."""
    return 1.0


def bounded_mean_sensitivity(lower: float, upper: float, n: int) -> float:
    """Sensitivity of a fixed-size, replace-one bounded sample mean."""
    lower = _finite(lower, "lower")
    upper = _finite(upper, "upper")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    if upper <= lower:
        raise ValueError("upper must exceed lower")
    sensitivity = (upper - lower) / n
    if not math.isfinite(sensitivity) or sensitivity <= 0:
        raise ValueError("invalid mean sensitivity")
    return sensitivity


def laplace_noise(scale: float, *, uniform: float = None) -> float:
    """Sample Laplace(0, scale) with OS-backed randomness by default.

    The `uniform` argument is for deterministic mathematical tests only.
    Production callers must not substitute predictable random samples.
    """
    scale = _finite(scale, "scale", positive=True)
    if uniform is None:
        # Avoid floating-point rounding to exactly 1 at the upper endpoint.
        uniform = (secrets.randbits(53) + 1) / ((2 ** 53) + 2)
    else:
        uniform = _finite(uniform, "uniform")
        if not 0 < uniform < 1:
            raise ValueError("uniform must be strictly between 0 and 1")
    if uniform < 0.5:
        return scale * math.log(2 * uniform)
    return -scale * math.log(2 * (1 - uniform))


@dataclass(frozen=True)
class LaplaceRelease:
    noisy_value: float
    noise: float
    epsilon: float
    sensitivity: float
    scale: float
    spent_epsilon: float
    remaining_epsilon: float

    def to_dict(self):
        return asdict(self)


class PrivacyBudget:
    """Session-local epsilon ledger using basic sequential composition (delta=0).

    Release once for each actual disclosure. New instances, browsers and
    processes DO NOT share expenditure or reset a real-world privacy budget.
    """

    def __init__(self, total_epsilon: float):
        total = _finite(total_epsilon, "total_epsilon", positive=True)
        self.total_epsilon = total
        self._total = Decimal(str(total))
        self._spent = Decimal("0")
        self._lock = threading.Lock()

    @property
    def spent_epsilon(self) -> float:
        with self._lock:
            return float(self._spent)

    @property
    def remaining_epsilon(self) -> float:
        with self._lock:
            return float(self._total - self._spent)

    def release(self, value: float, *, sensitivity: float, epsilon: float) -> LaplaceRelease:
        value = _finite(value, "value")
        sensitivity = _finite(sensitivity, "sensitivity", positive=True)
        epsilon = _finite(epsilon, "epsilon", positive=True)
        scale = sensitivity / epsilon
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("invalid Laplace noise scale")
        with self._lock:
            charge = Decimal(str(epsilon))
            next_spent = self._spent + charge
            if next_spent > self._total:
                raise BudgetExceeded("epsilon budget exhausted; release rejected")
            # Commit expenditure only after successful noise generation.
            noise = laplace_noise(scale)
            noisy_value = value + noise
            if not math.isfinite(noisy_value):
                raise ValueError("noisy result would be non-finite")
            self._spent = next_spent
            return LaplaceRelease(
                noisy_value=noisy_value,
                noise=noise,
                epsilon=epsilon,
                sensitivity=sensitivity,
                scale=scale,
                spent_epsilon=float(self._spent),
                remaining_epsilon=float(self._total - self._spent),
            )
