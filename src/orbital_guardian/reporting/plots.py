from __future__ import annotations

from pathlib import Path

from ..types import ScenarioResult


def _require_matplotlib():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Plot generation requires matplotlib. Install the optional 'viz' dependency first."
        ) from exc
    return plt


def save_timeseries_plot(result: ScenarioResult, output_dir: str | Path) -> Path:
    plt = _require_matplotlib()
    output_path = Path(output_dir) / "timeseries.png"

    times = [sample.time_minute for sample in result.telemetry]
    soc = [sample.battery_soc_pct for sample in result.telemetry]
    solar = [sample.solar_power_w for sample in result.telemetry]
    load = [sample.load_power_w for sample in result.telemetry]
    temp = [sample.battery_temperature_c for sample in result.telemetry]
    temp_sensor = [sample.sensor_temperature_c for sample in result.telemetry]
    wheel = [sample.wheel_speed_rpm for sample in result.telemetry]

    figure, axes = plt.subplots(4, 1, figsize=(13, 11), sharex=True)
    axes[0].plot(times, soc, color="#1b4d8c", linewidth=2)
    axes[0].set_ylabel("Battery SoC [%]")
    axes[0].grid(alpha=0.3)

    axes[1].plot(times, solar, label="Solar generation", color="#2a9d8f", linewidth=2)
    axes[1].plot(times, load, label="Load demand", color="#e76f51", linewidth=2)
    axes[1].set_ylabel("Power [W]")
    axes[1].legend(loc="upper right")
    axes[1].grid(alpha=0.3)

    axes[2].plot(times, temp, label="Actual temperature", color="#c1121f", linewidth=2)
    axes[2].plot(times, temp_sensor, label="Sensor temperature", color="#f4a261", linewidth=1.5, linestyle="--")
    axes[2].set_ylabel("Temperature [C]")
    axes[2].legend(loc="upper right")
    axes[2].grid(alpha=0.3)

    axes[3].plot(times, wheel, color="#6a4c93", linewidth=2)
    axes[3].set_ylabel("Wheel speed [rpm]")
    axes[3].set_xlabel("Mission elapsed time [min]")
    axes[3].grid(alpha=0.3)

    figure.suptitle(f"Orbital Guardian Scenario: {result.scenario_name}")
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return output_path


def save_timeline_plot(result: ScenarioResult, output_dir: str | Path) -> Path:
    plt = _require_matplotlib()
    output_path = Path(output_dir) / "timeline.png"

    times = [sample.time_minute for sample in result.telemetry]
    mode_map = {
        "nominal": 4,
        "science": 3,
        "degraded": 2,
        "charging": 1,
        "safe": 0,
    }
    mode_values = [mode_map[sample.effective_mode.value] for sample in result.telemetry]
    alert_counts = [len(sample.alerts) for sample in result.telemetry]

    figure, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    axes[0].step(times, mode_values, where="post", color="#264653", linewidth=2)
    axes[0].set_yticks([0, 1, 2, 3, 4], labels=["safe", "charging", "degraded", "science", "nominal"])
    axes[0].set_ylabel("Mode")
    axes[0].grid(alpha=0.3)

    axes[1].step(times, alert_counts, where="post", color="#d62828", linewidth=2)
    axes[1].set_ylabel("Alert count")
    axes[1].set_xlabel("Mission elapsed time [min]")
    axes[1].grid(alpha=0.3)

    for event in result.events:
        if event.category == "fault_activated":
            for axis in axes:
                axis.axvline(event.time_minute, color="#f77f00", linestyle="--", alpha=0.6)

    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return output_path


def save_all_plots(result: ScenarioResult, output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        save_timeseries_plot(result, output_dir),
        save_timeline_plot(result, output_dir),
    ]

