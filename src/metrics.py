import pandas as pd


# Calcula as métricas do simulador em ciclos.
class Metrics:
    # Calcula as métricas da CPU usando o cronograma executado.
    @staticmethod
    def cpu(processes: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
        columns = [
            "process",
            "waiting_cycles",
            "turnaround_cycles",
            "response_cycles",
            "context_switches",
        ]
        if processes.empty or schedule.empty:
            return pd.DataFrame(columns=columns)

        cycle_column = "cycle"
        process_column = "name" if "name" in schedule.columns else "id"
        ordered = schedule.sort_values(cycle_column, kind="stable")
        rows = []

        for process in processes.to_dict(orient="records"):
            name = process[process_column]
            process_cycles = ordered.loc[ordered[process_column] == name, cycle_column]
            if process_cycles.empty:
                continue

            first_cycle = int(process_cycles.iloc[0])
            completion_cycle = int(process_cycles.iloc[-1])
            burst_cycles = int(process["burst"])
            # O cronograma estático considera todos os processos prontos no ciclo zero.
            turnaround_cycles = completion_cycle
            rows.append(
                {
                    "process": name,
                    "waiting_cycles": turnaround_cycles - burst_cycles,
                    "turnaround_cycles": turnaround_cycles,
                    "response_cycles": first_cycle - 1,
                    "context_switches": pd.NA,
                }
            )

        result = pd.DataFrame.from_records(rows, columns=columns)
        if result.empty:
            return result

        execution_order = ordered[process_column].tolist()
        context_switches = 0
        for position in range(1, len(execution_order)):
            previous_process = execution_order[position - 1]
            current_process = execution_order[position]
            if previous_process != current_process:
                context_switches += 1
        summary = {
            "process": "MÉDIA",
            "waiting_cycles": round(result["waiting_cycles"].mean(), 2),
            "turnaround_cycles": round(result["turnaround_cycles"].mean(), 2),
            "response_cycles": round(result["response_cycles"].mean(), 2),
            "context_switches": pd.NA,
        }
        context_switch_summary = {
            "process": "TOTAL",
            "waiting_cycles": pd.NA,
            "turnaround_cycles": pd.NA,
            "response_cycles": pd.NA,
            "context_switches": int(context_switches),
        }
        output_rows = result.to_dict(orient="records")
        output_rows.append(summary)
        output_rows.append(context_switch_summary)
        return pd.DataFrame.from_records(output_rows, columns=columns)

    # Agrupa ciclos consecutivos do mesmo processo em intervalos de CPU.
    @staticmethod
    def gantt(schedule: pd.DataFrame) -> pd.DataFrame:
        columns = ["process", "start_cycle", "end_cycle", "cycles_to_run"]
        if schedule.empty:
            return pd.DataFrame(columns=columns)

        cycle_column = "cycle"
        process_column = "name" if "name" in schedule.columns else "id"
        ordered = schedule.sort_values(cycle_column, kind="stable")
        rows = []

        for row in ordered.to_dict(orient="records"):
            cycle = int(row[cycle_column])
            process = row[process_column]
            if rows and rows[-1]["process"] == process:
                rows[-1]["end_cycle"] = cycle
                rows[-1]["cycles_to_run"] += 1
            else:
                rows.append(
                    {
                        "process": process,
                        "start_cycle": cycle - 1,
                        "end_cycle": cycle,
                        "cycles_to_run": 1,
                    }
                )
        return pd.DataFrame.from_records(rows, columns=columns)

    # Retorna contagens de memória e taxa de faltas em percentual.
    @staticmethod
    def memory(schedule: pd.DataFrame) -> pd.DataFrame:
        columns = [
            "references",
            "page_hits",
            "page_faults",
            "page_fault_rate (%)",
        ]
        if schedule.empty:
            return pd.DataFrame([[0, 0, 0, 0.0]], columns=columns)

        if "page_hit" in schedule.columns:
            hits = 0
            for page_hit in schedule["page_hit"]:
                if bool(page_hit):
                    hits += 1
            faults = len(schedule) - hits
        else:
            hits = int(schedule["total_page_hits"].iloc[-1])
            faults = int(schedule["total_page_faults"].iloc[-1])
        references = len(schedule)
        return pd.DataFrame(
            [[references, hits, faults, round(faults / references * 100, 2)]],
            columns=columns,
        )

    # Converte os dados em DataFrames
    @staticmethod
    def from_values(**values: float) -> pd.DataFrame:
        return pd.DataFrame([values])

    # Calcula as médias.
    @staticmethod
    def averages(metrics: pd.DataFrame) -> pd.DataFrame:
        numeric = metrics.select_dtypes(include="number")
        if numeric.empty:
            return pd.DataFrame([{}])

        averages = {}
        for column in numeric.columns:
            averages[column] = round(numeric[column].mean(), 2)
        return pd.DataFrame([averages])
