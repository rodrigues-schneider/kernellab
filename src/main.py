import pandas as pd

from devices import DeviceManager
from memory import MemoryManager
from schedulers import CPU_Scheduler
from services.data_loader import DataLoader


def main(
    processes_json: str,
    memory_references_json: str,
    access_control_list_json: str,
    devices_json: str,
    cpu_method: CPU_Scheduler.Methods,
    memory_method: MemoryManager.Methods,
    memory_capacity: int = 4,
    quantum: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    process_file: str = "../data/cpu/" + processes_json
    memory_file: str = "../data/memory" + memory_references_json
    acl_file: str = "../data/access_control" + access_control_list_json
    devices_file: str = "../data/devices" + devices_json

    processes = DataLoader.read_dataframe(process_file)
    memory_references_json = DataLoader.read_dataframe(memory_file)
    access_control_list_json = DataLoader.read_dataframe(acl_file)
    devices_json = DataLoader.read_dataframe(devices_file)

    cpu_algorithm = getattr(CPU_Scheduler, cpu_method.value)

    if cpu_method is CPU_Scheduler.Methods.ROUND_ROBIN:
        cpu_schedule = cpu_algorithm(processes, quantum=quantum)
    else:
        cpu_schedule = cpu_algorithm(processes)

    memory_algorithm = getattr(MemoryManager, memory_method.value)
    memory_schedule = memory_algorithm(memory_references_json, memory_capacity)

    devices_schedule = DeviceManager.scheduler(
        cpu_schedule,
        access_control_list_json,
        devices_json,
    )

    return cpu_schedule, memory_schedule, devices_schedule
