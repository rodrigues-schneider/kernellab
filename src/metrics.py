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

        ordered = schedule.sort_values("cycle", kind="stable")
        rows = []

        for process in processes.to_dict(orient="records"):
            process_name = process["name"]
            process_schedule = ordered[ordered["name"] == process_name]
            if process_schedule.empty:
                continue

            process_cycles = process_schedule["cycle"].tolist()
            first_cycle = int(process_cycles[0])
            completion_cycle = int(process_cycles[-1])
            burst_cycles = int(process["burst"])
            # O cronograma estático considera todos os processos prontos no ciclo zero.
            turnaround_cycles = completion_cycle
            rows.append(
                {
                    "process": process_name,
                    "waiting_cycles": turnaround_cycles - burst_cycles,
                    "turnaround_cycles": turnaround_cycles,
                    "response_cycles": first_cycle - 1,
                    "context_switches": pd.NA,
                }
            )

        result = pd.DataFrame.from_records(rows, columns=columns)
        if result.empty:
            return result

        execution_order = ordered["name"].tolist()
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

        ordered = schedule.sort_values("cycle", kind="stable")
        rows = []

        for schedule_row in ordered.to_dict(orient="records"):
            cycle = int(schedule_row["cycle"])
            process_name = schedule_row["name"]
            if rows and rows[-1]["process"] == process_name:
                rows[-1]["end_cycle"] = cycle
                rows[-1]["cycles_to_run"] += 1
            else:
                rows.append(
                    {
                        "process": process_name,
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

        hits = 0
        for page_hit in schedule["page_hit"]:
            if page_hit:
                hits += 1
        faults = len(schedule) - hits
        references = len(schedule)
        return pd.DataFrame(
            [[references, hits, faults, round(faults / references * 100, 2)]],
            columns=columns,
        )

