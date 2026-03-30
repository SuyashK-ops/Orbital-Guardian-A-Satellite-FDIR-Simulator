from __future__ import annotations

import json
from pathlib import Path

from ..types import ScenarioResult


def summarize_result(result: ScenarioResult) -> dict[str, object]:
    telemetry = result.telemetry
    events = result.events
    if not telemetry:
        return {"scenario_name": result.scenario_name, "status": "no_data"}

    step_minutes = telemetry[1].time_minute - telemetry[0].time_minute if len(telemetry) > 1 else 0
    safe_mode_minutes = sum(
        step_minutes for sample in telemetry if sample.effective_mode.value == "safe"
    )
    charging_minutes = sum(
        step_minutes for sample in telemetry if sample.effective_mode.value == "charging"
    )
    degraded_minutes = sum(
        step_minutes for sample in telemetry if sample.effective_mode.value == "degraded"
    )
    false_alarm_minutes = sum(
        step_minutes
        for sample in telemetry
        if sample.isolated_fault not in {None, "", "unknown_anomaly"} and not sample.active_faults
    )

    fault_start_times = {
        str(event.metadata.get("fault_type", event.metadata.get("fault_name", ""))): event.time_minute
        for event in events
        if event.category == "fault_activated"
    }
    detection_delays: dict[str, int] = {}
    for event in events:
        if event.category != "fdir_detection":
            continue
        identified = str(event.metadata.get("isolated_fault", ""))
        if not identified or identified == "unknown_anomaly":
            continue
        for fault_key, start_time in fault_start_times.items():
            if identified == fault_key:
                detection_delays.setdefault(fault_key, event.time_minute - start_time)

    final_sample = telemetry[-1]
    recovery_success = (
        final_sample.battery_soc_pct > 30.0
        and final_sample.battery_temperature_c < 35.0
        and abs(final_sample.wheel_speed_rpm) < 4200.0
    )

    return {
        "scenario_name": result.scenario_name,
        "description": result.description,
        "duration_minutes": telemetry[-1].time_minute,
        "minimum_soc_pct": round(min(sample.battery_soc_pct for sample in telemetry), 3),
        "maximum_temperature_c": round(max(sample.battery_temperature_c for sample in telemetry), 3),
        "maximum_sensor_temperature_c": round(max(sample.sensor_temperature_c for sample in telemetry), 3),
        "maximum_wheel_speed_rpm": round(max(abs(sample.wheel_speed_rpm) for sample in telemetry), 3),
        "safe_mode_minutes": safe_mode_minutes,
        "charging_mode_minutes": charging_minutes,
        "degraded_mode_minutes": degraded_minutes,
        "false_alarm_minutes": false_alarm_minutes,
        "fault_detection_delays_min": detection_delays,
        "recovery_success": recovery_success,
        "event_count": len(events),
    }


def save_summary_outputs(result: ScenarioResult, output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json = output_dir / "summary.json"
    summary_md = output_dir / "summary.md"
    events_json = output_dir / "events.json"
    telemetry_csv = output_dir / "telemetry.csv"

    summary_json.write_text(json.dumps(result.summary, indent=2), encoding="utf-8")

    markdown_lines = [
        f"# Scenario Summary: {result.scenario_name}",
        "",
        result.description,
        "",
        "## Key Metrics",
    ]
    for key, value in result.summary.items():
        markdown_lines.append(f"- **{key}**: {value}")
    summary_md.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    events_payload = [
        {
            "time_minute": event.time_minute,
            "category": event.category,
            "message": event.message,
            "metadata": event.metadata,
        }
        for event in result.events
    ]
    events_json.write_text(json.dumps(events_payload, indent=2), encoding="utf-8")

    headers = list(result.telemetry[0].as_dict().keys())
    rows = [sample.as_dict() for sample in result.telemetry]
    csv_lines = [",".join(headers)]
    for row in rows:
        csv_lines.append(",".join(str(row[header]) for header in headers))
    telemetry_csv.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    return [summary_json, summary_md, events_json, telemetry_csv]
