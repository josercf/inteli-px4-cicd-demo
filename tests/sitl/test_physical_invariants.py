"""Invariantes físicos do voo — testes que falham se o drone violou regras
de segurança absolutas durante a missão.

Diferente de baseline thresholds (que medem performance), invariantes são
regras que SEMPRE têm que valer, independente da missão:
- Aceleração instantânea não excede limite mecânico do hardware.
- Altitude nunca é negativa (drone abaixo do solo é bug ou crash).
- Drone permanece dentro do geofence configurado.
- Bateria não tem queda anômala (>15% num único intervalo) indicando crash.

Esses testes são parametrizados por missão: se o invariante quebra em alguma
missão, é regressão real.
"""

import math
from pathlib import Path

import pytest

from libs.drone_modeling.mission import load_mission

pytestmark = pytest.mark.sitl


# --------------------------------------------------------------------------- #
# Configuração das missões disponíveis. Adicionar nova missão = nova linha.
# --------------------------------------------------------------------------- #

MISSIONS = [
    pytest.param("missions/square_50m.yaml", id="square_50m"),
    # Outras missões entram aqui conforme repo cresce: line_30m, hover_test, etc.
]


def _extract_full_telemetry(repo_root: Path, ulog_path: Path) -> dict:
    """Extrai métricas + lê arrays brutos do ULog para asserções detalhadas."""
    from pyulog import ULog

    log = ULog(str(ulog_path))

    def get_topic(name: str):
        for d in log.data_list:
            if d.name == name:
                return d
        return None

    out: dict[str, list] = {
        "altitudes_m": [],
        "accel_modules": [],
        "battery_pct": [],
        "positions_ne": [],  # (north, east) em m
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


@pytest.fixture
def mission_telemetry(
    request: pytest.FixtureRequest,
    run_mission: object,
    latest_ulog_path: Path,
    repo_root: Path,
) -> dict:
    """Executa a missão indicada via parametrize e retorna telemetria bruta."""
    mission_yaml = request.param
    run_mission(mission_yaml)  # type: ignore[operator]
    return _extract_full_telemetry(repo_root, latest_ulog_path)


# --------------------------------------------------------------------------- #
# Invariantes — cada teste valida UMA regra. Parametrizado por missão.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("mission_telemetry", MISSIONS, indirect=True)
def test_max_acceleration_within_hardware_limit(mission_telemetry: dict) -> None:
    """Aceleração nunca excede 15 m/s² (limite mecânico nominal do quadrotor x500).

    Excede = motores reagindo agressivo demais → desgaste prematuro de hardware
    no campo. Valor 15 está alinhado com PX4 default MC_TPA_RATE_P.
    """
    accels = mission_telemetry["accel_modules"]
    if not accels:
        pytest.skip("sem amostras de aceleração no ULog")
    max_accel = max(accels)
    assert max_accel < 15.0, (
        f"violação de invariante: aceleração máxima {max_accel:.2f} m/s² "
        f"excede limite mecânico de 15 m/s²"
    )


@pytest.mark.parametrize("mission_telemetry", MISSIONS, indirect=True)
def test_altitude_never_negative(mission_telemetry: dict) -> None:
    """Drone nunca passa abaixo do solo (altitude < -0.5m indica crash ou bug NED)."""
    altitudes = mission_telemetry["altitudes_m"]
    if not altitudes:
        pytest.skip("sem amostras de altitude no ULog")
    min_alt = min(altitudes)
    # Tolerância de -0.5m: pouso pode registrar leve negativo por ruído de sensor.
    assert min_alt >= -0.5, (
        f"violação de invariante: altitude mínima {min_alt:.2f}m indica drone "
        f"abaixo do solo (crash ou bug de conversão NED→altitude)"
    )


@pytest.mark.parametrize("mission_telemetry", MISSIONS, indirect=True)
def test_position_within_geofence(mission_telemetry: dict) -> None:
    """Drone permanece dentro do geofence definido na missão.

    Lê o geofence_radius_m da missão correspondente e valida que nenhuma
    posição (norte, leste) ficou fora desse raio do home (0,0 em NED).
    """
    # Buscar a missão usada por essa parametrização — request.param da fixture
    # não está exposto aqui; assumimos square_50m por enquanto. Quando MISSIONS
    # crescer, mover essa lookup pra fixture.
    repo_root = Path(__file__).resolve().parents[2]
    mission = load_mission(repo_root / "missions" / "square_50m.yaml")
    geofence = mission.geofence_radius_m

    positions = mission_telemetry["positions_ne"]
    if not positions:
        pytest.skip("sem amostras de posição no ULog")

    max_dist = max(math.sqrt(n * n + e * e) for n, e in positions)
    assert max_dist <= geofence, (
        f"violação de invariante: maior distância do home {max_dist:.1f}m "
        f"excede geofence configurado de {geofence}m"
    )


@pytest.mark.parametrize("mission_telemetry", MISSIONS, indirect=True)
def test_no_anomalous_battery_drop(mission_telemetry: dict) -> None:
    """Bateria não cai mais que 15% num único intervalo entre amostras.

    Quedas grandes entre amostras consecutivas indicam: crash sensor, falha
    elétrica simulada, ou bug no logger. Em voo normal, queda max ~1% por amostra.
    """
    battery = mission_telemetry["battery_pct"]
    if len(battery) < 2:
        pytest.skip("amostras insuficientes de bateria no ULog")
    max_drop = max(battery[i - 1] - battery[i] for i in range(1, len(battery)))
    assert max_drop < 15.0, (
        f"violação de invariante: queda de bateria de {max_drop:.1f}% num "
        f"intervalo indica anomalia (crash, falha elétrica, ou bug do logger)"
    )
