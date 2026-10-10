from collections import deque
from copy import deepcopy
from enum import Enum

from services.data_loader import DataLoader


# Classe que recebe uma lista de processos e ordena, retornando uma sequencia de escalonamento da cpu a cada ciclo
class CPU_Scheduler:
    def __init__(self, uri: str):
        self.processes_list = DataLoader().processes(uri)

    # Métodos da Classe
    class Methods(Enum):
        FCFS = "__first_come_first_served"
        SJF = "__shortest_job_first"
        PRIORITY = "__priority_order"
        ROUND_ROBIN = "__round_robin"

    def execute(self, method: Methods, *args, **kwargs) -> list[dict]:
        real_method = getattr(self, method.value)
        return real_method(self.processes_list, *args, **kwargs)

    # Recebe a lista de processos ordenada e um limite (quantum) e retorna uma lista ciclo a ciclo
    def __order_processes(self, process_list: list[dict]) -> list[dict]:

        index = 0

        final_list: list[dict] = []

        for process in process_list:
            p = deepcopy(process)
            if "rounds_left" not in p:
                p["rounds_left"] = int(p["burst"])

            for i in range(int(p["rounds_left"])):
                index += 1
                p["rounds_left"] -= 1
                ciclo: dict = {index: p}
                final_list.append(ciclo)

        return final_list

    # Critério FCFS [ordem de chegada]
    def __first_come_first_served(self, processes: list[dict]) -> list[dict]:
        # Cria uma nova lista, ordenada, preservando a lista original
        sorted_processes = sorted(
            deepcopy(processes), key=lambda process: process["arrival"]
        )

        return self.__order_processes(sorted_processes)

    # Critério SJF [executa primeiro aquele que demanda memos ciclos]
    def __shortest_job_first(self, processes: list[dict]) -> list[dict]:
        sorted_processes = sorted(
            deepcopy(processes), key=lambda process: process["burst"]
        )

        return self.__order_processes(sorted_processes)

    # Critério Priority Order [executa por ordem de prioridade]
    def __priority_order(self, processes: list[dict]) -> list[dict]:
        sorted_processes = sorted(
            deepcopy(processes), key=lambda process: process["priority"]
        )

        return self.__order_processes(sorted_processes)

    # Critério Round Robin com Quantum padrão de 3 [igual a FCFS, mas limita o tempo de uso de CPU ao Quantum]
    def __round_robin(self, processes: list[dict], quantum=3) -> list[dict]:
        sorted_processes = sorted(
            deepcopy(processes), key=lambda process: process["arrival"]
        )

        queue = deque(sorted_processes)

        process_list: list[dict] = []

        index = 0

        if quantum <= 0:
            return process_list

        while queue:
            process = queue.popleft()

            if "rounds_left" not in process:
                process["rounds_left"] = int(process["burst"])

            cycles_to_run = min(quantum, process["rounds_left"])

            for _ in range(cycles_to_run):
                index += 1
                process["rounds_left"] -= 1
                process_list.append({index: process.copy()})

            if process["rounds_left"] > 0:
                queue.append(process)

        return process_list
