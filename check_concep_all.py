import pandas as pd
import os

EXCEL_PATH = r"DASHBOARD INGE.xlsx"

if os.path.exists(EXCEL_PATH):
    xls = pd.ExcelFile(EXCEL_PATH)
    print("Checking for ANY variations of 'Concep'...")
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for col in df.columns:
            if df[col].dtype == "object":
                unique_vals = [str(v) for v in df[col].unique() if pd.notna(v)]
                for v in unique_vals:
                    if "concep" in v.lower():
                        print(f"Sheet: {sheet}, Column: {col}, Value: '{v}'")
else:
    print("Excel not found")
