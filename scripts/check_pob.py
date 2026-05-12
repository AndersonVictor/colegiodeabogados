import os

import pandas as pd

_ROOT = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_ROOT)
df = pd.read_excel(
    os.path.join(_PROJECT, "data", "data_organizada_CSJJ_2025.xlsx"),
    sheet_name="Demografia",
)
print(df.columns)
