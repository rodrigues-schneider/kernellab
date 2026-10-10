"""Leitura simples dos arquivos JSON usados pelo simulador."""

import json
from pathlib import Path


class DataLoader:
    def __init__(self, data_directory: str | Path | None = None):
        default_directory = Path(__file__).resolve().parents[2] / "data"
        self.data_directory = Path(data_directory or default_directory)

    def read(self, filename: str | Path):
        path = Path(filename)
        if not path.is_absolute():
            path = self.data_directory / path
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    def processes(self, filename: str = "processes.json") -> list[dict]:
        processes = self.read(filename)
        for process in processes:
            for field in ("arrival", "burst", "priority", "memory"):
                process[field] = int(process[field])
        return processes

    def memory_references(self, filename: str = "memory_requering.json") -> list[str]:
        data = self.read(filename)
        return [str(page) for page in data[0][next(iter(data[0]))]]

    def access_control_list(self, filename: str = "access_control_list.json") -> dict:
        data = self.read(filename)
        acl = {}
        for record in data:
            for process_name, rules in record.items():
                permissions = {}
                for rule in rules:
                    permissions.update(rule)
                acl[process_name] = permissions
        return acl

    def devices(self, filename: str = "devices_list.json") -> list[dict]:
        return self.read(filename)
