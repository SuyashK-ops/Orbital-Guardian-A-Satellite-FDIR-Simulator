from __future__ import annotations

import argparse
from pathlib import Path

from .simulation import run_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Orbital Guardian FDIR scenarios.")
    parser.add_argument("--config", required=True, help="Path to a scenario JSON file.")
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
