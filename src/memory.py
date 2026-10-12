from collections import deque
from enum import Enum

import pandas as pd


# Recebe a lista de requisições da memória e o número de páginas e demonstra o estado a cada ciclo
class MemoryManager:
    class Methods(Enum):
        FIFO = "first_in_first_out"
        LRU = "least_recently_used"
        OPTIMAL = "optimal"

    @staticmethod
    def _as_dataframe(rows: list[dict]) -> pd.DataFrame:
        columns = [
            "cycle",
            "requested_page",
            "page_hit",
            "total_page_faults",
            "total_page_hits",
            "pages_in_memory",
        ]
        return pd.DataFrame.from_records(rows, columns=columns)

    # Remove a página que chegou primeiro
    @staticmethod
    def first_in_first_out(
        references_df: pd.DataFrame, memory_capacity: int = 4
    ) -> pd.DataFrame:
        references = references_df["page"].astype(str).tolist()
        memory: deque[str] = deque()
        rows = []
        faults = 0
        hits = 0

        for cycle, page in enumerate(references):
            page_hit = page in memory

            if page_hit:
                hits += 1
            else:
                faults += 1
                if memory_capacity > 0:
                    if len(memory) >= memory_capacity:
                        memory.pop()
                    memory.appendleft(page)

            rows.append(
                {
                    "cycle": cycle,
                    "requested_page": page,
                    "page_hit": page_hit,
                    "total_page_faults": faults,
                    "total_page_hits": hits,
                    "pages_in_memory": list(memory),
                }
            )

        return MemoryManager._as_dataframe(rows)

    # Remove a página há mais tempo sem uso
    @staticmethod
    def least_recently_used(
        references_df: pd.DataFrame, memory_capacity: int = 4
    ) -> pd.DataFrame:
        references = references_df["page"].astype(str).tolist()
        memory: deque[str] = deque()
        rows = []
        faults = 0
        hits = 0

        for cycle, page in enumerate(references):
            page_hit = page in memory

            if page_hit:
                hits += 1
                memory.remove(page)
                memory.appendleft(page)
            else:
                faults += 1
                if memory_capacity > 0:
                    if len(memory) >= memory_capacity:
                        memory.pop()
                    memory.appendleft(page)

            rows.append(
                {
                    "cycle": cycle,
                    "requested_page": page,
                    "page_hit": page_hit,
                    "total_page_faults": faults,
                    "total_page_hits": hits,
                    "pages_in_memory": list(memory),
                }
            )

        return MemoryManager._as_dataframe(rows)

    # Olha para o restante da lista e remove a página que ficará mais tempo sem ser requisitada
    @staticmethod
    def optimal(references_df: pd.DataFrame, memory_capacity: int = 4) -> pd.DataFrame:
        references = references_df["page"].astype(str).tolist()
        memory: deque[str] = deque()
        rows = []
        faults = 0
        hits = 0

        for cycle, page in enumerate(references):
            page_hit = page in memory

            if page_hit:
                hits += 1
            else:
                faults += 1
                if memory_capacity > 0:
                    if len(memory) >= memory_capacity:
                        future_references = references[cycle + 1 :]
                        next_use = {
                            resident_page: (
                                future_references.index(resident_page)
                                if resident_page in future_references
                                else float("inf")
                            )
                            for resident_page in memory
                        }
                        page_to_remove = max(next_use, key=next_use.get)
                        memory.remove(page_to_remove)

                    memory.append(page)

            rows.append(
                {
                    "cycle": cycle,
                    "requested_page": page,
                    "page_hit": page_hit,
                    "total_page_faults": faults,
                    "total_page_hits": hits,
                    "pages_in_memory": list(reversed(memory)),
                }
            )

        return MemoryManager._as_dataframe(rows)
