import pandas as pd
import tkinter as tk
import ttkbootstrap as ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from view.output_format import PROCESS_COLORS


class SimulationControls:
    """Controles para escolher os parâmetros da simulação."""

    def __init__(self, parent, cpu_methods, memory_methods):
        frame = ttk.Frame(parent, padding=8)
        frame.pack(anchor="center", pady=8)

        ttk.Label(frame, text="CPU:").grid(row=0, column=0, sticky="w")
        self.cpu_choice = tk.StringVar(value="FCFS")
        ttk.Combobox(
            frame,
            textvariable=self.cpu_choice,
            values=list(cpu_methods),
            state="readonly",
            width=18,
        ).grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="Memória:").grid(row=0, column=2, sticky="w")
        self.memory_choice = tk.StringVar(value="FIFO")
        ttk.Combobox(
            frame,
            textvariable=self.memory_choice,
            values=list(memory_methods),
            state="readonly",
            width=18,
        ).grid(row=0, column=3, padx=5)

        ttk.Label(frame, text="Quantum:").grid(row=1, column=0, sticky="w")
        self.quantum = tk.StringVar(value="3")
        ttk.Entry(frame, textvariable=self.quantum, width=8).grid(
            row=1, column=1, sticky="w", padx=5
        )

        ttk.Label(frame, text="Frames:").grid(row=1, column=2, sticky="w")
        self.frames = tk.StringVar(value="4")
        ttk.Entry(frame, textvariable=self.frames, width=8).grid(
            row=1, column=3, sticky="w", padx=5
        )

        self.pages_mode = tk.StringVar(value="default")
        ttk.Radiobutton(
            frame,
            text="Sequência padrão",
            variable=self.pages_mode,
            value="default",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Radiobutton(
            frame,
            text="Minha sequência:",
            variable=self.pages_mode,
            value="custom",
        ).grid(row=2, column=2, sticky="w", pady=5)

        self.pages_entry = ttk.Entry(frame, width=55)
        self.pages_entry.insert(
            0, "1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5, 2, 1, 5, 3, 2"
        )
        self.pages_entry.grid(row=3, column=0, columnspan=4, sticky="ew", pady=4)


class DataFrameTable:
    """Uma aba com tabela e barras de rolagem para exibir um DataFrame."""

    def __init__(self, notebook, title, row_colors=None):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text=title)
        self.row_colors = row_colors or {}

        self.table = ttk.Treeview(frame, show="headings")
        vertical_scroll = ttk.Scrollbar(
            frame, orient="vertical", command=self.table.yview
        )
        horizontal_scroll = ttk.Scrollbar(
            frame, orient="horizontal", command=self.table.xview
        )
        self.table.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        for row_name, color in self.row_colors.items():
            self.table.tag_configure(
                f"row_{row_name}",
                background=color,
                foreground="#212529",
                font=("TkDefaultFont", 9, "bold"),
            )

    def show(self, dataframe):
        for item in self.table.get_children():
            self.table.delete(item)

        columns = list(dataframe.columns)
        self.table.configure(columns=columns)
        for column in columns:
            self.table.heading(column, text=column.upper())
            self.table.column(column, width=130, minwidth=90, stretch=True)

        for _, row in dataframe.iterrows():
            values = []
            for column in columns:
                value = row[column]
                if column == "queue" and isinstance(value, list):
                    queue_items = []
                    for request in value:
                        if isinstance(request, dict):
                            process = request.get("process", "")
                            status = request.get("status", "")
                            queue_items.append(f"{process} ({status})")
                    value = ", ".join(queue_items)
                elif isinstance(value, (list, dict)):
                    value = str(value)
                elif pd.isna(value):
                    value = ""
                values.append(str(value))

            tags = ()
            color_column = "device"
            if color_column not in dataframe.columns:
                color_column = "process"
            if color_column in dataframe.columns:
                row_name = row[color_column]
                if row_name in self.row_colors:
                    tags = (f"row_{row_name}",)
            self.table.insert("", "end", values=values, tags=tags)


class GanttView:
    """Desenha o escalonamento da CPU em uma aba da interface."""

    process_colors = PROCESS_COLORS

    def __init__(self, notebook):
        frame = ttk.Frame(notebook, padding=8)
        notebook.add(frame, text="Gantt CPU")
        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=4)

    def show(self, gantt_data, process_names):
        self.figure.clear()
        axis = self.figure.add_subplot(111)

        for _, row in gantt_data.iterrows():
            process = row["process"]
            position = process_names.index(process)
            start = int(row["start_cycle"])
            end = int(row["end_cycle"])
            color = self.process_colors[position % len(self.process_colors)]
            axis.barh(position, end - start, left=start, color=color)

        if gantt_data.empty:
            last_cycle = 1
        else:
            last_cycle = int(gantt_data["end_cycle"].max())

        axis.set_xlim(0, max(last_cycle, 1))
        axis.set_xticks(range(last_cycle + 1))
        axis.set_yticks(range(len(process_names)))
        axis.set_yticklabels(process_names)
        axis.invert_yaxis()
        axis.set_xlabel("Ciclos")
        axis.set_ylabel("Processos")
        axis.grid(axis="x")
        axis.set_axisbelow(True)
        self.figure.tight_layout()
        self.canvas.draw()
