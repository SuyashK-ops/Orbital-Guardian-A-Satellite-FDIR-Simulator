from __future__ import annotations

from dataclasses import dataclass, field

from ..config import FDIRConfig, SatelliteConfig
from ..subsystems.thermal import update_temperature_c
from ..types import FDIRDiagnosis, FaultEffect, OperationMode


@dataclass(slots=True)
class FDIRController:
    config: FDIRConfig
    expected_temperature_c: float
    override_mode: OperationMode | None = None
    override_remaining_minutes: int = 0
    last_signature: tuple[tuple[str, ...], str | None, str | None] | None = None
    condition_counters: dict[str, int] = field(default_factory=dict)

    def step_override_timer(self, step_minutes: int) -> None:
        if self.override_remaining_minutes <= 0:
            self.override_mode = None
            return
        self.override_remaining_minutes = max(0, self.override_remaining_minutes - step_minutes)
        if self.override_remaining_minutes == 0:
            self.override_mode = None

    def select_mode(self, scheduled_mode: OperationMode) -> OperationMode:
        return self.override_mode or scheduled_mode

    def _persisted(self, name: str, condition: bool, minimum_steps: int) -> bool:
        if condition:
            self.condition_counters[name] = self.condition_counters.get(name, 0) + 1
        else:
            self.condition_counters[name] = 0
        return self.condition_counters[name] >= minimum_steps

    def evaluate(
        self,
        telemetry: dict[str, float | bool | str],
        expected_mode_load_w: float,
        satellite: SatelliteConfig,
        solar_incidence: float,
        sink_temperature_c: float,
        heater_on: bool,
        step_minutes: int,
    ) -> FDIRDiagnosis:
        in_sunlight = bool(telemetry["in_sunlight"])
        solar_power_w = float(telemetry["solar_power_w"])
        load_power_w = float(telemetry["load_power_w"])
        net_power_w = float(telemetry["net_power_w"])
        sensor_soc_pct = float(telemetry["sensor_soc_pct"])
        sensor_temperature_c = float(telemetry["sensor_temperature_c"])
        wheel_speed_rpm = abs(float(telemetry["wheel_speed_rpm"]))
        expected_solar_w = float(telemetry["expected_solar_power_w"])

        self.expected_temperature_c = update_temperature_c(
            current_temperature_c=self.expected_temperature_c,
            load_power_w=load_power_w,
            in_sunlight=in_sunlight,
            solar_incidence=solar_incidence,
            sink_temperature_c=sink_temperature_c,
            heater_on=heater_on,
            step_minutes=step_minutes,
            satellite=satellite,
            fault_effect=FaultEffect(),
        )

        temperature_residual_c = sensor_temperature_c - self.expected_temperature_c

        alerts: list[str] = []
        if sensor_soc_pct < self.config.low_soc_pct:
            alerts.append("low_state_of_charge")
        if sensor_soc_pct < self.config.critical_soc_pct:
            alerts.append("critical_state_of_charge")
        if sensor_temperature_c > self.config.high_temp_c:
            alerts.append("high_temperature")
        if sensor_temperature_c > self.config.critical_temp_c:
            alerts.append("critical_temperature")
        if wheel_speed_rpm > self.config.wheel_high_rpm:
            alerts.append("reaction_wheel_high_speed")
        if in_sunlight and expected_solar_w > 1.0:
            ratio = solar_power_w / expected_solar_w
            if self._persisted(
                "underperforming_solar_generation",
                ratio < self.config.solar_generation_ratio_min,
                minimum_steps=3,
            ):
                alerts.append("underperforming_solar_generation")
        if self._persisted(
            "unexpected_power_draw",
            load_power_w > expected_mode_load_w + self.config.unexpected_load_margin_w,
            minimum_steps=2,
        ):
            alerts.append("unexpected_power_draw")
        if self._persisted(
            "sustained_power_deficit",
            net_power_w < self.config.net_power_negative_threshold_w
            and (in_sunlight or sensor_soc_pct < self.config.low_soc_pct + 10.0),
            minimum_steps=4,
        ):
            alerts.append("sustained_power_deficit")
        if self._persisted(
            "temperature_sensor_residual",
            abs(temperature_residual_c) > self.config.temperature_residual_alert_c,
            minimum_steps=5,
        ):
            alerts.append("temperature_sensor_residual")

        scores = {
            "solar_array_degradation": 0,
            "battery_degradation": 0,
            "temperature_sensor_drift": 0,
            "reaction_wheel_anomaly": 0,
            "heater_stuck_on": 0,
            "load_spike": 0,
        }

        if "underperforming_solar_generation" in alerts:
            scores["solar_array_degradation"] += 3
        if "sustained_power_deficit" in alerts and "unexpected_power_draw" in alerts:
            scores["load_spike"] += 3
        if "high_temperature" in alerts and "unexpected_power_draw" in alerts:
            scores["heater_stuck_on"] += 2
        if "high_temperature" in alerts and not in_sunlight:
            scores["heater_stuck_on"] += 1
        if "temperature_sensor_residual" in alerts and "high_temperature" not in alerts:
            scores["temperature_sensor_drift"] += 3
        if "reaction_wheel_high_speed" in alerts:
            scores["reaction_wheel_anomaly"] += 4
        if (
            "critical_state_of_charge" in alerts
            and in_sunlight
            and "underperforming_solar_generation" not in alerts
            and "sustained_power_deficit" not in alerts
            and "unexpected_power_draw" not in alerts
        ):
            scores["battery_degradation"] += 2
        if (
            "low_state_of_charge" in alerts
            and in_sunlight
            and solar_power_w >= expected_solar_w * 0.8
            and net_power_w > -3.0
        ):
            scores["battery_degradation"] += 1

        isolated_fault = None
        confidence = 0.0
        top_fault, top_score = max(scores.items(), key=lambda item: item[1])
        if top_score >= 2:
            isolated_fault = top_fault
            confidence = min(0.95, 0.4 + 0.12 * top_score + 0.04 * max(0, len(alerts) - 1))
        elif alerts:
            isolated_fault = "unknown_anomaly"
            confidence = 0.35

        recommended_mode = None
        actions: list[str] = []
        if "critical_state_of_charge" in alerts or "critical_temperature" in alerts:
            recommended_mode = OperationMode.SAFE
        elif "reaction_wheel_high_speed" in alerts:
            recommended_mode = OperationMode.SAFE
        elif "low_state_of_charge" in alerts:
            recommended_mode = OperationMode.CHARGING
        elif "sustained_power_deficit" in alerts and (
            sensor_soc_pct < self.config.low_soc_pct + 8.0
            or "underperforming_solar_generation" in alerts
            or "unexpected_power_draw" in alerts
        ):
            recommended_mode = OperationMode.CHARGING
        elif isolated_fault == "temperature_sensor_drift":
            recommended_mode = OperationMode.DEGRADED

        if recommended_mode is OperationMode.SAFE:
            actions.extend(["shed_noncritical_loads", "suspend_payload", "stabilize_bus"])
        elif recommended_mode is OperationMode.CHARGING:
            actions.extend(["shed_payload_loads", "bias_toward_power_positive_attitude"])
        elif recommended_mode is OperationMode.DEGRADED:
            actions.extend(["flag_sensor_for_maintenance", "continue_with_reduced_authority"])

        if isolated_fault == "reaction_wheel_anomaly":
            actions.append("perform_momentum_dump")
        if isolated_fault == "heater_stuck_on":
            actions.append("inhibit_faulty_heater_if_possible")
        if isolated_fault == "solar_array_degradation":
            actions.append("prioritize_battery_recharge_windows")

        if recommended_mode is not None:
            self.override_mode = recommended_mode
            self.override_remaining_minutes = self.config.override_hold_minutes

        return FDIRDiagnosis(
            alerts=alerts,
            isolated_fault=isolated_fault,
            confidence=confidence,
            recommended_mode=recommended_mode,
            actions=actions,
            expected_temperature_c=self.expected_temperature_c,
            temperature_residual_c=temperature_residual_c,
        )

    def signature_for(self, diagnosis: FDIRDiagnosis) -> tuple[tuple[str, ...], str | None, str | None]:
        mode = diagnosis.recommended_mode.value if diagnosis.recommended_mode else None
        return (tuple(diagnosis.alerts), diagnosis.isolated_fault, mode)
