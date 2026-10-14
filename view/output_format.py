import pandas as pd


PROCESS_COLORS = [
    "#DCE6F1",
    "#FCE4D6",
    "#E2F0D9",
    "#F4CCCC",
    "#EADCF8",
    "#EADDD2",
]

DEVICE_COLORS = {
    "LAN": "#DCEEFF",
    "SSD": "#E2F0D9",
    "AUDIO": "#FCE4D6",
}


# Padroniza os nomes dos processos em letras maiúsculas.
def format_process_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    result["process"] = result["process"].str.upper()
    return result


# Ordena e formata as colunas de saída dos dispositivos.
def format_device_output(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    columns = [
        "device",
        "status",
        "running_process",
        "start_cycle",
        "end_cycle",
        "cycles_to_run",
        "cycles_waiting",
        "process_permissions",
        "queue",
    ]
    result = result[columns]
    result["device"] = result["device"].str.upper()
    result["running_process"] = result["running_process"].str.upper()
    result["status"] = result["status"].str.upper()

    formatted_permissions = []
    for permissions in result["process_permissions"]:
        if permissions:
            formatted_permissions.append(", ".join(permissions).upper())
        else:
            formatted_permissions.append("NONE")
    result["process_permissions"] = formatted_permissions

    formatted_queues = []
    for queue in result["queue"]:
        formatted_queue = []
        for request in queue:
            formatted_queue.append(
                {
                    "process": request["process"].upper(),
                    "status": request["status"].upper(),
                }
            )
        formatted_queues.append(formatted_queue)
    result["queue"] = formatted_queues
    return result


# Associa uma cor fixa para cada processo.
def process_color_map(process_names: list[str]) -> dict[str, str]:
    colors = {}
    for index, process_name in enumerate(process_names):
        color_index = index % len(PROCESS_COLORS)
        colors[process_name.upper()] = PROCESS_COLORS[color_index]
    return colors
