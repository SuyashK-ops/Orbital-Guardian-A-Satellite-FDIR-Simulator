# Incremental Roadmap

This roadmap is meant to support steady GitHub progress. Each phase should feel like a real milestone, not filler.

## Phase 1: Baseline Simulator

Goal:
Build the time-stepped spacecraft plant and basic outputs.

Deliverables:

- orbit sunlight/eclipse cycling
- battery and bus power simulation
- thermal state propagation
- operational mode schedule
- telemetry export
- baseline notebook and README

Suggested commit sequence:

- `initial simulator skeleton`
- `power subsystem model added`
- `thermal dynamics added`
- `mode scheduling and telemetry export added`

## Phase 2: Fault Injection

Goal:
Make anomalies configurable and reproducible.

Deliverables:

- config-driven fault activation
- event logs for start time and type
- at least three meaningful fault families
- scenario comparison against nominal behavior

Suggested commit sequence:

- `fault model interface added`
- `solar array degradation fault added`
- `sensor drift fault added`
- `power spike and thermal fault scenarios added`

## Phase 3: Rule-Based FDIR

Goal:
Separate detection, isolation, and recovery.

Deliverables:

- alerting logic
- heuristic isolation scoring
- safe-mode and charging-mode responses
- uncertainty escalation when isolation is weak

Suggested commit sequence:

- `threshold detection added`
- `fault isolation heuristics added`
- `recovery mode overrides added`
- `event log and timeline plotting improved`

## Phase 4: Scenario Evaluation

Goal:
Quantify how well the autonomy behaves.

Deliverables:

- nominal vs faulted comparison
- detection delay metrics
- false-alarm tracking
- time in degraded or safe mode
- recovery success criteria

Suggested commit sequence:

- `scenario summary metrics added`
- `batch comparison notebook added`
- `detection delay reporting improved`

## Phase 5: Professional Polish

Goal:
Turn the simulator into a portfolio-ready engineering artifact.

Deliverables:

- unit tests
- architecture diagrams
- structured logging
- cleaner visual design
- saved example outputs
- refined documentation and assumptions

Suggested commit sequence:

- `tests for nominal and fault response added`
- `architecture docs and diagrams added`
- `saved example plots added`
- `readme polished for portfolio presentation`

## Longer-Horizon Stretch Goals

- probabilistic or Bayesian isolation
- state-estimator-based residual generation
- redundant sensor voting
- Monte Carlo campaign tooling
- command sequencing and onboard constraints
- more realistic ADCS and thermal zonal models
