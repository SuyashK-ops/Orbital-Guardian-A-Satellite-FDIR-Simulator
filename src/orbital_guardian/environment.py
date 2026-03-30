from __future__ import annotations

import math
from dataclasses import dataclass

from .config import SimulationConfig


@dataclass(slots=True)
class EnvironmentSnapshot:
    orbit_phase: float
    in_sunlight: bool
    solar_incidence: float
    sink_temperature_c: float


def get_environment(time_minute: int, config: SimulationConfig) -> EnvironmentSnapshot:
    offset = 0.0 if config.start_in_sunlight else 0.5
    orbit_phase = ((time_minute / config.orbit_period_minutes) + offset) % 1.0
    in_sunlight = orbit_phase < config.sunlight_fraction

    if in_sunlight:
        sun_phase = orbit_phase / max(config.sunlight_fraction, 1e-6)
        solar_incidence = 0.35 + 0.65 * math.sin(math.pi * sun_phase)
        sink_temperature_c = 5.0
    else:
        solar_incidence = 0.0
        sink_temperature_c = -14.0

    return EnvironmentSnapshot(
        orbit_phase=orbit_phase,
        in_sunlight=in_sunlight,
        solar_incidence=max(0.0, solar_incidence),
        sink_temperature_c=sink_temperature_c,
    )

