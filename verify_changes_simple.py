import pandas as pd
import os

EXCEL_PATH = r"DASHBOARD INGE.xlsx"

if os.path.exists(EXCEL_PATH):
    xls = pd.ExcelFile(EXCEL_PATH)
    found = False
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for col in df.columns:
            if df[col].dtype == "object":
                matches = df[df[col].astype(str).str.contains("La Concep", case=False, na=False)]
                if not matches.empty:
                    print(f"FOUND: sheet={sheet}, col={col}, values={matches[col].unique()}")
                    found = True
    if not found:
        print("SUCCESS: 'La Concepcion' not found.")
    
    if "Resumen_Provincia" in xls.sheet_names:
        rp = xls.parse("Resumen_Provincia", skiprows=1)
        print("Provincias in Resumen_Provincia:", list(rp.iloc[:, 0].unique()))
else:
    print("Excel not found")
