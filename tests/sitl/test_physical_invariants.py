"""Invariantes físicos do voo — testes que falham se o drone violou regras
de segurança absolutas durante a missão.

Diferente de baseline thresholds (que medem performance), invariantes são
regras que SEMPRE têm que valer, independente da missão:
- Aceleração instantânea não excede limite mecânico do hardware.
- Altitude nunca é negativa (drone abaixo do solo é bug ou crash).
- Drone permanece dentro do geofence configurado.
- Bateria não tem queda anômala (>15% num único intervalo) indicando crash.

PR #3: todos os invariantes usam fixture `square_50m_mission_completed`
session-scoped do conftest — missão roda 1× e todos os testes consomem o
mesmo .ulg. Quando tivermos múltiplas missões, parametrizamos novamente.
"""

import math
from pathlib import Path
from typing import Any

import pytest

from libs.drone_modeling.mission import load_mission

pytestmark = pytest.mark.sitl


def _extract_full_telemetry(ulog_path: Path) -> dict:
    """Extrai séries temporais brutas do ULog para asserções detalhadas."""
    from pyulog import ULog

    log = ULog(str(ulog_path))

    def get_topic(name: str) -> Any:
        for d in log.data_list:
            if d.name == name:
                return d
        return None

    out: dict[str, list] = {
        "altitudes_m": [],
        "accel_modules": [],
        "battery_pct": [],
        "positions_ne": [],
    }

    pos = get_topic("vehicle_local_position")
    if pos is not None:
        out["altitudes_m"] = [-z for z in pos.data["z"].tolist()]
        out["positions_ne"] = list(
            zip(pos.data["x"].tolist(), pos.data["y"].tolist(), strict=False)
        )

    accel = get_topic("vehicle_acceleration")
    if accel is not None:
        xs = accel.data["xyz[0]"].tolist()
        ys = accel.data["xyz[1]"].tolist()
        zs = accel.data["xyz[2]"].tolist()
        out["accel_modules"] = [
            math.sqrt(x * x + y * y + z * z) for x, y, z in zip(xs, ys, zs, strict=False)
        ]

    batt = get_topic("battery_status")
    if batt is not None:
        out["battery_pct"] = [r * 100 for r in batt.data["remaining"].tolist()]

    return out


@pytest.fixture(scope="session")
def square_50m_telemetry(square_50m_mission_completed: dict[str, Any]) -> dict:
    """Telemetria bruta extraída UMA vez por sessão a partir do .ulg da missão."""
    return _extract_full_telemetry(square_50m_mission_completed["ulog"])


def test_max_acceleration_within_hardware_limit(square_50m_telemetry: dict) -> None:
    """Aceleração nunca excede 15 m/s² (limite mecânico nominal do quadrotor x500).

    Excede = motores reagindo agressivo demais → desgaste prematuro de hardware
    no campo. Valor 15 está alinhado com PX4 default MC_TPA_RATE_P.
    """
    accels = square_50m_telemetry["accel_modules"]
    if not accels:
        pytest.skip("sem amostras de aceleração no ULog")
    max_accel = max(accels)
    assert max_accel < 15.0, (
        f"violação de invariante: aceleração máxima {max_accel:.2f} m/s² "
        f"excede limite mecânico de 15 m/s²"
    )


def test_altitude_never_negative(square_50m_telemetry: dict) -> None:
    """Drone nunca passa abaixo do solo (altitude < -0.5m indica crash ou bug NED)."""
    altitudes = square_50m_telemetry["altitudes_m"]
    if not altitudes:
        pytest.skip("sem amostras de altitude no ULog")
    min_alt = min(altitudes)
    # Tolerância de -0.5m: pouso pode registrar leve negativo por ruído de sensor.
    assert min_alt >= -0.5, (
        f"violação de invariante: altitude mínima {min_alt:.2f}m indica drone "
        f"abaixo do solo (crash ou bug de conversão NED→altitude)"
    )


def test_position_within_geofence(square_50m_telemetry: dict, repo_root: Path) -> None:
    """Drone permanece dentro do geofence definido na missão."""
    mission = load_mission(repo_root / "missions" / "square_50m.yaml")
    geofence = mission.geofence_radius_m

    positions = square_50m_telemetry["positions_ne"]
    if not positions:
        pytest.skip("sem amostras de posição no ULog")

    max_dist = max(math.sqrt(n * n + e * e) for n, e in positions)
    assert max_dist <= geofence, (
        f"violação de invariante: maior distância do home {max_dist:.1f}m "
        f"excede geofence configurado de {geofence}m"
    )


def test_no_anomalous_battery_drop(square_50m_telemetry: dict) -> None:
    """Bateria não cai mais que 15% num único intervalo entre amostras."""
    battery = square_50m_telemetry["battery_pct"]
    if len(battery) < 2:
        pytest.skip("amostras insuficientes de bateria no ULog")
    max_drop = max(battery[i - 1] - battery[i] for i in range(1, len(battery)))
    assert max_drop < 15.0, (
        f"violação de invariante: queda de bateria de {max_drop:.1f}% num "
        f"intervalo indica anomalia (crash, falha elétrica, ou bug do logger)"
    )
