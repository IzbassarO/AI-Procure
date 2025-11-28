# backend/db/csv_store.py
import csv
import os
from typing import List, Dict

_TENDERS: List[Dict] = []
_IS_LOADED = False

def load_tenders() -> None:
    """Читает data/tenders.csv и кладёт все строки в память."""
    global _TENDERS, _IS_LOADED

    if _IS_LOADED:
        return

    base_dir = os.path.dirname(__file__)          # backend/db
    project_root = os.path.dirname(base_dir)      # backend
    csv_path = os.path.join(project_root, "data", "tenders.csv")

    tenders: List[Dict] = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tenders.append(row)

    _TENDERS = tenders
    _IS_LOADED = True
    print(f"✅ CSV загружен: {len(_TENDERS)} тендеров из {csv_path}")

def get_all_tenders() -> List[Dict]:
    if not _IS_LOADED:
        load_tenders()
    return _TENDERS
