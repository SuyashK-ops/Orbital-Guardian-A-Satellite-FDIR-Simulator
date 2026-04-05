from __future__ import annotations

import argparse
from pathlib import Path

from .batch import run_scenario_directory
from .simulation import run_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Orbital Guardian FDIR scenarios.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--config", help="Path to a scenario JSON file.")
    target_group.add_argument(
        "--config-dir",
        help="Directory containing scenario JSON files to run as a batch.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/latest_run",
        help="Directory for plots, telemetry, and summary outputs.",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Run the scenario without generating matplotlib plots.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if args.config_dir:
        results = run_scenario_directory(
            args.config_dir,
            output_dir=output_dir,
            save_plots=not args.skip_plots,
        )
        print(f"Batch completed: {len(results)} scenarios")
        print(f"Outputs written to: {output_dir.resolve()}")
        print("Scenario summaries:")
        for result in results:
            print(
                f"- {result.scenario_name}: recovery_success={result.summary['recovery_success']}, "
                f"safe_mode_minutes={result.summary['safe_mode_minutes']}, "
                f"false_alarm_minutes={result.summary['false_alarm_minutes']}"
            )
        return

    result = run_scenario(
        args.config,
        output_dir=output_dir,
        save_plots=not args.skip_plots,
        save_outputs=True,
    )
    print(f"Scenario: {result.scenario_name}")
    print(f"Summary written to: {output_dir.resolve()}")
    for key, value in result.summary.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
