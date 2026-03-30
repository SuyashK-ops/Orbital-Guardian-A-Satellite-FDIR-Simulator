from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class OperationMode(str, Enum):
    NOMINAL = "nominal"
    SCIENCE = "science"
    SAFE = "safe"
    CHARGING = "charging"
    DEGRADED = "degraded"


@dataclass(slots=True)
class FaultEffect:
    solar_scale: float = 1.0
    battery_capacity_scale: float = 1.0
    extra_load_w: float = 0.0
    thermal_bias_w: float = 0.0
    temperature_sensor_bias_c: float = 0.0
    temperature_sensor_stuck_c: float | None = None
    soc_sensor_bias_pct: float = 0.0
    wheel_bias_rpm_per_min: float = 0.0
    heater_forced_on: bool = False


@dataclass(slots=True)
class Event:
    time_minute: int
    category: str
    message: str
    metadata: dict[str, str | float | int] = field(default_factory=dict)


@dataclass(slots=True)
class FDIRDiagnosis:
    alerts: list[str]
    isolated_fault: str | None
    confidence: float
    recommended_mode: OperationMode | None
    actions: list[str]
    expected_temperature_c: float
    temperature_residual_c: float


@dataclass(slots=True)
class TelemetrySample:
    time_minute: int
    orbit_phase: float
    in_sunlight: bool
    solar_incidence: float
    scheduled_mode: OperationMode
    effective_mode: OperationMode
    battery_soc_pct: float
    battery_temperature_c: float
    bus_voltage_v: float
    solar_power_w: float
    load_power_w: float
    net_power_w: float
    wheel_speed_rpm: float
    sensor_temperature_c: float
    sensor_soc_pct: float
    expected_temperature_c: float
    temperature_residual_c: float
    active_faults: list[str]
    alerts: list[str]
    isolated_fault: str | None
    isolation_confidence: float
    recommended_mode: OperationMode | None
    recovery_actions: list[str]

    def as_dict(self) -> dict[str, str | float | int | bool]:
        return {
            "time_minute": self.time_minute,
            "orbit_phase": round(self.orbit_phase, 4),
            "in_sunlight": self.in_sunlight,
            "solar_incidence": round(self.solar_incidence, 4),
            "scheduled_mode": self.scheduled_mode.value,
            "effective_mode": self.effective_mode.value,
            "battery_soc_pct": round(self.battery_soc_pct, 3),
            "battery_temperature_c": round(self.battery_temperature_c, 3),
            "bus_voltage_v": round(self.bus_voltage_v, 3),
            "solar_power_w": round(self.solar_power_w, 3),
            "load_power_w": round(self.load_power_w, 3),
            "net_power_w": round(self.net_power_w, 3),
            "wheel_speed_rpm": round(self.wheel_speed_rpm, 3),
            "sensor_temperature_c": round(self.sensor_temperature_c, 3),
            "sensor_soc_pct": round(self.sensor_soc_pct, 3),
            "expected_temperature_c": round(self.expected_temperature_c, 3),
            "temperature_residual_c": round(self.temperature_residual_c, 3),
            "active_faults": ",".join(self.active_faults),
            "alerts": ",".join(self.alerts),
            "isolated_fault": self.isolated_fault or "",
            "isolation_confidence": round(self.isolation_confidence, 3),
            "recommended_mode": self.recommended_mode.value if self.recommended_mode else "",
            "recovery_actions": ",".join(self.recovery_actions),
        }


@dataclass(slots=True)
class ScenarioResult:
    scenario_name: str
    description: str
    telemetry: list[TelemetrySample]
    events: list[Event]
    summary: dict[str, object]
