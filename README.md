# Orbital Guardian

Orbital Guardian is a small-satellite Fault Detection, Isolation, and Recovery (FDIR) simulator. It models simplified spacecraft power, thermal, and reaction-wheel behavior over time, injects configurable faults, and applies rule-based FDIR logic to detect anomalies, estimate likely causes, and trigger recovery responses such as charging mode or safe mode.

## Features

- time-stepped spacecraft simulation
- sunlight and eclipse cycling
- battery state-of-charge and bus power tracking
- first-order thermal model with heater behavior
- operational modes: `nominal`, `science`, `charging`, `degraded`, `safe`
- config-driven fault injection
- rule-based FDIR detection, isolation, and recovery
- telemetry export, event logs, summary files, and plots
- single-scenario and batch scenario execution from the CLI

## Repository Layout

```text
configs/                  Scenario definitions
docs/                     Architecture notes and roadmap
notebooks/                Main notebooks for running and comparing scenarios
outputs/                  Generated run artifacts
src/orbital_guardian/     Simulator package
tests/                    Automated tests
```

## Subsystem Scope

Current models include:

- `power`: solar generation, eclipse periods, battery charging/discharging, and mode-dependent loads
- `thermal`: first-order temperature response from internal loads, solar input, eclipse cooling, and heater effects
- `attitude / operations`: reaction-wheel speed proxy with disturbance accumulation and mode-dependent unloading
- `faults`: degradations and anomalies that affect generation, loads, telemetry, and wheel behavior
- `fdir`: detection rules, heuristic fault isolation, and recovery-mode selection

## Included Scenarios

- `configs/nominal.json`
  Baseline reference case with no injected faults.
- `configs/power_fault.json`
  Solar-array degradation and unexpected load increase.
- `configs/thermal_sensor_fault.json`
  Temperature sensor drift and heater fault case.
- `configs/fdir_demo.json`
  Combined multi-fault scenario.

## Requirements

- Python 3.11+
- `matplotlib` for plot generation and notebook plotting

Optional install from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m pip install matplotlib
```

## How To Run

Run a single scenario from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m orbital_guardian.cli --config configs/nominal.json --output-dir outputs/nominal
```

Run all scenario files in `configs/` as a batch:

```powershell
$env:PYTHONPATH = "src"
python -m orbital_guardian.cli --config-dir configs --output-dir outputs/batch_run --skip-plots
```

Use `--skip-plots` to skip image generation.

## Files To Open Or Run

- `src/orbital_guardian/cli.py`
  Main command-line entry point.
- `notebooks/01_baseline_simulator.ipynb`
  Baseline simulator walkthrough.
- `notebooks/02_fdir_scenario_comparison.ipynb`
  Scenario comparison notebook.
- `src/orbital_guardian/simulation.py`
  Main simulation loop.
- `src/orbital_guardian/fdir/logic.py`
  Detection, isolation, and recovery logic.
- `tests/test_simulation.py`
  Basic automated test coverage.

## Outputs

Single-scenario runs write files such as:

- `summary.json`
- `summary.md`
- `events.json`
- `telemetry.csv`
- `timeseries.png`
- `timeline.png`

Batch runs also write:

- `comparison.json`
- `comparison.csv`

## Fault Types

- `solar_array_degradation`
- `battery_degradation`
- `temperature_sensor_drift`
- `temperature_sensor_stuck`
- `reaction_wheel_anomaly`
- `heater_stuck_on`
- `load_spike`

## Limitations

- single-node thermal model
- simplified power subsystem dynamics
- reaction-wheel speed used as an operational proxy instead of full attitude dynamics
- rule-based FDIR instead of probabilistic or model-based diagnosis
- no command sequencing or hardware interface layer

## Documentation

- `docs/architecture.md`
- `docs/roadmap.md`
