from __future__ import annotations

from dataclasses import dataclass

from ..config import FaultConfig
from ..types import FaultEffect


@dataclass(slots=True)
class FaultModel:
    config: FaultConfig
    _was_active: bool = False

    def is_active(self, time_minute: int) -> bool:
        if time_minute < self.config.start_minute:
            return False
        if self.config.end_minute is None:
            return True
        return time_minute <= self.config.end_minute

    def active_transition(self, time_minute: int) -> tuple[bool, bool]:
        is_active_now = self.is_active(time_minute)
        activated = is_active_now and not self._was_active
        cleared = self._was_active and not is_active_now
        self._was_active = is_active_now
        return activated, cleared

    def effect(self, time_minute: int) -> FaultEffect:
        raise NotImplementedError


class SolarArrayDegradationFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        return FaultEffect(solar_scale=float(self.config.parameters.get("solar_scale", 0.55)))


class BatteryDegradationFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        return FaultEffect(
            battery_capacity_scale=float(self.config.parameters.get("capacity_scale", 0.7))
        )


class TemperatureSensorDriftFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        hours = max(0.0, (time_minute - self.config.start_minute) / 60.0)
        slope = float(self.config.parameters.get("drift_c_per_hour", 1.6))
        return FaultEffect(temperature_sensor_bias_c=hours * slope)


class TemperatureSensorStuckFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        return FaultEffect(
            temperature_sensor_stuck_c=float(self.config.parameters.get("stuck_value_c", 42.0))
        )


class ReactionWheelAnomalyFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        return FaultEffect(
            wheel_bias_rpm_per_min=float(self.config.parameters.get("extra_spin_rpm_per_min", 28.0))
        )


class HeaterStuckOnFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        return FaultEffect(
            heater_forced_on=True,
            thermal_bias_w=float(self.config.parameters.get("thermal_bias_w", 10.0)),
        )


class LoadSpikeFault(FaultModel):
    def effect(self, time_minute: int) -> FaultEffect:
        return FaultEffect(extra_load_w=float(self.config.parameters.get("extra_load_w", 22.0)))


FAULT_TYPES: dict[str, type[FaultModel]] = {
    "solar_array_degradation": SolarArrayDegradationFault,
    "battery_degradation": BatteryDegradationFault,
    "temperature_sensor_drift": TemperatureSensorDriftFault,
    "temperature_sensor_stuck": TemperatureSensorStuckFault,
    "reaction_wheel_anomaly": ReactionWheelAnomalyFault,
    "heater_stuck_on": HeaterStuckOnFault,
    "load_spike": LoadSpikeFault,
}


def build_fault_models(configs: list[FaultConfig]) -> list[FaultModel]:
    models: list[FaultModel] = []
    for config in configs:
        model_cls = FAULT_TYPES.get(config.type)
        if model_cls is None:
            raise ValueError(f"Unsupported fault type '{config.type}'.")
        models.append(model_cls(config=config))
    return models

