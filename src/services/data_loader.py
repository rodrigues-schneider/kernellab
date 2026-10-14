# Classe utilitária simples para carregar arquivos JSON

from pathlib import Path

import pandas as pd


class DataLoader:
    @staticmethod
    def read_dataframe(file_path: Path) -> pd.DataFrame:
        return pd.read_json(file_path, orient="records", encoding="utf-8")
