from collections import deque
from enum import Enum

import pandas as pd


# Classe que recebe uma lista de processos e ordena, retornando uma sequencia de escalonamento da cpu a cada ciclo
class CPU_Scheduler:
    # Métodos da Classe
    class Methods(Enum):
        FCFS = "first_come_first_served"
        SJF = "shortest_job_first"
        PRIORITY = "priority_order"
        ROUND_ROBIN = "round_robin"

    # Recebe a lista de processos ordenada e um limite (quantum) e retorna uma lista ciclo a ciclo
    @staticmethod
    def __order_processes(
        processes_df: pd.DataFrame, round_robin: bool = False, quantum: int = 3
    ) -> pd.DataFrame:

        columns = ["cycle", *processes_df.columns, "cycles_left"]

        # Trata erros, devolvendo um DF vazio
        if processes_df.empty or (round_robin and quantum <= 0):
            return pd.DataFrame(columns=columns)

        processes = processes_df.to_dict(orient="records")
        rows = []
        cycle = 0

        # Distribuição dos processo segundo o método 'Round Robin'
        if round_robin:
            queue = deque(processes)

            while queue:
                process = queue.popleft()
                cycles_left = int(process.get("cycles_left", process["burst"]))
                cycles_to_run = min(quantum, cycles_left)

                for _ in range(cycles_to_run):
                    cycle += 1
                    cycles_left -= 1
                    rows.append(
                        {
                            "cycle": cycle,
                            **process,
                            "cycles_left": cycles_left,
                        }
                    )

                if cycles_left > 0:
                    process["cycles_left"] = cycles_left
                    queue.append(process)

        # Distribuição dos processos  para os demais métodos
        else:
            for process in processes:
                cycles_left = int(process["burst"])

                for _ in range(cycles_left):
                    cycle += 1
                    cycles_left -= 1
                    rows.append(
                        {
                            "cycle": cycle,
                            **process,
                            "cycles_left": cycles_left,
                        }
                    )

        return pd.DataFrame(rows, columns=columns)

    # Critério FCFS [ordem de chegada]
    @staticmethod
    def first_come_first_served(processes_df: pd.DataFrame) -> pd.DataFrame:
        # Define os critérios de ordenamento e desempate
        processes = processes_df.sort_values(
            by=["arrival", "priority", "burst"], kind="stable"
        )

        return CPU_Scheduler.__order_processes(processes)

    # Critério SJF [executa primeiro aquele que demanda memos ciclos]
    @staticmethod
    def shortest_job_first(processes_df: pd.DataFrame) -> pd.DataFrame:
        # Define os critérios de ordenamento e desempate
        processes = processes_df.sort_values(
            by=["burst", "priority", "arrival"], kind="stable"
        )

        return CPU_Scheduler.__order_processes(processes)

    # Critério Priority Order [executa por ordem de prioridade]
    @staticmethod
    def priority_order(processes_df: pd.DataFrame) -> pd.DataFrame:
        # Define os critérios de ordenamento e desempate
        processes = processes_df.sort_values(
            by=["priority", "arrival", "burst"], kind="stable"
        )

        return CPU_Scheduler.__order_processes(processes)

    # Critério Round Robin com Quantum padrão de 3 [igual a FCFS, mas limita o tempo de uso de CPU ao Quantum]
    @staticmethod
    def round_robin(processes_df: pd.DataFrame, quantum: int = 3) -> pd.DataFrame:
        # Define os critérios de ordenamento e desempate
        processes = processes_df.sort_values(
            by=["arrival", "priority", "burst"], kind="stable"
        )

        return CPU_Scheduler.__order_processes(
            processes, round_robin=True, quantum=quantum
        )
