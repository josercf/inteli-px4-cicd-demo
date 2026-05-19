"""Testes para libs.drone_modeling.dynamics."""

import pytest

from libs.drone_modeling.dynamics import compute_thrust


class TestComputeThrust:
    def test_basic_multiplication(self) -> None:
        assert compute_thrust(mass=2.0, acceleration=5.0) == 10.0

    def test_zero_mass_returns_zero(self) -> None:
        assert compute_thrust(mass=0.0, acceleration=9.81) == 0.0

    def test_negative_acceleration_inverts_thrust(self) -> None:
        assert compute_thrust(mass=1.5, acceleration=-9.81) == pytest.approx(-14.715)

    def test_rejects_negative_mass(self) -> None:
        with pytest.raises(ValueError, match="mass must be non-negative"):
            compute_thrust(mass=-1.0, acceleration=9.81)

class TestComputeWeight:
    def test_weight_calculation(self) -> None:
        from libs.drone_modeling.dynamics import compute_weight
        assert compute_weight(mass=2.0) == pytest.approx(19.62)

    def test_zero_mass_returns_zero(self) -> None:
        from libs.drone_modeling.dynamics import compute_weight
        assert compute_weight(mass=0.0) == 0.0

    def test_rejects_negative_mass(self) -> None:
        from libs.drone_modeling.dynamics import compute_weight
        with pytest.raises(ValueError, match="mass must be non-negative"):
            compute_weight(mass=-1.0)