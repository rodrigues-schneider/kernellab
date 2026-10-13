from copy import deepcopy
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

    @staticmethod
    def _build_acl(access_control_list: pd.DataFrame) -> dict:
        if access_control_list.empty:
            return {}

        return {
            process: group.set_index("device")["permissions"].to_dict()
            for process, group in access_control_list.groupby("process")
        }

    @staticmethod
    def _build_devices(devices_df: pd.DataFrame) -> dict:
        devices = {}
        for row in devices_df.to_dict(orient="records"):
            devices[row["device"]] = {
                "status": DeviceManager.DeviceStatus.FREE.value,
                "running_process": "none",
                "process_permissions": "none",
                "queue": deepcopy(row.get("queue", [])),
            }
        return devices

    @staticmethod
    def _distribute_processes(
        cpu_schedule: pd.DataFrame, acl: dict, devices: dict
    ) -> None:
        processes = []
        process_names = []

        # Cada processo entra nas filas uma única vez, na ordem do escalonamento.
        for process in cpu_schedule.to_dict(orient="records"):
            process_name = process.get("name")
            if process_name not in process_names:
                process_names.append(process_name)
                processes.append(process)

        for process in processes:
            process_name = process.get("name")
            process_acl = acl.get(process_name, {})
            requested_devices = []
            cycles_left = process.get("cycles_left")
            if pd.isna(cycles_left):
                cycles_to_run = int(process.get("burst", 1))
            else:
                cycles_to_run = int(cycles_left) + 1

            for device_name in process.get("devices", []) or []:
                if device_name in devices and device_name in process_acl:
                    if device_name not in requested_devices:
                        requested_devices.append(device_name)

            for device_name in requested_devices:
                request = {
                    "process": process_name,
                    "permissions": process_acl[device_name],
                    "status": DeviceManager.ProcessStatus.WAITING.value,
                    "requested_devices": requested_devices,
                    "cycles_left": cycles_to_run,
                }
                devices[device_name]["queue"].append(request)

    @staticmethod
    def _handle_exclusive_access(devices: dict) -> tuple[list[str], list[str]]:
        exclusive_processes = []

        # Um processo exclusivo deve esperar em todas as filas que requisitou.
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
                if device["queue"]:
                    request = device["queue"][0]
                    if request["process"] == process_name:
                        process_request = request
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

            has_busy_device = False
            for device_name in requested_devices:
                if device_name in busy_devices:
                    has_busy_device = True
                    break
            if has_busy_device:
                waiting_processes.append(process_name)
                continue

            # O processo mantém todos os dispositivos até consumir seu burst.
            completed_requests = True
            for device_name in requested_devices:
                device = devices[device_name]
                request = device["queue"][0]
                request["status"] = DeviceManager.ProcessStatus.RUNNING.value
                request["cycles_left"] -= 1
                device["running_process"] = process_name
                device["process_permissions"] = request["permissions"]
                if "exclusive_access" in request["permissions"]:
                    device["status"] = DeviceManager.DeviceStatus.EXCLUSIVE_ACCESS.value
                else:
                    device["status"] = DeviceManager.DeviceStatus.IN_USE.value
                busy_devices.append(device_name)
                if request["cycles_left"] > 0:
                    completed_requests = False

            if completed_requests:
                for device_name in requested_devices:
                    devices[device_name]["queue"].pop(0)

        return busy_devices, waiting_processes

    @staticmethod
    def _execute_device_queues(devices: dict) -> list[dict]:
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
            permissions = request["permissions"]

            # Um pedido exclusivo espera até poder entrar em todos os dispositivos.
            if (
                "exclusive_access" in permissions
                or request["process"] in waiting_processes
            ):
                continue

            request = device["queue"].pop(0)
            request["status"] = DeviceManager.ProcessStatus.RUNNING.value
            device["running_process"] = request["process"]
            device["process_permissions"] = permissions
            device["status"] = DeviceManager.DeviceStatus.IN_USE.value
            request["cycles_left"] -= 1
            if request["cycles_left"] > 0:
                device["queue"].insert(0, request)

        rows = []
        for device_name, device in devices.items():
            queue_summary = []
            for request in device["queue"]:
                if isinstance(request, dict):
                    if request.get("status") == DeviceManager.ProcessStatus.RUNNING.value:
                        continue
                    queue_summary.append(
                        {
                            "process": request.get("process", ""),
                            "status": request.get(
                                "status", DeviceManager.ProcessStatus.WAITING.value
                            ),
                        }
                    )

            rows.append(
                {
                    "device": device_name,
                    "status": device["status"],
                    "running_process": device["running_process"],
                    "process_permissions": device["process_permissions"],
                    "queue": queue_summary,
                }
            )

        return rows

    @staticmethod
    def scheduler(
        cpu_schedule: pd.DataFrame,
        access_control_list: pd.DataFrame,
        devices_df: pd.DataFrame,
    ) -> pd.DataFrame:
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

        if cpu_schedule.empty or devices_df.empty:
            return pd.DataFrame(columns=columns)

        acl = DeviceManager._build_acl(access_control_list)
        devices = DeviceManager._build_devices(devices_df)
        DeviceManager._distribute_processes(cpu_schedule, acl, devices)

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

            device_states = DeviceManager._execute_device_queues(devices)
            for device_state in device_states:
                rows.append({"cycle": cycle, **device_state})
            cycle += 1

        return DeviceManager._compress_schedule(rows, list(devices), columns)

    @staticmethod
    def _compress_schedule(
        rows: list[dict], device_order: list[str], columns: list[str]
    ) -> pd.DataFrame:
        intervals = []
        active_intervals = {}

        for row in rows:
            device_name = row["device"]
            state = {
                "status": row["status"],
                "running_process": row["running_process"],
                "process_permissions": row["process_permissions"],
                "queue": row["queue"],
            }
            current = active_intervals.get(device_name)

            same_state = current is not None
            if same_state:
                for key, value in state.items():
                    if current[key] != value:
                        same_state = False
                        break

            if same_state:
                current["end_cycle"] = row["cycle"]
                if row["running_process"] != "none":
                    current["cycles_to_run"] += 1
                if row["queue"]:
                    current["cycles_waiting"] += 1
                continue

            if current is not None:
                intervals.append(current)

            active_intervals[device_name] = {
                "start_cycle": row["cycle"],
                "end_cycle": row["cycle"],
                "cycles_to_run": int(row["running_process"] != "none"),
                "cycles_waiting": int(bool(row["queue"])),
                **state,
                "device": device_name,
            }

        for device_name in device_order:
            if device_name in active_intervals:
                intervals.append(active_intervals[device_name])

        device_positions = {name: index for index, name in enumerate(device_order)}
        intervals.sort(key=lambda row: (row["start_cycle"], device_positions[row["device"]]))
        return pd.DataFrame.from_records(intervals, columns=columns)
