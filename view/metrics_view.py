from view.components import DataFrameTable


# Cria as abas de métricas e mostra seus resultados.
class MetricsView:

    # Cria as abas de métricas de CPU e memória.
    def __init__(self, notebook, process_colors):
        self.cpu_table = DataFrameTable(
            notebook, "Métricas CPU", "process", row_colors=process_colors
        )
        self.memory_table = DataFrameTable(notebook, "Métricas memória")

    # Atualiza as duas tabelas de métricas.
    def show(self, cpu_metrics, memory_metrics):
        self.cpu_table.show(cpu_metrics)
        self.memory_table.show(memory_metrics)
