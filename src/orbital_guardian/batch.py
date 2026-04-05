from __future__ import annotations

import json
from pathlib import Path

from .config import load_scenario_config
from .simulation import run_scenario
from .types import ScenarioResult


def _normalize_name(value: str) -> str:
    return value.lower().replace(" ", "_")


def run_scenario_directory(
    config_dir: str | Path,
    output_dir: str | Path,
    save_plots: bool = False,
) -> list[ScenarioResult]:
    config_dir = Path(config_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_paths = sorted(config_dir.glob("*.json"))
    if not config_paths:
        raise FileNotFoundError(f"No scenario JSON files found in '{config_dir}'.")

    results: list[ScenarioResult] = []
    for config_path in config_paths:
        config = load_scenario_config(config_path)
        scenario_output_dir = output_dir / _normalize_name(config.scenario_name)
        result = run_scenario(
            config,
            output_dir=scenario_output_dir,
            save_plots=save_plots,
            save_outputs=True,
        )
        results.append(result)

    save_comparison_outputs(results, output_dir)
    return results


def save_comparison_outputs(results: list[ScenarioResult], output_dir: str | Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_json = output_dir / "comparison.json"
    comparison_csv = output_dir / "comparison.csv"

    rows = [result.summary for result in results]
    comparison_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    if rows:
        headers = list(rows[0].keys())
        csv_lines = [",".join(headers)]
        for row in rows:
            csv_lines.append(",".join(_csv_value(row.get(header, "")) for header in headers))
        comparison_csv.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    return [comparison_json, comparison_csv]


def _csv_value(value: object) -> str:
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return str(value)
