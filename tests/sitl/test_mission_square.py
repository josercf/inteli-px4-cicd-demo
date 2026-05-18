"""Teste SITL: executa missão square_50m e valida métricas baseline.

PR #3 refatorou esse arquivo pra usar fixtures (conftest.py) e remover
duplicação. Comparar com a versão original do PR #2 (git blame) mostra:
- Setup MAVSDK extraído pra fixture (DRY).
- _wait_armable extraído pra fixture (era inline).
- Path do .ulg extraído pra fixture (era glob duplicado).
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.sitl


def test_square_50m_mission_completes(run_mission: object) -> None:
    """Missão square_50m executa do início ao fim sem erro.

    O fixture `run_mission` invoca tools/run_mission.py como subprocess e
    falha o teste com diagnóstico se exit code != 0.
    """
    run_mission("missions/square_50m.yaml")  # type: ignore[operator]


def test_metrics_within_baseline_thresholds(
    run_mission: object, latest_ulog_path: Path, repo_root: Path, tmp_path: Path
) -> None:
    """Após missão, KPIs extraídos do .ulg ficam em janela baseline.

    Thresholds são frouxos no PR #3 (informativos). PR #4 aperta via
    quality_gates.yaml e bloqueia merge.
    """
    import subprocess

    run_mission("missions/square_50m.yaml")  # type: ignore[operator]

    output = tmp_path / "metrics.json"
    result = subprocess.run(
        [
            "python",
            "-m",
            "tools.extract_metrics",
            "--ulog",
            str(latest_ulog_path),
            "--output",
            str(output),
        ],
        cwd=repo_root,
        timeout=60,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"extract_metrics falhou: {result.stderr}"

    metrics = json.loads(output.read_text())

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
