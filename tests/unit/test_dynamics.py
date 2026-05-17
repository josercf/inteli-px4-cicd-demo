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
