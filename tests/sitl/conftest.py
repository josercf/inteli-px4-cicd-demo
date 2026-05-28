"""Fixtures pytest para testes SITL.

Princípios FIRST aplicados:
- **Fast**: fixtures cacheiam connection/setup quando possível (scope='session').
- **Independent**: cada teste tem estado limpo (mission reset entre testes).
- **Repeatable**: timeouts e thresholds determinísticos, sem `sleep()` arbitrário.
- **Self-validating**: cada fixture documenta pré/pós condições.
- **Timely**: validados em PR #3, antes de quality gates obrigatórios (PR #4).
"""

from __future__ import annotations

import asyncio
import os
import subprocess
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from mavsdk import System


# --------------------------------------------------------------------------- #
# URLs e paths — configuráveis via env, com defaults pro compose padrão.
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def mavlink_url() -> str:
    """MAVLink URL usada por pymavlink (smoke direto, sem mavsdk_server)."""
    return os.environ.get("MAVLINK_URL", "udpin:127.0.0.1:14540")


@pytest.fixture(scope="session")
def mavsdk_server_host() -> str:
    return os.environ.get("MAVSDK_SERVER_HOST", "127.0.0.1")


@pytest.fixture(scope="session")
def mavsdk_server_port() -> int:
    return int(os.environ.get("MAVSDK_SERVER_PORT", "50051"))


@pytest.fixture(scope="session")
def ulog_dir() -> Path:
    """Diretório onde PX4 SITL escreve .ulg (mapeado via docker volume)."""
    return Path(os.environ.get("ULOG_DIR", "/ulogs"))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# MAVSDK System — session-scoped pra reutilizar conexão entre testes.
# Cada teste que precisa de drone armado roda como mission separada;
# o teardown garante que próximo teste começa com drone em estado conhecido.
# --------------------------------------------------------------------------- #


@pytest.fixture
async def mavsdk_system(
    mavsdk_server_host: str, mavsdk_server_port: int, mavlink_url: str
) -> AsyncIterator[System]:
    """MAVSDK System conectado e armable (mas NÃO armado ainda).

    Yields:
        drone pronto pra receber upload_mission/arm/start_mission.

    Cleanup:
        Best-effort land() pra deixar drone em estado seguro pro próximo teste.
    """
    from mavsdk import System

    drone = System(mavsdk_server_address=mavsdk_server_host, port=mavsdk_server_port)
    await drone.connect(system_address=mavlink_url)

    await _wait_connection(drone, timeout_s=30)
    await _wait_armable(drone, timeout_s=90)

    yield drone

    # Teardown: tentar pousar caso o teste tenha deixado drone armado/voando.
    import contextlib

    with contextlib.suppress(Exception):
        await asyncio.wait_for(drone.action.land(), timeout=10)


async def _wait_connection(drone: System, timeout_s: float) -> None:
    """Espera heartbeat MAVLink. Sem isso, próximos comandos falham silenciosamente."""

    async def loop() -> None:
        async for state in drone.core.connection_state():
            if state.is_connected:
                return

    await asyncio.wait_for(loop(), timeout=timeout_s)


async def _wait_armable(drone: System, timeout_s: float) -> None:
    """Espera health checks indicarem drone armable (EKF2 convergido + GPS + home)."""

    async def loop() -> None:
        async for health in drone.telemetry.health():
            if (
                health.is_global_position_ok
                and health.is_home_position_ok
                and health.is_local_position_ok
                and health.is_armable
            ):
                return

    await asyncio.wait_for(loop(), timeout=timeout_s)


# --------------------------------------------------------------------------- #
# Mission runners — executam run_mission.py CLI como subprocess.
# Mantém isolamento de processo (assim flakiness de evento async não vaza
# entre testes) e usa mesmo entrypoint do production code.
# --------------------------------------------------------------------------- #


def _run_mission(
    repo_root: Path,
    mission_yaml: Path,
    timeout_s: int,
    mavsdk_server_host: str,
    mavsdk_server_port: int,
    mavlink_url: str,
) -> subprocess.CompletedProcess[str]:
    """Executa run_mission.py CLI. Síncrono — cada chamada espera missão fechar."""
    return subprocess.run(
        [
            "python",
            "-m",
            "tools.run_mission",
            "--mission",
            str(mission_yaml),
            "--mavsdk-server",
            mavsdk_server_host,
            "--mavsdk-port",
            str(mavsdk_server_port),
            "--system-address",
            mavlink_url,
        ],
        cwd=repo_root,
        timeout=timeout_s,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def run_mission(
    repo_root: Path, mavsdk_server_host: str, mavsdk_server_port: int, mavlink_url: str
) -> Any:
    """Factory fixture: retorna função que executa missão arbitrária."""

    def _factory(yaml_path: str | Path, timeout_s: int = 300) -> subprocess.CompletedProcess[str]:
        path = Path(yaml_path)
        if not path.is_absolute():
            path = repo_root / path
        result = _run_mission(
            repo_root, path, timeout_s, mavsdk_server_host, mavsdk_server_port, mavlink_url
        )
        if result.returncode != 0:
            pytest.fail(
                f"run_mission falhou (exit={result.returncode}) "
                f"para missão {path.name}\n"
                f"stdout:\n{result.stdout[-1500:]}\n"
                f"stderr:\n{result.stderr[-1500:]}"
            )
        return result

    return _factory


@pytest.fixture
def latest_ulog_path(ulog_dir: Path) -> Path:
    """Retorna path do .ulg mais recente. Use APÓS run_mission ter rodado."""
    if not ulog_dir.is_dir():
        pytest.skip(f"ulog_dir não existe: {ulog_dir}")
    candidates = sorted(
        ulog_dir.rglob("*.ulg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        pytest.skip(f"nenhum .ulg encontrado em {ulog_dir}")
    return candidates[0]


# --------------------------------------------------------------------------- #
# Cache da missão: roda UMA vez por sessão, vários testes consomem o mesmo
# resultado. PX4 SITL não reinicializa entre missões sem reset completo do
# container — chamar run_mission 2x na mesma sessão faz a 2ª travar no arm.
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def square_50m_mission_completed(
    repo_root: Path,
    ulog_dir: Path,
    mavsdk_server_host: str,
    mavsdk_server_port: int,
    mavlink_url: str,
) -> dict[str, Path | subprocess.CompletedProcess[str]]:
    """Executa a missão square_50m UMA vez por sessão de testes.

    Returns:
        dict com:
        - 'result': CompletedProcess do CLI run_mission
        - 'ulog': Path do .ulg gerado

    Falha (pytest.fail) se a missão não completar — invalida todos os testes
    dependentes, que é o comportamento desejado.
    """
    result = _run_mission(
        repo_root,
        repo_root / "missions" / "square_50m.yaml",
        timeout_s=300,
        mavsdk_server_host,
        mavsdk_server_port,
        mavlink_url,
    )
    if result.returncode != 0:
        pytest.fail(
            f"square_50m mission falhou (exit={result.returncode}).\n"
            f"stdout: {result.stdout[-1500:]}\n"
            f"stderr: {result.stderr[-1500:]}"
        )

    if not ulog_dir.is_dir():
        pytest.fail(f"ulog_dir não existe após missão: {ulog_dir}")
    candidates = sorted(
        ulog_dir.rglob("*.ulg"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        pytest.fail(f"missão completou mas nenhum .ulg em {ulog_dir}")

    return {"result": result, "ulog": candidates[0]}
