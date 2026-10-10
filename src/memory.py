from collections import deque
from enum import Enum


# Recebe uma lista de requisições de memória e retorna o estado da memória a cada ciclo
class MemoryManager:
    def __init__(self):
        pass

    # Métodos da Classe
    class Methods(Enum):
        FIFO = "first_in_first_out"
        LRU = "least_recently_used"
        OPTIMAL = "optimal"

    def execute(
        self, method: Methods, processes: list[dict], *args, **kwargs
    ) -> list[dict]:
        real_method = getattr(self, method.value)
        return real_method(processes, *args, **kwargs)

    # Critério de ordem de chegada. A lista 'anda' a cada nova inserção
    def first_in_first_out(
        self, requiring_list: list[str], memory_capacity: int = 4
    ) -> list[dict]:

        memory: deque[str] = deque()

        final_list: list[dict] = []

        faults = 0

        hits = 0

        if memory_capacity <= 0:
            return final_list

        for index, frame in enumerate(requiring_list):
            page_hit = True

            if frame not in memory:
                faults += 1
                page_hit = False

                if len(memory) >= memory_capacity:
                    memory.pop()

                memory.appendleft(frame)  # Nova pagina adicionada ao inicio
            else:
                hits += 1

            final_list.append(
                {
                    index: {
                        "requested_page": frame,
                        "page_hit": str(page_hit),
                        "total_page_faults": faults,
                        "total_page_hits": hits,
                        "pages_in_memory": list(memory),
                    }
                }
            )

        return final_list

    # Critério de página há mais tempo sem requisição. A lista 'anda' a cada nova inserção
    def least_recently_used(
        self, requiring_list: list[str], memory_capacity: int = 4
    ) -> list[dict]:

        memory: deque[str] = deque()

        final_list: list[dict] = []

        faults = 0

        hits = 0

        if memory_capacity <= 0:
            return final_list

        for index, frame in enumerate(requiring_list):
            page_hit = True

            if frame not in memory:
                faults += 1
                page_hit = False

                if len(memory) >= memory_capacity:
                    memory.pop()

                memory.appendleft(frame)
            else:  # Se a página está na memória, ela é movida para a primeira posição
                hits += 1
                memory.remove(frame)
                memory.appendleft(frame)

            final_list.append(
                {
                    index: {
                        "requested_page": frame,
                        "page_hit": str(page_hit),
                        "total_page_faults": faults,
                        "total_page_hits": hits,
                        "pages_in_memory": list(memory),
                    }
                }
            )

        return final_list

    # Critério de página que ficará mais tempo sem requisições. A lista 'anda' a cada nova inserção
    def optimal(
        self, requiring_list: list[str], memory_capacity: int = 4
    ) -> list[dict]:

        memory: deque[str] = deque()

        final_list: list[dict] = []

        faults = 0

        hits = 0

        if memory_capacity <= 0:
            return final_list

        for index, frame in enumerate(requiring_list):
            page_hit = True

            if frame not in memory:
                faults += 1
                page_hit = False

                if (
                    len(memory) >= memory_capacity
                ):  # Se a memória for extrapolada,remove a página mais distante
                    future = requiring_list[index + 1 :]
                    page_to_remove = None
                    farthest_index = -1

                    for p in memory:
                        if p not in future:
                            page_to_remove = p
                            break

                        else:
                            next_use = future.index(p)
                            if next_use > farthest_index:
                                farthest_index = next_use
                                page_to_remove = p

                    memory.remove(page_to_remove)

                memory.append(
                    frame
                )  # Nova pagina adicionada ao final para atender às convenções acadêmicas de desempate

            else:
                hits += 1

            final_list.append(
                {
                    index: {
                        "requested_page": frame,
                        "page_hit": str(page_hit),
                        "total_page_faults": faults,
                        "total_page_hits": hits,
                        "pages_in_memory": list(
                            reversed(memory)
                        ),  # Lista revertida para manter o padrão dos demais métodos
                    }
                }
            )

        return final_list
