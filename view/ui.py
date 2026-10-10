from pprint import pprint

from main import main
from memory import MemoryManager
from schedulers import CPU_Scheduler

uri: str = "../data/processes.json"
memory_method: MemoryManager.Methods = MemoryManager.Methods.FIFO
cpu_method: CPU_Scheduler.Methods = CPU_Scheduler.Methods.FCFS


main()
