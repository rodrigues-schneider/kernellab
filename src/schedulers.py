from dataclasses import dataclass;

class Scheduler:

    def __init__(self, processes: list[Process]):
        self.processes = processes;

@classmethod
def from_json(cls, json_string: str):
    data = json.loads(json_string);

    processes = [
        Process(**item)     for item in data
    ]
    return cls(processes)


def first_come_first_served(self):
    return sorted(
        self.processes,
        key=lambda process: process.arrival
    )
