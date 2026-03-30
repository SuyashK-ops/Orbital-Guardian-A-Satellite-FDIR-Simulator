from __future__ import annotations

from dataclasses import dataclass

from ..config import SatelliteConfig
from ..types import FaultEffect, OperationMode


@dataclass(slots=True)
class PowerState:
    battery_energy_wh: float
    battery_soc_pct: float
    bus_voltage_v: float
    solar_power_w: float
    load_power_w: float
    net_power_w: float
    heater_commanded_on: bool


def mode_load_w(mode: OperationMode, satellite: SatelliteConfig) -> float:
    if mode is OperationMode.SCIENCE:
        return (
            satellite.housekeeping_load_w
            + satellite.nominal_avionics_load_w
            + satellite.adcs_load_w
            + satellite.science_payload_load_w
        )
    if mode is OperationMode.SAFE:
        return satellite.housekeeping_load_w + satellite.safe_mode_load_w
    if mode is OperationMode.CHARGING:
        return satellite.housekeeping_load_w + satellite.charging_mode_load_w
    if mode is OperationMode.DEGRADED:
        return satellite.housekeeping_load_w + satellite.degraded_mode_load_w
    return satellite.housekeeping_load_w + satellite.nominal_avionics_load_w + satellite.adcs_load_w


def update_power_state(
    battery_energy_wh: float,
    temperature_c: float,
    mode: OperationMode,
    in_sunlight: bool,
    solar_incidence: float,
    step_minutes: int,
    satellite: SatelliteConfig,
    fault_effect: FaultEffect,
) -> PowerState:
    effective_capacity_wh = satellite.battery_capacity_wh * fault_effect.battery_capacity_scale
    effective_capacity_wh = max(effective_capacity_wh, satellite.battery_capacity_wh * 0.25)

    heater_commanded_on = temperature_c < satellite.heater_control_on_below_c
    if temperature_c > satellite.heater_control_off_above_c:
        heater_commanded_on = False
    if fault_effect.heater_forced_on:
        heater_commanded_on = True

    solar_power_w = 0.0
    if in_sunlight:
        solar_power_w = satellite.solar_array_max_power_w * solar_incidence * fault_effect.solar_scale
        if mode is OperationMode.CHARGING:
            solar_power_w *= 1.07

    load_power_w = mode_load_w(mode, satellite)
    if heater_commanded_on:
        load_power_w += satellite.heater_power_w
    load_power_w += fault_effect.extra_load_w

    net_power_w = solar_power_w - load_power_w
    battery_energy_wh = max(
        0.0,
        min(effective_capacity_wh, battery_energy_wh + net_power_w * (step_minutes / 60.0)),
    )
    battery_soc_pct = 100.0 * battery_energy_wh / effective_capacity_wh
    bus_voltage_v = satellite.battery_voltage_empty_v + (
        (satellite.battery_voltage_full_v - satellite.battery_voltage_empty_v) * battery_soc_pct / 100.0
    )

    return PowerState(
        battery_energy_wh=battery_energy_wh,
        battery_soc_pct=battery_soc_pct,
        bus_voltage_v=bus_voltage_v,
        solar_power_w=solar_power_w,
        load_power_w=load_power_w,
        net_power_w=net_power_w,
        heater_commanded_on=heater_commanded_on,
    )

