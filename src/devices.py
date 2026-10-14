from enum import StrEnum

import pandas as pd


class DeviceManager:
    class DeviceStatus(StrEnum):
        FREE = "FREE"
        IN_USE = "IN_USE"
        EXCLUSIVE_ACCESS = "EXCLUSIVE_ACCESS"

    class ProcessStatus(StrEnum):
        RUNNING = "RUNNING"
        WAITING = "WAITING"

    # Converte os registros finais da simulação em DataFrame.
    @staticmethod
    def _as_dataframe(rows: list[dict]) -> pd.DataFrame:
        columns = [
            "device",
            "status",
            "running_process",
            "process_permissions",
            "queue",
            "start_cycle",
            "end_cycle",
            "cycles_to_run",
            "cycles_waiting",
        ]
        return pd.DataFrame.from_records(rows, columns=columns)

    # Distribui cada processo nas filas dos dispositivos autorizados.
    @staticmethod
    def _distribute_processes(
        cpu_schedule: pd.DataFrame,
        access_control_list: pd.DataFrame,
        devices: dict,
    ) -> None:
        permissions = {}
        for row in access_control_list.to_dict(orient="records"):
            permissions[(row["process"], row["device"])] = row["permissions"]

        processes = cpu_schedule.drop_duplicates(subset="name").to_dict(
            orient="records"
        )
        for process in processes:
            process_name = process["name"]
            requested_devices = []
            cycles_to_run = int(process["cycles_left"]) + 1

            for device_name in process["devices"]:
                if (
                    device_name in devices
                    and (process_name, device_name) in permissions
                    and device_name not in requested_devices
                ):
                    requested_devices.append(device_name)

            for device_name in requested_devices:
                devices[device_name]["queue"].append(
                    {
                        "process": process_name,
                        "permissions": permissions[(process_name, device_name)],
                        "requested_devices": requested_devices,
                        "cycles_left": cycles_to_run,
                        "status": DeviceManager.ProcessStatus.WAITING.value,
                    }
                )

    # Coordena a entrada simultânea em dispositivos com acesso exclusivo.
    @staticmethod
    def _handle_exclusive_access(devices: dict) -> tuple[list[str], list[str]]:
        exclusive_processes = []
        for device in devices.values():
            for request in device["queue"]:
                if "exclusive_access" in request["permissions"]:
                    process_name = request["process"]
                    if process_name not in exclusive_processes:
                        exclusive_processes.append(process_name)

        busy_devices = []
        waiting_processes = []
        for process_name in exclusive_processes:
            process_request = None
            for device in devices.values():
                if device["queue"] and device["queue"][0]["process"] == process_name:
                    process_request = device["queue"][0]
                    break

            if process_request is None:
                continue

            requested_devices = process_request["requested_devices"]
            can_enter_all_devices = True
            for device_name in requested_devices:
                queue = devices[device_name]["queue"]
                if not queue or queue[0]["process"] != process_name:
                    can_enter_all_devices = False
                    break

            if not can_enter_all_devices:
                waiting_processes.append(process_name)
                continue

            is_device_busy = False
            for device_name in requested_devices:
                if device_name in busy_devices:
                    is_device_busy = True
                    break
            if is_device_busy:
                waiting_processes.append(process_name)
                continue

            requests_are_complete = True
            for device_name in requested_devices:
                device = devices[device_name]
                request = device["queue"][0]
                request["status"] = DeviceManager.ProcessStatus.RUNNING.value
                request["cycles_left"] -= 1
                device["running_process"] = process_name
                device["process_permissions"] = request["permissions"]
                device["status"] = (
                    DeviceManager.DeviceStatus.EXCLUSIVE_ACCESS.value
                    if "exclusive_access" in request["permissions"]
                    else DeviceManager.DeviceStatus.IN_USE.value
                )
                busy_devices.append(device_name)
                if request["cycles_left"] > 0:
                    requests_are_complete = False

            if requests_are_complete:
                for device_name in requested_devices:
                    devices[device_name]["queue"].pop(0)

        return busy_devices, waiting_processes

    # Executa um ciclo das filas e registra o estado de cada dispositivo.
    @staticmethod
    def _execute_device_queues(devices: dict, cycle: int) -> list[dict]:
        for device in devices.values():
            device["status"] = DeviceManager.DeviceStatus.FREE.value
            device["running_process"] = "none"
            device["process_permissions"] = "none"

        busy_devices, waiting_processes = DeviceManager._handle_exclusive_access(
            devices
        )

        for device_name, device in devices.items():
            if device_name in busy_devices or not device["queue"]:
                continue

            request = device["queue"][0]
            if (
                "exclusive_access" in request["permissions"]
                or request["process"] in waiting_processes
            ):
                continue

            request = device["queue"].pop(0)
            request["status"] = DeviceManager.ProcessStatus.RUNNING.value
            request["cycles_left"] -= 1
            device["running_process"] = request["process"]
            device["process_permissions"] = request["permissions"]
            device["status"] = DeviceManager.DeviceStatus.IN_USE.value
            if request["cycles_left"] > 0:
                device["queue"].insert(0, request)

        rows = []
        for device_name, device in devices.items():
            queue = []
            for request in device["queue"]:
                if request["status"] == DeviceManager.ProcessStatus.WAITING.value:
                    queue.append(
                        {
                            "process": request["process"],
                            "status": request["status"],
                        }
                    )

            rows.append(
                {
                    "cycle": cycle,
                    "device": device_name,
                    "status": device["status"],
                    "running_process": device["running_process"],
                    "process_permissions": device["process_permissions"],
                    "queue": queue,
                }
            )
        return rows

    # Agrupa os ciclos de execução e espera por dispositivo e processo.
    @staticmethod
    def _compress_schedule(rows: list[dict], device_order: list[str]) -> pd.DataFrame:
        activities = {}

        for row in rows:
            device_name = row["device"]
            cycle = row["cycle"]
            process_name = row["running_process"]
            if process_name != "none":
                key = (device_name, process_name)
                if key not in activities:
                    activities[key] = {
                        "run_cycles": [],
                        "waiting_cycles": [],
                        "status": row["status"],
                        "permissions": row["process_permissions"],
                        "queue": [],
                    }
                activities[key]["status"] = row["status"]
                activities[key]["permissions"] = row["process_permissions"]
                activities[key]["run_cycles"].append(cycle)
                if not activities[key]["queue"]:
                    activities[key]["queue"] = row["queue"]

            for request in row["queue"]:
                key = (device_name, request["process"])
                if key not in activities:
                    activities[key] = {
                        "run_cycles": [],
                        "waiting_cycles": [],
                        "status": DeviceManager.ProcessStatus.WAITING.value,
                        "permissions": [],
                        "queue": row["queue"],
                    }
                activities[key]["waiting_cycles"].append(cycle)

        intervals = []
        for device_name in device_order:
            for (activity_device, process_name), activity in activities.items():
                if activity_device != device_name:
                    continue

                run_cycles = activity["run_cycles"]
                waiting_cycles = activity["waiting_cycles"]
                relevant_cycles = run_cycles or waiting_cycles
                intervals.append(
                    {
                        "device": device_name,
                        "status": activity["status"],
                        "running_process": process_name if run_cycles else "none",
                        "process_permissions": activity["permissions"],
                        "queue": activity["queue"],
                        "start_cycle": min(relevant_cycles),
                        "end_cycle": max(relevant_cycles),
                        "cycles_to_run": len(run_cycles),
                        "cycles_waiting": len(waiting_cycles),
                    }
                )

        return DeviceManager._as_dataframe(intervals)

    # Coordena as filas dos dispositivos e retorna o cronograma resumido.
    @staticmethod
    def scheduler(
        cpu_schedule: pd.DataFrame,
        access_control_list: pd.DataFrame,
        devices_df: pd.DataFrame,
    ) -> pd.DataFrame:
        if cpu_schedule.empty or devices_df.empty:
            return DeviceManager._as_dataframe([])

        devices = {}
        for row in devices_df.to_dict(orient="records"):
            devices[row["device"]] = {
                "status": DeviceManager.DeviceStatus.FREE.value,
                "running_process": "none",
                "process_permissions": "none",
                "queue": [],
            }
        DeviceManager._distribute_processes(cpu_schedule, access_control_list, devices)

        rows = []
        cycle = 1
        has_pending_requests = True
        while has_pending_requests:
            has_pending_requests = False
            for device in devices.values():
                if device["queue"]:
                    has_pending_requests = True
                    break
            if not has_pending_requests:
                break

            rows.extend(DeviceManager._execute_device_queues(devices, cycle))
            cycle += 1

        return DeviceManager._compress_schedule(rows, list(devices))
