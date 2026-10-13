from datetime import datetime
from io import BytesIO
from pathlib import Path
import os
import platform
import subprocess
from tkinter import messagebox

import pandas as pd
import ttkbootstrap as ttk
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font, PatternFill

from src.main import main
from src.memory import MemoryManager
from src.metrics import Metrics
from src.schedulers import CPU_Scheduler
from src.services.data_loader import DataLoader
from view.components import DataFrameTable, GanttView, SimulationControls
from view.metrics_view import MetricsView
from view.output_format import (
    DEVICE_COLORS,
    format_device_output,
    format_process_names,
    process_color_map,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"

PROCESS_FILE = DATA_DIR / "cpu" / "processes.json"
PAGES_FILE = DATA_DIR / "memory" / "memory_requering.json"
ACL_FILE = DATA_DIR / "access_control" / "access_control_list.json"
DEVICES_FILE = DATA_DIR / "devices" / "devices_list.json"

CPU_METHODS = {
    "FCFS": CPU_Scheduler.Methods.FCFS,
    "SJF": CPU_Scheduler.Methods.SJF,
    "Round Robin": CPU_Scheduler.Methods.ROUND_ROBIN,
    "Prioridade": CPU_Scheduler.Methods.PRIORITY,
}

MEMORY_METHODS = {
    "FIFO": MemoryManager.Methods.FIFO,
    "LRU": MemoryManager.Methods.LRU,
    "Optimal": MemoryManager.Methods.OPTIMAL,
}

class SimulatorApp:
    def __init__(self, window):
        self.window = window
        self.window.title("KernelLab")
        self.window.geometry("900x750")

        self.last_results = None
        self.last_settings = None
        self._build_window()

    def _build_window(self):
        self.controls = SimulationControls(self.window, CPU_METHODS, MEMORY_METHODS)

        buttons = ttk.Frame(self.window, padding=(8, 0, 8, 8))
        buttons.pack(anchor="center")
        ttk.Button(
            buttons, text="Executar", command=self.run_simulation, bootstyle="success"
        ).pack(side="left", padx=(0, 5))
        self.save_button = ttk.Button(
            buttons, text="Salvar resultados", command=self.save_results, state="disabled"
        )
        self.save_button.pack(side="left", padx=5)
        ttk.Button(
            buttons, text="Abrir pasta docs", command=self.open_docs_folder
        ).pack(side="left", padx=5)

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=4)

        process_names = DataLoader.read_dataframe(PROCESS_FILE)["name"].tolist()
        self.process_colors = process_color_map(process_names)
        self.metrics_view = MetricsView(self.notebook, self.process_colors)

        self.cpu_schedule_table = DataFrameTable(
            self.notebook, "Escalonamento CPU", row_colors=self.process_colors
        )
        self.memory_schedule_table = DataFrameTable(
            self.notebook, "Estado da memória"
        )
        self.devices_table = DataFrameTable(
            self.notebook, "Dispositivos", row_colors=DEVICE_COLORS
        )
        self.gantt_view = GanttView(self.notebook)

        self.status = ttk.Label(
            self.window, text="Pronto.", padding=8, anchor="center"
        )
        self.status.pack(fill="x")

    def _get_pages(self):
        if self.controls.pages_mode.get() == "default":
            return PAGES_FILE

        pages = []
        text = self.controls.pages_entry.get()
        for page in text.split(","):
            page = page.strip()
            if page != "":
                pages.append(page)

        if len(pages) == 0:
            raise ValueError("Digite as páginas separadas por vírgula.")
        return pd.DataFrame({"page": pages})

    def run_simulation(self):
        self.save_button.configure(state="disabled")
        try:
            cpu_method = CPU_METHODS[self.controls.cpu_choice.get()]
            memory_method = MEMORY_METHODS[self.controls.memory_choice.get()]
            quantum = int(self.controls.quantum.get())
            frames = int(self.controls.frames.get())
            if quantum <= 0:
                raise ValueError("O quantum deve ser maior que zero.")
            if frames <= 0:
                raise ValueError("A quantidade de frames deve ser maior que zero.")
            pages = self._get_pages()
            processes = DataLoader.read_dataframe(PROCESS_FILE)

            cpu_schedule, memory_schedule, device_schedule = main(
                PROCESS_FILE,
                pages,
                ACL_FILE,
                DEVICES_FILE,
                cpu_method,
                memory_method,
                memory_capacity=frames,
                quantum=quantum,
            )

            cpu_metrics = format_process_names(Metrics.cpu(processes, cpu_schedule))
            memory_metrics = Metrics.memory(memory_schedule)
            gantt_data = format_process_names(Metrics.gantt(cpu_schedule))
            device_output = format_device_output(device_schedule)
            process_names = [name.upper() for name in processes["name"].tolist()]

            self.last_results = {
                "CPU_Metricas": cpu_metrics,
                "CPU_Escalonamento": gantt_data,
                "Memoria_Metricas": memory_metrics,
                "Memoria_Estado": memory_schedule,
                "Dispositivos": device_output,
                "Gantt_CPU": gantt_data,
            }
            self.last_settings = pd.DataFrame(
                [{
                    "cpu_method": cpu_method.name,
                    "memory_method": memory_method.name,
                    "quantum": quantum,
                    "frames": frames,
                    "page_sequence": ", ".join(
                        memory_schedule["requested_page"].astype(str).tolist()
                    ),
                }]
            )

            self.metrics_view.show(cpu_metrics, memory_metrics)
            self.cpu_schedule_table.show(gantt_data)
            self.memory_schedule_table.show(memory_schedule)
            self.devices_table.show(device_output)
            self.gantt_view.show(gantt_data, process_names)
            self.notebook.select(self.metrics_view.cpu_table.table.winfo_parent())
            self.save_button.configure(state="normal")
            self.status.configure(text="Simulação concluída.")
        except Exception as error:
            self.status.configure(text="Erro na simulação.")
            messagebox.showerror("Erro", str(error), parent=self.window)

    def save_results(self):
        if self.last_results is None:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_path = DOCS_DIR / f"resultados_{timestamp}.xlsx"
        image_data = BytesIO()

        try:
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
            self.gantt_view.figure.savefig(
                image_data, format="png", bbox_inches="tight"
            )
            image_data.seek(0)

            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                self.last_settings.to_excel(writer, sheet_name="Configuracao", index=False)
                for sheet_name, dataframe in self.last_results.items():
                    dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
                writer.sheets["Gantt_CPU"].add_image(ExcelImage(image_data), "E2")

                header_fill = PatternFill(
                    fill_type="solid", fgColor="E7E6E6"
                )
                for worksheet in writer.book.worksheets:
                    worksheet.freeze_panes = "A2"
                    for cell in worksheet[1]:
                        if cell.value is not None:
                            cell.value = str(cell.value).upper()
                        cell.fill = header_fill
                        cell.font = Font(bold=True)

                style_sheets = {
                    "CPU_Metricas": (
                        "PROCESS",
                        self.process_colors,
                        ["PROCESS"],
                    ),
                    "CPU_Escalonamento": (
                        "PROCESS",
                        self.process_colors,
                        ["PROCESS"],
                    ),
                    "Gantt_CPU": (
                        "PROCESS",
                        self.process_colors,
                        ["PROCESS"],
                    ),
                    "Dispositivos": (
                        "DEVICE",
                        DEVICE_COLORS,
                        ["DEVICE", "RUNNING_PROCESS", "QUEUE"],
                    ),
                }
                for sheet_name, (name_column, colors, bold_names) in style_sheets.items():
                    worksheet = writer.sheets[sheet_name]
                    name_columns = {
                        cell.value: cell.column for cell in worksheet[1]
                    }
                    entity_column = name_columns.get(name_column)
                    if entity_column is None:
                        continue
                    for row_number in range(2, worksheet.max_row + 1):
                        entity_name = worksheet.cell(
                            row=row_number, column=entity_column
                        ).value
                        color = colors.get(entity_name)
                        if color is None:
                            continue
                        row_fill = PatternFill(
                            fill_type="solid", fgColor=color.lstrip("#")
                        )
                        for cell in worksheet[row_number]:
                            cell.fill = row_fill
                        for column_name in bold_names:
                            column_number = name_columns.get(column_name)
                            if column_number is not None:
                                worksheet.cell(
                                    row=row_number, column=column_number
                                ).font = Font(bold=True)

            self.status.configure(text=f"Salvo em {file_path}")
            messagebox.showinfo(
                "Salvo", f"Arquivo salvo em:\n{file_path}", parent=self.window
            )
        except Exception as error:
            messagebox.showerror("Erro ao salvar", str(error), parent=self.window)
        finally:
            image_data.close()

    def open_docs_folder(self):
        try:
            DOCS_DIR.mkdir(parents=True, exist_ok=True)
            if platform.system() == "Windows":
                os.startfile(str(DOCS_DIR))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(DOCS_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(DOCS_DIR)])
        except Exception as error:
            messagebox.showerror(
                "Erro ao abrir pasta", str(error), parent=self.window
            )


def run_app():
    window = ttk.Window(themename="darkly")
    SimulatorApp(window)
    window.mainloop()
