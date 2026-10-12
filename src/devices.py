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
    def _enqueue_cycle_requests(
        process: dict, acl: dict, devices: dict
    ) -> None:
        process_name = process.get("name")
        process_acl = acl.get(process_name, {})

        for device_name in process.get("devices", []) or []:
            if device_name not in devices or device_name not in process_acl:
                continue

            devices[device_name]["queue"].append(
                {
                    "process": process_name,
                    "permissions": process_acl[device_name],
                    "status": DeviceManager.ProcessStatus.WAITING.value,
                }
            )

    @staticmethod
    def _run_device_cycle(devices: dict) -> list[dict]:
        rows = []

        for device_name, device in devices.items():
            device["status"] = DeviceManager.DeviceStatus.FREE.value
            device["running_process"] = "none"
            device["process_permissions"] = "none"

            if device["queue"]:
                request = device["queue"].pop(0)
                permissions = request["permissions"]

                device["running_process"] = request["process"]
                device["process_permissions"] = permissions
                device["status"] = (
                    DeviceManager.DeviceStatus.EXCLUSIVE_ACCESS.value
                    if "exclusive_access" in permissions
                    else DeviceManager.DeviceStatus.IN_USE.value
                )

            rows.append(
                {
                    "device": device_name,
                    "status": device["status"],
                    "running_process": device["running_process"],
                    "process_permissions": device["process_permissions"],
                    "queue": deepcopy(device["queue"]),
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
            "cycle",
            "device",
            "status",
            "running_process",
            "process_permissions",
            "queue",
        ]

        if cpu_schedule.empty or devices_df.empty:
            return pd.DataFrame(columns=columns)

        acl = DeviceManager._build_acl(access_control_list)
        devices = DeviceManager._build_devices(devices_df)
        rows = []

        for index, process in enumerate(cpu_schedule.to_dict(orient="records")):
            cycle = process.get("cicle", process.get("cycle", index + 1))
            DeviceManager._enqueue_cycle_requests(process, acl, devices)

            for device_state in DeviceManager._run_device_cycle(devices):
                rows.append({"cycle": cycle, **device_state})

        return pd.DataFrame.from_records(rows, columns=columns)
