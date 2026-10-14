from pathlib import Path

import pandas as pd

from .devices import DeviceManager
from .memory import MemoryManager
from .schedulers import CPU_Scheduler
from .services.data_loader import DataLoader


# Carrega os dados e executa os algoritmos escolhidos.
def main(
    processes_path: Path,
    memory_references: pd.DataFrame,
    access_control_list_path: Path,
    devices_path: Path,
    cpu_method: CPU_Scheduler.Methods,
    memory_method: MemoryManager.Methods,
    memory_capacity: int = 4,
    quantum: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    processes = DataLoader.read_dataframe(processes_path)
    access_control_list = DataLoader.read_dataframe(access_control_list_path)
    devices = DataLoader.read_dataframe(devices_path)

    cpu_algorithms = {
        CPU_Scheduler.Methods.FCFS: CPU_Scheduler.first_come_first_served,
        CPU_Scheduler.Methods.SJF: CPU_Scheduler.shortest_job_first,
        CPU_Scheduler.Methods.PRIORITY: CPU_Scheduler.priority_order,
        CPU_Scheduler.Methods.ROUND_ROBIN: CPU_Scheduler.round_robin,
    }
    cpu_algorithm = cpu_algorithms[cpu_method]

    if cpu_method is CPU_Scheduler.Methods.ROUND_ROBIN:
        cpu_schedule = cpu_algorithm(processes, quantum=quantum)
    else:
        cpu_schedule = cpu_algorithm(processes)

    memory_algorithms = {
        MemoryManager.Methods.FIFO: MemoryManager.first_in_first_out,
        MemoryManager.Methods.LRU: MemoryManager.least_recently_used,
        MemoryManager.Methods.OPTIMAL: MemoryManager.optimal,
    }
    memory_algorithm = memory_algorithms[memory_method]
    memory_schedule = memory_algorithm(memory_references, memory_capacity)

    device_schedule = DeviceManager.scheduler(
        cpu_schedule,
        access_control_list,
        devices,
    )

    return cpu_schedule, memory_schedule, device_schedule
