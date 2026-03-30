# Architecture Notes

## System Intent

Orbital Guardian is organized around a simple but credible separation between the spacecraft plant, the fault layer, and the FDIR controller:

```text
scenario config
    -> simulation engine
        -> environment model
        -> subsystem models
        -> fault effects
        -> telemetry stream
        -> FDIR evaluation
        -> event log + outputs
```

This matters because it keeps the code extensible in the same way real flight and test software usually has to be extensible.

## Main Components

### `config.py`

Defines typed scenario configuration:

- simulation settings
- satellite parameters
- mode schedule
- injected faults
- FDIR thresholds

The config-driven approach is important for GitHub progress because each new scenario can be added as a small, visible commit.

### `environment.py`

Provides the orbital operating context for each time step:

- sunlight or eclipse
- solar incidence factor
- thermal sink temperature

This is intentionally lightweight, but it still captures the mission-relevant fact that orbit phase drives both power and thermal behavior.

### `subsystems/`

Contains independent first-order subsystem models.

- `power.py`
  Battery energy, bus voltage, solar power, and load power
- `thermal.py`
  Internal heating, solar heating, eclipse cooling, and heater behavior
- `attitude.py`
  Reaction-wheel speed proxy with disturbance accumulation and mode-dependent desaturation

### `faults/library.py`

Maps fault definitions from config into fault models that alter either physical behavior or telemetry.

This split is deliberate:

- some faults affect the plant itself
- some faults affect the measurements
- some faults affect both

That distinction is central to real FDIR work because the spacecraft may be healthy while the telemetry is lying, or vice versa.

### `fdir/logic.py`

Implements a rule-based controller with three steps:

1. detect suspicious conditions
2. isolate a likely fault family with heuristic scoring
3. choose a recovery mode and action list

The controller also manages temporary mode overrides so the recovery action can affect future time steps.

### `simulation.py`

Acts as the orchestration layer:

1. load the scenario
2. determine scheduled and effective mode
3. collect active fault effects
4. propagate subsystem state
5. synthesize telemetry
6. run FDIR
7. log events
8. assemble summary outputs

## Modeling Assumptions

The project currently uses the following simplifications:

- one thermal node
- one battery state variable
- orbit phase represented as repeating sunlight/eclipse windows
- wheel speed used as an attitude-control stress indicator
- deterministic rules instead of stochastic uncertainty propagation

These are acceptable for an early portfolio version because they preserve the engineering logic without hiding it under excessive fidelity.

## Design Choices That Reflect Systems Thinking

- `Mode-aware loads`
  The spacecraft does not consume the same power in science mode as in safe mode.
- `Telemetry vs truth separation`
  Sensor faults can bias readings without changing the actual plant state.
- `FDIR uncertainty handling`
  The system can escalate an unknown anomaly instead of pretending to know the exact cause.
- `Config-driven fault injection`
  Scenarios are testable and reproducible.
- `Outputs for analysis`
  Telemetry, events, summaries, and plots are all treated as first-class artifacts.

## Near-Term Improvements

- recovery hysteresis and persistence logic
- better detection-delay accounting and fault attribution
- subsystem health states with latching logic
- scenario batch runner for performance metrics
- explicit command constraints and recovery cooldowns
