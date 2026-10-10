from devices import DeviceManager
from services.data_loader import DataLoader
from memory import MemoryManager
from schedulers import CPU_Scheduler


def main(
    processes_uri: str,
    cpu_schedule_method: CPU_Scheduler.Methods,
    memory_schedule_method: MemoryManager.Methods,
    memory_requering_sequency: list[str] | str,
):

    loader = DataLoader()
    cpu = CPU_Scheduler(processes_uri)
    cpu_schedule = cpu.execute(cpu_schedule_method)

    if isinstance(memory_requering_sequency, str):
        memory_requering_sequency = loader.load_memory_references(
            memory_requering_sequency
        )

    memory = MemoryManager()
    memory_schedule = memory.execute(memory_schedule_method, memory_requering_sequency)

    devices = DeviceManager(data_loader=loader)
    devices_schedule = devices.scheduler(cpu.processes_list)

    return cpu_schedule, memory_schedule, devices_schedule
