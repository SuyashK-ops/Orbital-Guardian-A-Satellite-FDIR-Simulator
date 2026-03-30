from __future__ import annotations

from pathlib import Path

from .config import ScenarioConfig, load_scenario_config
from .environment import get_environment
from .faults import build_fault_models
from .fdir import FDIRController
from .modes import scheduled_mode_for_time
from .reporting import save_all_plots, save_summary_outputs, summarize_result
from .subsystems.attitude import update_wheel_speed_rpm
from .subsystems.power import mode_load_w, update_power_state
from .subsystems.thermal import update_temperature_c
from .types import Event, FaultEffect, ScenarioResult, TelemetrySample


def run_scenario(
    config_or_path: ScenarioConfig | str | Path,
    output_dir: str | Path | None = None,
    save_plots: bool = False,
    save_outputs: bool = False,
) -> ScenarioResult:
    config = (
        load_scenario_config(config_or_path)
        if isinstance(config_or_path, (str, Path))
        else config_or_path
    )

    fault_models = build_fault_models(config.faults)
    controller = FDIRController(
        config=config.fdir,
        expected_temperature_c=config.satellite.initial_temperature_c,
    )

    events: list[Event] = [
        Event(
            time_minute=0,
            category="scenario_start",
            message=f"Scenario '{config.scenario_name}' started.",
        )
    ]
    telemetry: list[TelemetrySample] = []

    battery_energy_wh = config.satellite.battery_capacity_wh * config.satellite.initial_soc_pct / 100.0
    battery_temperature_c = config.satellite.initial_temperature_c
    wheel_speed_rpm = config.satellite.wheel_speed_initial_rpm
    last_effective_mode = None
    last_recommended_mode = None

    for time_minute in range(
        0,
        config.simulation.duration_minutes + config.simulation.step_minutes,
        config.simulation.step_minutes,
    ):
        controller.step_override_timer(config.simulation.step_minutes)
        scheduled_mode = scheduled_mode_for_time(time_minute, config.mode_schedule)
        effective_mode = controller.select_mode(scheduled_mode)
        environment = get_environment(time_minute, config.simulation)

        if last_effective_mode != effective_mode.value:
            events.append(
                Event(
                    time_minute=time_minute,
                    category="mode_change",
                    message=f"Vehicle entered {effective_mode.value} mode.",
                    metadata={
                        "scheduled_mode": scheduled_mode.value,
                        "effective_mode": effective_mode.value,
                    },
                )
            )
            last_effective_mode = effective_mode.value

        combined_effect = FaultEffect()
        active_faults: list[str] = []
        for fault in fault_models:
            activated, cleared = fault.active_transition(time_minute)
            if activated:
                events.append(
                    Event(
                        time_minute=time_minute,
                        category="fault_activated",
                        message=f"Fault '{fault.config.name}' became active.",
                        metadata={"fault_name": fault.config.name, "fault_type": fault.config.type},
                    )
                )
            if cleared:
                events.append(
                    Event(
                        time_minute=time_minute,
                        category="fault_cleared",
                        message=f"Fault '{fault.config.name}' cleared.",
                        metadata={"fault_name": fault.config.name, "fault_type": fault.config.type},
                    )
                )
            if not fault.is_active(time_minute):
                continue

            active_faults.append(fault.config.type)
            effect = fault.effect(time_minute)
            combined_effect.solar_scale *= effect.solar_scale
            combined_effect.battery_capacity_scale *= effect.battery_capacity_scale
            combined_effect.extra_load_w += effect.extra_load_w
            combined_effect.thermal_bias_w += effect.thermal_bias_w
            combined_effect.temperature_sensor_bias_c += effect.temperature_sensor_bias_c
            combined_effect.soc_sensor_bias_pct += effect.soc_sensor_bias_pct
            combined_effect.wheel_bias_rpm_per_min += effect.wheel_bias_rpm_per_min
            combined_effect.heater_forced_on = combined_effect.heater_forced_on or effect.heater_forced_on
            if effect.temperature_sensor_stuck_c is not None:
                combined_effect.temperature_sensor_stuck_c = effect.temperature_sensor_stuck_c

        power_state = update_power_state(
            battery_energy_wh=battery_energy_wh,
            temperature_c=battery_temperature_c,
            mode=effective_mode,
            in_sunlight=environment.in_sunlight,
            solar_incidence=environment.solar_incidence,
            step_minutes=config.simulation.step_minutes,
            satellite=config.satellite,
            fault_effect=combined_effect,
        )
        battery_energy_wh = power_state.battery_energy_wh

        battery_temperature_c = update_temperature_c(
            current_temperature_c=battery_temperature_c,
            load_power_w=power_state.load_power_w,
            in_sunlight=environment.in_sunlight,
            solar_incidence=environment.solar_incidence,
            sink_temperature_c=environment.sink_temperature_c,
            heater_on=power_state.heater_commanded_on,
            step_minutes=config.simulation.step_minutes,
            satellite=config.satellite,
            fault_effect=combined_effect,
        )

        wheel_speed_rpm = update_wheel_speed_rpm(
            wheel_speed_rpm=wheel_speed_rpm,
            mode=effective_mode,
            step_minutes=config.simulation.step_minutes,
            satellite=config.satellite,
            fault_effect=combined_effect,
        )

        sensor_temperature_c = (
            combined_effect.temperature_sensor_stuck_c
            if combined_effect.temperature_sensor_stuck_c is not None
            else battery_temperature_c + combined_effect.temperature_sensor_bias_c
        )
        sensor_soc_pct = max(0.0, min(100.0, power_state.battery_soc_pct + combined_effect.soc_sensor_bias_pct))

        expected_mode_load = mode_load_w(effective_mode, config.satellite)
        expected_solar_power = (
            config.satellite.solar_array_max_power_w * environment.solar_incidence
            if environment.in_sunlight
            else 0.0
        )
        telemetry_for_fdir = {
            "in_sunlight": environment.in_sunlight,
            "solar_power_w": power_state.solar_power_w,
            "load_power_w": power_state.load_power_w,
            "net_power_w": power_state.net_power_w,
            "sensor_soc_pct": sensor_soc_pct,
            "sensor_temperature_c": sensor_temperature_c,
            "wheel_speed_rpm": wheel_speed_rpm,
            "expected_solar_power_w": expected_solar_power,
        }
        diagnosis = controller.evaluate(
            telemetry=telemetry_for_fdir,
            expected_mode_load_w=expected_mode_load,
            satellite=config.satellite,
            solar_incidence=environment.solar_incidence,
            sink_temperature_c=environment.sink_temperature_c,
            heater_on=power_state.heater_commanded_on,
            step_minutes=config.simulation.step_minutes,
        )

        sample = TelemetrySample(
            time_minute=time_minute,
            orbit_phase=environment.orbit_phase,
            in_sunlight=environment.in_sunlight,
            solar_incidence=environment.solar_incidence,
            scheduled_mode=scheduled_mode,
            effective_mode=effective_mode,
            battery_soc_pct=power_state.battery_soc_pct,
            battery_temperature_c=battery_temperature_c,
            bus_voltage_v=power_state.bus_voltage_v,
            solar_power_w=power_state.solar_power_w,
            load_power_w=power_state.load_power_w,
            net_power_w=power_state.net_power_w,
            wheel_speed_rpm=wheel_speed_rpm,
            sensor_temperature_c=sensor_temperature_c,
            sensor_soc_pct=sensor_soc_pct,
            expected_temperature_c=diagnosis.expected_temperature_c,
            temperature_residual_c=diagnosis.temperature_residual_c,
            active_faults=active_faults,
            alerts=diagnosis.alerts,
            isolated_fault=diagnosis.isolated_fault,
            isolation_confidence=diagnosis.confidence,
            recommended_mode=diagnosis.recommended_mode,
            recovery_actions=diagnosis.actions,
        )
        telemetry.append(sample)

        signature = controller.signature_for(diagnosis)
        if diagnosis.alerts and controller.last_signature != signature:
            events.append(
                Event(
                    time_minute=time_minute,
                    category="fdir_detection",
                    message="FDIR detected an anomaly signature.",
                    metadata={
                        "alerts": ",".join(diagnosis.alerts),
                        "isolated_fault": diagnosis.isolated_fault or "",
                        "confidence": round(diagnosis.confidence, 3),
                    },
                )
            )
            controller.last_signature = signature
        if not diagnosis.alerts:
            controller.last_signature = None

        current_recommended_mode = diagnosis.recommended_mode.value if diagnosis.recommended_mode else None
        if current_recommended_mode is not None and current_recommended_mode != last_recommended_mode:
            events.append(
                Event(
                    time_minute=time_minute,
                    category="recovery_action",
                    message=f"FDIR recommended {diagnosis.recommended_mode.value} mode.",
                    metadata={
                        "recommended_mode": diagnosis.recommended_mode.value,
                        "actions": ",".join(diagnosis.actions),
                    },
                )
            )
        last_recommended_mode = current_recommended_mode

    result = ScenarioResult(
        scenario_name=config.scenario_name,
        description=config.description,
        telemetry=telemetry,
        events=events,
        summary={},
    )
    result.summary = summarize_result(result)

    if save_outputs and output_dir is not None:
        save_summary_outputs(result, output_dir)
    if save_plots and output_dir is not None:
        save_all_plots(result, output_dir)

    return result
