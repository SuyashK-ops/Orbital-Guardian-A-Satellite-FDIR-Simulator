from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orbital_guardian.batch import run_scenario_directory  # noqa: E402
from orbital_guardian.config import (  # noqa: E402
    FDIRConfig,
    FaultConfig,
    ModeScheduleEntry,
    SatelliteConfig,
    ScenarioConfig,
    SimulationConfig,
)
from orbital_guardian.simulation import run_scenario  # noqa: E402
from orbital_guardian.types import OperationMode  # noqa: E402


class SimulationSmokeTests(unittest.TestCase):
    def test_nominal_short_run_stays_fault_free(self) -> None:
        config = ScenarioConfig(
            scenario_name="test_nominal",
            description="Short nominal regression.",
            simulation=SimulationConfig(duration_minutes=60, step_minutes=1),
            satellite=SatelliteConfig(),
            mode_schedule=[ModeScheduleEntry(start_minute=0, mode=OperationMode.NOMINAL)],
            faults=[],
            fdir=FDIRConfig(),
        )

        result = run_scenario(config)

        self.assertGreater(len(result.telemetry), 10)
        self.assertTrue(all(not sample.active_faults for sample in result.telemetry))
        self.assertGreaterEqual(min(sample.battery_soc_pct for sample in result.telemetry), 0.0)
        self.assertTrue(any(event.category == "scenario_start" for event in result.events))

    def test_load_spike_drives_protective_response(self) -> None:
        config = ScenarioConfig(
            scenario_name="test_power_fault",
            description="Regression scenario for recovery-mode activation.",
            simulation=SimulationConfig(duration_minutes=180, step_minutes=1),
            satellite=SatelliteConfig(initial_soc_pct=55.0),
            mode_schedule=[
                ModeScheduleEntry(start_minute=0, mode=OperationMode.NOMINAL),
                ModeScheduleEntry(start_minute=40, mode=OperationMode.SCIENCE),
            ],
            faults=[
                FaultConfig(
                    type="load_spike",
                    name="test_load_spike",
                    start_minute=60,
                    parameters={"extra_load_w": 30.0},
                )
            ],
            fdir=FDIRConfig(),
        )

        result = run_scenario(config)

        recommended_modes = {
            sample.recommended_mode.value
            for sample in result.telemetry
            if sample.recommended_mode is not None
        }

        self.assertIn("load_spike", {fault for sample in result.telemetry for fault in sample.active_faults})
        self.assertTrue({"charging", "safe"} & recommended_modes)
        self.assertTrue(any(event.category == "fault_activated" for event in result.events))

    def test_batch_runner_writes_comparison_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "batch_outputs"
            results = run_scenario_directory("configs", output_dir, save_plots=False)

            self.assertGreaterEqual(len(results), 4)
            self.assertTrue((output_dir / "comparison.json").exists())
            self.assertTrue((output_dir / "comparison.csv").exists())
            self.assertTrue(
                all((output_dir / result.scenario_name.lower().replace(" ", "_")).exists() for result in results)
            )


if __name__ == "__main__":
    unittest.main()
