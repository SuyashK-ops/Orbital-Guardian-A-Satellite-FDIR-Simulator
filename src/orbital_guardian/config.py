from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .types import OperationMode


@dataclass(slots=True)
class SimulationConfig:
    duration_minutes: int = 720
    step_minutes: int = 1
    orbit_period_minutes: int = 95
    sunlight_fraction: float = 0.62
    start_in_sunlight: bool = True


@dataclass(slots=True)
class SatelliteConfig:
    battery_capacity_wh: float = 120.0
    initial_soc_pct: float = 82.0
    battery_voltage_full_v: float = 31.0
    battery_voltage_empty_v: float = 24.0
    solar_array_max_power_w: float = 92.0
    housekeeping_load_w: float = 16.0
    nominal_avionics_load_w: float = 10.0
    science_payload_load_w: float = 28.0
    adcs_load_w: float = 8.0
    degraded_mode_load_w: float = 14.0
    safe_mode_load_w: float = 6.0
    charging_mode_load_w: float = 8.0
    heater_power_w: float = 10.0
    heater_control_on_below_c: float = 2.0
    heater_control_off_above_c: float = 7.0
    electrical_to_heat_fraction: float = 0.72
    sun_absorbed_w: float = 18.0
    eclipse_bias_w: float = -6.0
    thermal_mass_j_per_c: float = 18000.0
    thermal_conductance_w_per_c: float = 1.9
    initial_temperature_c: float = 16.0
    wheel_speed_initial_rpm: float = 900.0
    wheel_nominal_target_rpm: float = 1300.0
    wheel_science_target_rpm: float = 2400.0
    wheel_degraded_target_rpm: float = 1500.0
    wheel_safe_target_rpm: float = 500.0
    wheel_charging_target_rpm: float = 700.0
    wheel_response_gain: float = 0.05
    wheel_disturbance_rpm_per_min: float = 12.0
    wheel_desat_rpm_per_min: float = 45.0
    wheel_saturation_rpm: float = 4500.0


@dataclass(slots=True)
class ModeScheduleEntry:
    start_minute: int
    mode: OperationMode


@dataclass(slots=True)
class FaultConfig:
    type: str
    name: str
    start_minute: int
    end_minute: int | None = None
    parameters: dict[str, float | int | str | bool] = field(default_factory=dict)


@dataclass(slots=True)
class FDIRConfig:
    low_soc_pct: float = 38.0
    critical_soc_pct: float = 22.0
    high_temp_c: float = 33.0
    critical_temp_c: float = 40.0
    wheel_high_rpm: float = 4000.0
    solar_generation_ratio_min: float = 0.55
    unexpected_load_margin_w: float = 15.0
    net_power_negative_threshold_w: float = -10.0
    temperature_residual_alert_c: float = 9.0
    override_hold_minutes: int = 30


@dataclass(slots=True)
class ScenarioConfig:
    scenario_name: str
    description: str
    simulation: SimulationConfig
    satellite: SatelliteConfig
    mode_schedule: list[ModeScheduleEntry]
    faults: list[FaultConfig]
    fdir: FDIRConfig


def _parse_mode(value: str) -> OperationMode:
    return OperationMode(value.lower())


def load_scenario_config(path: str | Path) -> ScenarioConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    simulation = SimulationConfig(**raw.get("simulation", {}))
    satellite = SatelliteConfig(**raw.get("satellite", {}))
    fdir = FDIRConfig(**raw.get("fdir", {}))

    mode_schedule = [
        ModeScheduleEntry(
            start_minute=entry["start_minute"],
            mode=_parse_mode(entry["mode"]),
        )
        for entry in raw.get("mode_schedule", [{"start_minute": 0, "mode": "nominal"}])
    ]
    mode_schedule.sort(key=lambda entry: entry.start_minute)

    faults: list[FaultConfig] = []
    for entry in raw.get("faults", []):
        parameters = {
            key: value
            for key, value in entry.items()
            if key not in {"type", "name", "start_minute", "end_minute"}
        }
        faults.append(
            FaultConfig(
                type=entry["type"],
                name=entry.get("name", entry["type"]),
                start_minute=entry["start_minute"],
                end_minute=entry.get("end_minute"),
                parameters=parameters,
            )
        )

    return ScenarioConfig(
        scenario_name=raw.get("scenario_name", Path(path).stem),
        description=raw.get(
            "description",
            "Config-driven Orbital Guardian satellite FDIR scenario.",
        ),
        simulation=simulation,
        satellite=satellite,
        mode_schedule=mode_schedule,
        faults=faults,
        fdir=fdir,
    )
