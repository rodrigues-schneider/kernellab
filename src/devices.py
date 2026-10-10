from copy import deepcopy
from enum import StrEnum

from services.data_loader import DataLoader


# Recebe a lista de requisições e organiza as filas dos dispositivos.
class DeviceManager:
    def __init__(
        self,
        data_loader: DataLoader | None = None,
        acl_uri: str = "access_control_list.json",
        devices_uri: str = "devices_list.json",
    ):
        loader = data_loader or DataLoader()
        self.__acl = loader.access_control_list(acl_uri)
        self.__devices = loader.devices(devices_uri)

    class DeviceStatus(StrEnum):
        FREE = "FREE"
        IN_USE = "IN_USE"
        EXCLUSIVE_ACCESS = "EXCLUSIVE_ACCESS"

    class ProcessStatus(StrEnum):
        RUNNING = "RUNNING"
        WAITING = "WAITING"

    # Verifica se o processo tem direito de acesso ao dispositivo
    def __permissions_handler(self, process: dict) -> list[dict]:

        permissions: list[dict] = []

        process_acl = self.__acl.get(process["name"], {})

        for device in process["devices"]:
            if device in process_acl:
                permissions.append({device: process_acl[device]})

        return permissions

    # Envia o pedido de execução para os dispositivos corretos
    def __queue_mananger(self, process: dict):

        permissions = self.__permissions_handler(process)

        process["device_permissions"] = permissions

        for device_name in process["devices"]:
            # Verifica se o processo possui permissão.
            if not any(device_name in permission for permission in permissions):
                continue

        for device_record in self.__devices:
            if device_name in device_record:
                device = device_record[device_name]

                process["device_status"] = self.ProcessStatus.WAITING.value

                device["queue"].append(process)

                break

    # Executa as listas dos dispositivos a cada ciclo
    def __execution_manager(self) -> list[dict]:

        for device_record in self.__devices:
            for device_name, device in device_record.items():
                if device["queue"]:
                    process = device["queue"].pop(0)

                    device["status"] = self.DeviceStatus.IN_USE.value

                    process["device_status"] = self.ProcessStatus.RUNNING.value

                    device["running_process"] = process["name"]

                    device["process_permissions"] = next(
                        (
                            permission[device_name]
                            for permission in process["device_permissions"]
                            if device_name in permission
                        ),
                        "none",
                    )

        return deepcopy(self.__devices)

    # Método principal que restorna os estados a cada ciclo
    def scheduler(self, requiring_list: list[dict]) -> list[dict]:

        requests = deepcopy(requiring_list)

        queue_sizes: list[int] = []

        index = 0

        final_list: list[dict] = [{index: deepcopy(self.__devices)}]

        for request in requests:
            self.__queue_mananger(request)

        # Calcula o tamanho da fila de cada dispositivo e define a quantidade de repetições
        for device_record in self.__devices:
            for device in device_record.values():
                queue_sizes.append(len(device["queue"]))

        cycles_to_run = max(queue_sizes, default=0)

        while cycles_to_run > 0:
            state = self.__execution_manager()

            index += 1

            final_list.append({index: state})

            cycles_to_run -= 1

        return final_list
