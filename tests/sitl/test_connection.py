"""Smoke SITL do PR #1: MAVSDK conecta no PX4 dentro de 30s.

PR #2 adiciona testes que dependem de simulador físico (armado, missão).
"""

import asyncio
import os

import pytest
from mavsdk import System

pytestmark = pytest.mark.sitl


@pytest.fixture
def mavlink_url() -> str:
    return os.environ.get("MAVLINK_URL", "udpout://127.0.0.1:14540")


async def test_mavsdk_connects_within_30s(mavlink_url: str) -> None:
    """Valida que MAVSDK detecta heartbeat do PX4 em até 30 segundos.

    Esse teste prova que a plumbing MAVLink (rede docker + UDP + protocolo)
    está funcionando ponta a ponta. Não valida estado de telemetria — isso
    vem no PR #2 com simulador físico.
    """
    drone = System()
    await drone.connect(system_address=mavlink_url)

    async def wait_connected() -> bool:
        async for state in drone.core.connection_state():
            if state.is_connected:
                return True
        return False

    connected = await asyncio.wait_for(wait_connected(), timeout=30)
    assert connected, f"MAVSDK não detectou heartbeat do PX4 em 30s em {mavlink_url}"
