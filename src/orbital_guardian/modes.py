from __future__ import annotations

from .config import ModeScheduleEntry
from .types import OperationMode


def scheduled_mode_for_time(
    time_minute: int,
    schedule: list[ModeScheduleEntry],
) -> OperationMode:
    selected = schedule[0].mode if schedule else OperationMode.NOMINAL
    for entry in schedule:
        if time_minute >= entry.start_minute:
            selected = entry.mode
        else:
            break
    return selected
