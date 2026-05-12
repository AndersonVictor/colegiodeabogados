import os

import pandas as pd

_ROOT = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_ROOT)
EXCEL_PATH = os.path.join(_PROJECT, "data", "DASHBOARD INGE.xlsx")

if os.path.exists(EXCEL_PATH):
    xls = pd.ExcelFile(EXCEL_PATH)
    
    found = False
    print("\nVerificando cambios en el Excel...")
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for col in df.columns:
            if df[col].dtype == "object":
                matches = df[df[col].astype(str).str.contains("La Concep", case=False, na=False)]
                if not matches.empty:
                    print(f"⚠️ Aún existe 'La Concepcion' en hoja '{sheet}', columna '{col}': {matches[col].unique()}")
                    found = True
    
    if not found:
        print("✅ No se encontró el texto 'La Concepcion'. Los cambios en el Excel son correctos.")
        
    # Mostrar valores en Resumen_Provincia para estar seguros
    if "Resumen_Provincia" in xls.sheet_names:
        rp = xls.parse("Resumen_Provincia", skiprows=1)
        print("\nProvincias en 'Resumen_Provincia':")
        print(rp.iloc[:, 0].unique())
else:
    print("Archivo Excel no encontrado")
