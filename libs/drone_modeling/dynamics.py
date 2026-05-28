"""Modelagem dinâmica para validação física de missões."""


def compute_thrust(mass: float, acceleration: float) -> float:
    """Calcula empuxo (N) para massa (kg) e aceleração (m/s²) dadas.

    Newton's second law: F = m * a. Aceleração negativa representa frenagem
    ou aceleração descendente — empuxo correspondente é também negativo.

    Raises:
        ValueError: se mass for negativa.
    """
    if mass < 0:
        raise ValueError("mass must be non-negative")
    return mass * acceleration


def compute_weight(mass: float, gravity: float = 9.81) -> float:
    """Calcula peso (N) para massa (kg) e gravidade (m/s²) dadas.

    Raises:
        ValueError: se mass for negativa.
    """
    if mass < 0:
        raise ValueError("mass must be non-negative")
    return mass * gravity
