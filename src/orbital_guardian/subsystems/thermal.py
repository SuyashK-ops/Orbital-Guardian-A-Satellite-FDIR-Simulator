from __future__ import annotations

from ..config import SatelliteConfig
from ..types import FaultEffect


def update_temperature_c(
    current_temperature_c: float,
    load_power_w: float,
    in_sunlight: bool,
    solar_incidence: float,
    sink_temperature_c: float,
    heater_on: bool,
    step_minutes: int,
    satellite: SatelliteConfig,
    fault_effect: FaultEffect,
) -> float:
    internal_heat_w = load_power_w * satellite.electrical_to_heat_fraction
    solar_heat_w = satellite.sun_absorbed_w * solar_incidence if in_sunlight else 0.0
    eclipse_bias_w = 0.0 if in_sunlight else satellite.eclipse_bias_w
    heater_heat_w = satellite.heater_power_w if heater_on else 0.0
    net_heat_w = (
        internal_heat_w
        + solar_heat_w
        + eclipse_bias_w
        + heater_heat_w
        + fault_effect.thermal_bias_w
        - satellite.thermal_conductance_w_per_c * (current_temperature_c - sink_temperature_c)
    )
    delta_c = net_heat_w * (step_minutes * 60.0) / satellite.thermal_mass_j_per_c
    return current_temperature_c + delta_c

