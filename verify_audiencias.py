import pandas as pd
import os

EXCEL_PATH = r"DASHBOARD INGE.xlsx"

if os.path.exists(EXCEL_PATH):
    xls = pd.ExcelFile(EXCEL_PATH)
    
    if "Audiencias_Data" in xls.sheet_names:
        aud = xls.parse("Audiencias_Data")
        # Print columns to be sure
        print("Columns in Audiencias_Data:", aud.columns.tolist())
        # The code uses 'Sede' as the first column after parsing
        # but let's see what the actual first column values are.
        print("\nUnique values in first column of Audiencias_Data:")
        print(aud.iloc[:, 0].unique().tolist())
        
        # Search specifically for "Concep" in this sheet
        matches = aud[aud.iloc[:, 0].astype(str).str.contains("Concep", case=False, na=False)]
        if not matches.empty:
            print("\nMatches for 'Concep' in Audiencias_Data:")
            print(matches.iloc[:, 0].unique().tolist())
    else:
        print("Sheet 'Audiencias_Data' not found")
        
    # Global search again, but more sensitive
    print("\nGlobal search for 'Concep' (showing full strings):")
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        for col in df.columns:
            if df[col].dtype == "object":
                m = df[df[col].astype(str).str.contains("Concep", case=False, na=False)]
                if not m.empty:
                    print(f"Sheet '{sheet}', Col '{col}': {m[col].unique().tolist()}")
else:
    print("Excel not found")
