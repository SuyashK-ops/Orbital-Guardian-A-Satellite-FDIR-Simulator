# Orbital Guardian

Orbital Guardian is a portfolio-oriented small-satellite Fault Detection, Isolation, and Recovery (FDIR) simulator. The project is intentionally scoped as a realistic systems-engineering exercise rather than a high-fidelity mission tool: it models coupled power, thermal, and attitude-related behavior over time; injects subsystem faults through configuration; and applies rule-based FDIR logic to decide when the spacecraft should degrade gracefully, enter charging mode, or fall back to safe mode.

The goal is to show aerospace systems thinking in code:

- satellite subsystems interact and compete for limited resources
- nominal telemetry thresholds are not enough on their own
- detection, isolation, and recovery are distinct engineering functions
- autonomy has tradeoffs around uncertainty, robustness, and false positives
- operational modes matter because spacecraft do not respond to all anomalies the same way

## What This MVP Already Does

- simulates a small satellite in discrete time steps
- models sunlight/eclipse cycling with orbit-phase-dependent solar generation
- tracks battery state of charge, bus voltage, thermal state, and reaction-wheel speed
- supports mission mode scheduling across `nominal`, `science`, `charging`, `degraded`, and `safe`
- injects faults from JSON scenario files
- runs a lightweight rule-based FDIR controller
- logs fault activations, mode changes, detections, and recovery actions
- exports telemetry, event logs, and scenario summaries
- optionally generates portfolio-ready plots
- includes notebooks for exploratory runs and scenario comparison

## Repository Layout

```text
configs/                  Scenario definitions for nominal and faulted runs
docs/                     Architecture notes and staged roadmap
notebooks/                Main analysis and demo notebooks
src/orbital_guardian/     Simulator package
tests/                    Baseline regression tests
outputs/                  Generated plots, telemetry, and summaries
```

## Engineering Scope

This project uses simplified but purposeful models:

- `Power subsystem`: solar generation, eclipse losses, load variation by mode, battery charge/discharge
- `Thermal subsystem`: first-order energy balance with internal electrical heating, solar heating, eclipse cooling, and heater behavior
- `Attitude / operations`: reaction-wheel speed proxy, disturbance accumulation, mode-dependent momentum unloading
- `Fault models`: degradations and anomalies that affect generation, load, thermal behavior, sensors, and wheel dynamics
- `FDIR`: alerting, heuristic isolation, and autonomous recovery recommendations

It is not attempting full orbital mechanics, full rigid-body attitude dynamics, electrochemistry, or radiation transport. The point is to build a serious systems project that is transparent, extensible, and defensible in an interview.

## Quick Start

### 1. Run from the CLI

From the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m orbital_guardian.cli --config configs/nominal.json --output-dir outputs/nominal --skip-plots
```

To generate plots as well, install `matplotlib` and remove `--skip-plots`.

### 2. Work from notebooks

Open one of the notebooks in `notebooks/`:

- `01_baseline_simulator.ipynb`
- `02_fdir_scenario_comparison.ipynb`

These notebooks are meant to be the main presentation layer for GitHub screenshots, portfolio walkthroughs, and future iteration.

## Scenario Files

Scenario configuration is JSON-based so the repo can grow through small, meaningful commits. Example scenarios included right now:

- `configs/nominal.json`: baseline reference mission
- `configs/power_fault.json`: solar degradation plus unexpected power draw
- `configs/thermal_sensor_fault.json`: sensor drift plus heater fault
- `configs/fdir_demo.json`: combined multi-fault demonstration

Each scenario can define:

- simulation duration, step size, orbit period, and sunlight fraction
- scheduled mission modes
- subsystem parameters
- FDIR thresholds
- a list of injected faults with start times and parameters

## Current Fault Library

- `solar_array_degradation`
- `battery_degradation`
- `temperature_sensor_drift`
- `temperature_sensor_stuck`
- `reaction_wheel_anomaly`
- `heater_stuck_on`
- `load_spike`

## FDIR Philosophy In This Project

The current FDIR layer is deliberately lightweight but structured like a real early-phase autonomy design:

1. `Detection`
   Looks for suspicious patterns such as low state of charge, underperforming solar generation, power deficit, thermal limit exceedance, wheel-speed growth, or sensor residuals.
2. `Isolation`
   Uses heuristic scoring to estimate the most likely fault family rather than assuming a single threshold tells the whole story.
3. `Recovery`
   Recommends a mode response:
   `charging` for power stress, `degraded` for uncertain sensor issues, and `safe` for critical thermal, wheel, or energy conditions.

That separation matters. A spacecraft can detect that something is wrong without knowing exactly why, and it can still choose a conservative recovery action while uncertainty remains.

## Recommended Development Roadmap

This repo is intentionally built to support milestone-style growth rather than one giant dump of functionality:

1. `Phase 1`
   Baseline simulator and telemetry outputs
2. `Phase 2`
   Expand the fault library and scenario coverage
3. `Phase 3`
   Improve FDIR with persistence logic, confidence handling, and better residual models
4. `Phase 4`
   Add batch scenario evaluation and quantitative performance metrics
5. `Phase 5`
   Polish documentation, tests, diagrams, logging, and presentation assets

More detail lives in [docs/roadmap.md](docs/roadmap.md).
