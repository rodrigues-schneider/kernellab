import pandas as pd


class Metrics:
    """Calcula métricas do simulador e sempre retorna DataFrames."""

    @staticmethod
    def cpu(processes: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
        """Retorna métricas por processo e uma linha final com médias e trocas.

        Os valores são expressos em ciclos. A sequência de execução recebida é
        mantida; o primeiro ciclo numerado como 1 começa no instante 0.
        """
        columns = [
            "process",
            "waiting_cycles",
            "turnaround_cycles",
            "response_cycles",
            "context_switches",
        ]
        if processes.empty or schedule.empty:
            return pd.DataFrame(columns=columns)

        cycle_column = "cicle" if "cicle" in schedule.columns else "cycle"
        process_column = "name" if "name" in schedule.columns else "id"
        ordered = schedule.sort_values(cycle_column, kind="stable")
        rows = []

        for process in processes.to_dict(orient="records"):
            name = process[process_column]
            process_cycles = ordered.loc[
                ordered[process_column] == name, cycle_column
            ]
            if process_cycles.empty:
                continue

            first_cycle = int(process_cycles.iloc[0])
            completion_cycle = int(process_cycles.iloc[-1])
            arrival_cycle = int(process["arrival"])
            burst_cycles = int(process["burst"])
            turnaround_cycles = completion_cycle - arrival_cycle
            rows.append(
                {
                    "process": name,
                    "waiting_cycles": turnaround_cycles - burst_cycles,
                    "turnaround_cycles": turnaround_cycles,
                    "response_cycles": first_cycle - 1 - arrival_cycle,
                    "context_switches": pd.NA,
                }
            )

        result = pd.DataFrame.from_records(rows, columns=columns)
        if result.empty:
            return result

        execution_order = ordered[process_column].tolist()
        context_switches = sum(
            previous != current
            for previous, current in zip(execution_order, execution_order[1:])
        )
        summary = {
            "process": "MÉDIA",
            "waiting_cycles": result["waiting_cycles"].mean(),
            "turnaround_cycles": result["turnaround_cycles"].mean(),
            "response_cycles": result["response_cycles"].mean(),
            "context_switches": int(context_switches),
        }
        return pd.concat([result, pd.DataFrame([summary])], ignore_index=True)

    @staticmethod
    def gantt(schedule: pd.DataFrame) -> pd.DataFrame:
        """Retorna os intervalos contíguos do diagrama de Gantt em ciclos."""
        columns = ["process", "start_cycle", "end_cycle"]
        if schedule.empty:
            return pd.DataFrame(columns=columns)

        cycle_column = "cicle" if "cicle" in schedule.columns else "cycle"
        process_column = "name" if "name" in schedule.columns else "id"
        ordered = schedule.sort_values(cycle_column, kind="stable")
        rows = []

        for cycle, process in ordered[[cycle_column, process_column]].itertuples(
            index=False, name=None
        ):
            cycle = int(cycle)
            if rows and rows[-1]["process"] == process:
                rows[-1]["end_cycle"] = cycle
            else:
                rows.append(
                    {
                        "process": process,
                        "start_cycle": cycle - 1,
                        "end_cycle": cycle,
                    }
                )
        return pd.DataFrame.from_records(rows, columns=columns)

    @staticmethod
    def memory(schedule: pd.DataFrame) -> pd.DataFrame:
        """Retorna uma linha com hits, faltas e taxa de faltas de página."""
        columns = ["references", "page_hits", "page_faults", "page_fault_rate"]
        if schedule.empty:
            return pd.DataFrame([[0, 0, 0, 0.0]], columns=columns)

        if "page_hit" in schedule.columns:
            hits = int(schedule["page_hit"].fillna(False).astype(bool).sum())
            faults = len(schedule) - hits
        else:
            hits = int(schedule["total_page_hits"].iloc[-1])
            faults = int(schedule["total_page_faults"].iloc[-1])
        references = len(schedule)
        return pd.DataFrame(
            [[references, hits, faults, faults / references]], columns=columns
        )

    @staticmethod
    def from_values(**values: float) -> pd.DataFrame:
        """Organiza valores de métricas já calculados em uma linha tabular."""
        return pd.DataFrame([values])

    @staticmethod
    def averages(metrics: pd.DataFrame) -> pd.DataFrame:
        """Retorna as médias das colunas numéricas já calculadas por processo."""
        numeric = metrics.select_dtypes(include="number")
        if numeric.empty:
            return pd.DataFrame([{}])
        return pd.DataFrame([numeric.mean().to_dict()])
