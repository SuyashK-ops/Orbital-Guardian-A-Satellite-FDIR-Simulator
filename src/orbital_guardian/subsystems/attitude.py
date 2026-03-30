from __future__ import annotations

import math

from ..config import SatelliteConfig
from ..types import FaultEffect, OperationMode


def _target_wheel_speed(mode: OperationMode, satellite: SatelliteConfig) -> float:
    if mode is OperationMode.SCIENCE:
        return satellite.wheel_science_target_rpm
    if mode is OperationMode.SAFE:
        return satellite.wheel_safe_target_rpm
    if mode is OperationMode.CHARGING:
        return satellite.wheel_charging_target_rpm
    if mode is OperationMode.DEGRADED:
        return satellite.wheel_degraded_target_rpm
    return satellite.wheel_nominal_target_rpm


def update_wheel_speed_rpm(
    wheel_speed_rpm: float,
    mode: OperationMode,
    step_minutes: int,
    satellite: SatelliteConfig,
    fault_effect: FaultEffect,
) -> float:
    target = _target_wheel_speed(mode, satellite)
    control_delta = (target - wheel_speed_rpm) * satellite.wheel_response_gain * step_minutes
    disturbance = satellite.wheel_disturbance_rpm_per_min * step_minutes
    if mode in {OperationMode.SAFE, OperationMode.CHARGING}:
        disturbance *= 0.4

    wheel_speed_rpm += control_delta + disturbance + fault_effect.wheel_bias_rpm_per_min * step_minutes

    if mode in {OperationMode.SAFE, OperationMode.CHARGING} and abs(wheel_speed_rpm) > satellite.wheel_safe_target_rpm:
        desat = satellite.wheel_desat_rpm_per_min * step_minutes
        wheel_speed_rpm -= math.copysign(min(abs(wheel_speed_rpm), desat), wheel_speed_rpm)

    return max(-satellite.wheel_saturation_rpm * 1.3, min(satellite.wheel_saturation_rpm * 1.3, wheel_speed_rpm))
