from pathlib import Path
from functools import lru_cache
import pandas as pd

RAW_DATA = Path("data/raw_data.csv")
ERUPTION_DATA = Path("data/eruption_data.pkl")

raw_data = pd.read_csv(RAW_DATA, skiprows=1)
eruption_data = pd.read_pickle(ERUPTION_DATA)
