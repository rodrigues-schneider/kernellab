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


def format_process_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    if "process" in result.columns:
        result["process"] = result["process"].astype(str).str.upper()
    return result


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
    ordered_columns = []
    for column in columns:
        if column in result.columns:
            ordered_columns.append(column)
    for column in result.columns:
        if column not in ordered_columns:
            ordered_columns.append(column)
    result = result[ordered_columns]

    if "device" in result.columns:
        result["device"] = result["device"].astype(str).str.upper()
    if "running_process" in result.columns:
        result["running_process"] = (
            result["running_process"].astype(str).str.upper()
        )
    if "status" in result.columns:
        result["status"] = result["status"].astype(str).str.upper()
    if "queue" in result.columns:
        formatted_queues = []
        for queue in result["queue"]:
            formatted_queue = []
            if isinstance(queue, list):
                for request in queue:
                    formatted_queue.append(
                        {
                            **request,
                            "process": str(request.get("process", "")).upper(),
                            "status": str(request.get("status", "")).upper(),
                        }
                    )
            formatted_queues.append(formatted_queue)
        result["queue"] = formatted_queues
    return result


def process_color_map(process_names: list[str]) -> dict[str, str]:
    colors = {}
    for index, process_name in enumerate(process_names):
        color_index = index % len(PROCESS_COLORS)
        colors[str(process_name).upper()] = PROCESS_COLORS[color_index]
    return colors
