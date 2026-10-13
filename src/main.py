from pathlib import Path

import pandas as pd

from .devices import DeviceManager
from .memory import MemoryManager
from .schedulers import CPU_Scheduler
from .services.data_loader import DataLoader


def main(
    processes_json: str | Path,
    memory_references_json: str | Path | pd.DataFrame,
    access_control_list_json: str | Path,
    devices_json: str | Path,
    cpu_method: CPU_Scheduler.Methods,
    memory_method: MemoryManager.Methods,
    memory_capacity: int = 4,
    quantum: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    processes = DataLoader.read_dataframe(processes_json)
    if isinstance(memory_references_json, pd.DataFrame):
        memory_references = memory_references_json
    else:
        memory_references = DataLoader.read_dataframe(memory_references_json)
    access_control_list = DataLoader.read_dataframe(access_control_list_json)
    devices = DataLoader.read_dataframe(devices_json)

    cpu_algorithm = getattr(CPU_Scheduler, cpu_method.value)

    if cpu_method is CPU_Scheduler.Methods.ROUND_ROBIN:
        cpu_schedule = cpu_algorithm(processes, quantum=quantum)
    else:
        cpu_schedule = cpu_algorithm(processes)

    memory_algorithm = getattr(MemoryManager, memory_method.value)
    memory_schedule = memory_algorithm(memory_references, memory_capacity)

    devices_schedule = DeviceManager.scheduler(
        cpu_schedule,
        access_control_list,
        devices,
    )

    return cpu_schedule, memory_schedule, devices_schedule
