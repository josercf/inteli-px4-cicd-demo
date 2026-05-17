"""Smoke SITL do PR #1: pymavlink recebe heartbeat do PX4 em <30s.

Usamos pymavlink (Python puro) em vez de MAVSDK 2.x porque o
mavsdk_server (gRPC backend) tem problemas de bootstrap no container
python:3.11-slim. Para PR #2 (missão real) avaliamos voltar pra MAVSDK
ou migrar pra dronekit.

Requer container tester com `network_mode: service:sitl` (mesma netns
do PX4 SITL) — sem isso, PX4 não enviaria heartbeats pra rede docker
bridge (envia só pra localhost por default).
"""

import os

import pytest
from pymavlink import mavutil

pytestmark = pytest.mark.sitl


@pytest.fixture
def mavlink_url() -> str:
    return os.environ.get("MAVLINK_URL", "udpin:127.0.0.1:14540")


def test_px4_emits_heartbeat_within_30s(mavlink_url: str) -> None:
    """Valida que o PX4 SITL emite heartbeat MAVLink em até 30s.

    Esse teste prova que a plumbing está completa:
    1. PX4 SITL inicializou (jmavsim + autopilot)
    2. MAVLink module está rodando e emitindo heartbeat
    3. Rede docker entre tester e sitl funciona (shared netns)
    """
    conn = mavutil.mavlink_connection(mavlink_url)
    msg = conn.wait_heartbeat(timeout=30)
    assert msg is not None, f"PX4 não emitiu heartbeat em 30s ({mavlink_url})"
    assert conn.target_system != 0, "target_system deveria ser != 0 após heartbeat"
