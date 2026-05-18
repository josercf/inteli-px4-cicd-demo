"""Teste SITL: executa missão square_50m e valida métricas baseline.

PR #3 refatorou esse arquivo pra usar fixture `square_50m_mission_completed`
do conftest (session-scoped). Antes cada teste rodava sua própria missão e
PX4 SITL não re-arma na 2ª — ver issue de timeout no PR #3 antes do fix.
"""

import json
from typing import Any

import pytest

pytestmark = pytest.mark.sitl


def test_square_50m_mission_completes(square_50m_mission_completed: dict[str, Any]) -> None:
    """Smoke: missão square_50m executa do início ao fim sem erro.

    A própria fixture já validou exit code 0 e .ulg gerado, então só
    confirmamos que recebemos os artifacts esperados.
    """
    assert square_50m_mission_completed["result"].returncode == 0
    assert square_50m_mission_completed["ulog"].exists()


def test_metrics_within_baseline_thresholds(
    square_50m_mission_completed: dict[str, Any],
) -> None:
    """Após missão, KPIs extraídos do .ulg ficam em janela baseline.

    Thresholds frouxos no PR #3 (informativos). PR #4 aperta via
    quality_gates.yaml e bloqueia merge.

    PR #4: fixture extrai métricas para reports/metrics.json (path estável).
    """
    metrics_path = square_50m_mission_completed["metrics"]
    assert metrics_path.is_file(), f"metrics.json não encontrado: {metrics_path}"
    metrics = json.loads(metrics_path.read_text())

    # Baseline thresholds — generosos. Pra detectar valores impossíveis,
    # não pra cravar performance ideal.
    assert (
        30 <= metrics["mission_duration_s"] <= 240
    ), f"duração fora do baseline (30-240s): {metrics['mission_duration_s']}"
    assert (
        5 <= metrics["max_altitude_m"] <= 30
    ), f"max_altitude fora (5-30m): {metrics['max_altitude_m']}"
    assert (
        metrics["max_acceleration_m_s2"] < 50
    ), f"max_accel impossível: {metrics['max_acceleration_m_s2']}"
