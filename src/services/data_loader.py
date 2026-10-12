# Classe utilitária simples para carregar arquivos JSON

from pathlib import Path

import pandas as pd


class DataLoader:
    @staticmethod
    def read_dataframe(file_path: str | Path) -> pd.DataFrame:
        return pd.read_json(Path(file_path), orient="records", encoding="utf-8")
