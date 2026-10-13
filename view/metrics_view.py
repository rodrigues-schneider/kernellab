from view.components import DataFrameTable


class MetricsView:
    """Cria as abas de métricas e mostra seus resultados."""

    def __init__(self, notebook, process_colors=None):
        self.cpu_table = DataFrameTable(
            notebook, "Métricas CPU", row_colors=process_colors
        )
        self.memory_table = DataFrameTable(notebook, "Métricas memória")

    def show(self, cpu_metrics, memory_metrics):
        self.cpu_table.show(cpu_metrics)
        self.memory_table.show(memory_metrics)
