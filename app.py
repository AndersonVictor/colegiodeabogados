import base64
import json
import math
import os

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from plotly.subplots import make_subplots
from streamlit_folium import st_folium


def _ring_signed_area(lons, lats):
    n = len(lons)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        j = (i + 1) % n
        a += lons[i] * lats[j] - lons[j] * lats[i]
    return a * 0.5


def _ring_centroid_lonlat(lons, lats):
    """Centroide planar del anillo (lon, lat); mejor que el promedio de vértices para etiquetas."""
    n = len(lons)
    if n < 3:
        if n == 0:
            return None, None
        return sum(lons) / n, sum(lats) / n
    a = _ring_signed_area(lons, lats)
    if abs(a) < 1e-20:
        return sum(lons) / n, sum(lats) / n
    cx = 0.0
    cy = 0.0
    for i in range(n):
        j = (i + 1) % n
        cross = lons[i] * lats[j] - lons[j] * lats[i]
        cx += (lons[i] + lons[j]) * cross
        cy += (lats[i] + lats[j]) * cross
    return cx / (6.0 * a), cy / (6.0 * a)


def _label_point_latlon_for_feature(ft):
    """Un punto dentro de la geometría (polígono mayor si es MultiPolygon) para el texto."""
    geom = ft["geometry"]
    coords = geom["coordinates"]
    gtype = geom["type"]
    rings = []
    if gtype == "Polygon":
        if coords:
            rings.append(coords[0])
    elif gtype == "MultiPolygon":
        for poly in coords:
            if poly:
                rings.append(poly[0])
    if not rings:
        return None, None
    best = None
    best_a = -1.0
    for ring in rings:
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        ar = abs(_ring_signed_area(lons, lats))
        if ar > best_a:
            best_a = ar
            cx, cy = _ring_centroid_lonlat(lons, lats)
            best = (cy, cx)
    return best if best else (None, None)


def _safe_int(val, default=0):
    """int() seguro ante NaN/None/strings del Excel."""
    x = pd.to_numeric(val, errors="coerce")
    if pd.isna(x):
        return default
    try:
        return int(x)
    except (TypeError, ValueError, OverflowError):
        return default


# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard CSJJ Junín",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Set base plotly font size globally
pio.templates["custom_theme"] = pio.templates["plotly_white"]
pio.templates["custom_theme"].layout.paper_bgcolor = (
    "#F2E8D9"  # Color crema para el fondo del gráfico
)
pio.templates["custom_theme"].layout.plot_bgcolor = (
    "#F2E8D9"  # Color crema para el área del gráfico
)
pio.templates["custom_theme"].layout.font.size = 14
pio.templates["custom_theme"].layout.title.font.size = 16
pio.templates["custom_theme"].layout.legend.font.size = 18
pio.templates["custom_theme"].layout.legend.title.font.size = 18
pio.templates["custom_theme"].layout.xaxis.title.font.size = 20
pio.templates["custom_theme"].layout.xaxis.tickfont.size = 14
pio.templates["custom_theme"].layout.yaxis.title.font.size = 20
pio.templates["custom_theme"].layout.yaxis.tickfont.size = 14
pio.templates.default = "custom_theme"

ROJO = "#6B0F1A"
ROJO2 = "#8B1A2B"
DORADO = "#C4952A"
AZUL = "#2E6DA4"
VERDE = "#4A7C59"
GRIS = "#F2E8D9"

# Paleta de colores solicitada para gráficos generales
NUEVA_PALETA = [
    "#6B0F1A",  # Guindo
    "#E53935",  # Rojo
    "#F4511E",  # Naranja
    "#F9A825",  # Amarillo
    "#2E7D32",  # Verde
    "#00ACC1",  # Celeste
    "#1565C0",  # Azul
    "#6A1B9A",  # Morado
    "#D81B60",  # Rosa
    "#5D4037",  # Marrón
    "#546E7A",  # Gris
]

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
_ASSET_FONTS = os.path.join(ROOT, "assets", "fonts")
_ASSET_IMAGES = os.path.join(ROOT, "assets", "images")
_ANDINA_FONT = os.path.join(_ASSET_FONTS, "Andina free.ttf")


def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

_font_b64_early = (
    get_base64_of_bin_file(_ANDINA_FONT) if os.path.exists(_ANDINA_FONT) else ""
)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800&display=swap');
@font-face {{
    font-family: 'Andina';
    src: url('data:font/truetype;base64,{_font_b64_early}') format('truetype');
    font-weight: normal;
    font-style: normal;
}}
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: #F2E8D9 !important; }}

.block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}

.header-bar {{
    background: linear-gradient(135deg, {ROJO} 0%, {ROJO2} 60%, #3D0A14 100%);
    border-radius: 14px;
    padding: 18px 24px;
    margin-bottom: 22px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 6px 30px rgba(123,26,26,0.35);
    flex-wrap: wrap;
}}
.header-logo {{ flex-shrink: 0; }}
.header-logo img {{ height: 70px; display: block; }}
.header-text {{ flex: 1; min-width: 220px; }}
.header-bar h1 {{ 
    font-family: 'Montserrat', sans-serif; 
    color: #ffffff; 
    font-size: clamp(1.5rem, 4.5vw, 2.6rem);
    font-weight: 800; 
    margin: 0; 
    letter-spacing: .5px; 
    line-height: 1.2;
}}
.header-bar h3 {{ 
    font-family: 'Andina', 'Montserrat', sans-serif; 
    color: rgba(255,255,255,0.95); 
    font-size: clamp(1.4rem, 3.5vw, 2rem);
    font-weight: normal; 
    margin: 5px 0 0; 
    letter-spacing: .3px; 
}}
.header-bar p  {{ 
    color: rgba(255,255,255,.9); 
    font-size: clamp(0.75rem, 2vw, 1rem);
    margin: 5px 0 0; 
    font-weight: 600;
    color: #F9E79F;
    letter-spacing: 0.3px;
}}
.escudo {{ font-size: 3rem; line-height: 1; }}
@media (max-width: 600px) {{
    .header-bar {{ padding: 14px 14px; gap: 12px; border-radius: 10px; }}
    .header-logo img {{ height: 52px; }}
}}

.kpi-card {{
    background: #fff;
    border-radius: 14px;
    padding: 22px 20px;
    text-align: center;
    box-shadow: 0 2px 18px rgba(0,0,0,.10);
    border-top: 5px solid {ROJO};
    transition: transform .2s;
    height: 125px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}
.kpi-card:hover {{ transform: translateY(-4px); }}
.kpi-val  {{ font-size: 2.6rem; font-weight: 800; color: {ROJO}; margin: 0; line-height: 1.1; }}
.kpi-lbl  {{ font-size: .95rem; color: #555; text-transform: uppercase; letter-spacing: .8px; margin-top: 6px; }}
.kpi-delta{{ font-size: .9rem; color: {VERDE}; font-weight: 600; margin-top: 4px; }}
.kpi-wrap {{ margin-bottom: 0; }}
.section-title {{
    font-size: 1.35rem; font-weight: 800; color: {ROJO};
    border-left: 5px solid {ROJO}; padding-left: 12px;
    margin: 24px 0 14px;
}}
/* Global font size boost */
.stMarkdown p {{ font-size: 1.05rem; }}
.stDataFrame {{ font-size: 1.05rem; }}
[data-testid="stDataFrame"] th {{ color: #000 !important; font-weight: 800 !important; font-size: 1.1rem !important; background-color: #f8f9fa !important; }}
[data-testid="stDataFrame"] tbody td {{ font-size: 1.05rem !important; }}
.stMultiSelect span, .stSelectbox div {{ font-size: 1.05rem; }}

/* Mapa Plotly: menos “aires” arriba del iframe (título va fuera del Figure) */
[data-testid="stPlotlyChart"] {{
    padding-top: 0 !important;
    margin-top: 0 !important;
}}
[data-testid="stPlotlyChart"] > div {{
    margin-top: 0 !important;
}}

.stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: #fff; border-radius: 14px; padding: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; padding: 10px 26px; font-weight: 700; font-size: 1rem;
    color: #555; border: none; background: transparent;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {ROJO}, {ROJO2}) !important;
    color: #fff !important; box-shadow: 0 3px 14px rgba(123,26,26,.35);
}}

.map-title {{
    margin: 0 0 4px 0;
    padding: 0;
    font-size: 1.05rem;
    font-weight: 800;
    color: {ROJO};
}}

.personal-title {{
    font-size: 1.8rem;
}}

.personal-wrap {{
    display: flex;
    flex-direction: column;
    gap: 20px;
    justify-content: center;
    height: 100%;
    padding: 10px;
}}

.personal-total {{
    background: linear-gradient(135deg, {ROJO}, {ROJO2});
    padding: 25px;
    border-radius: 18px;
    color: white;
    text-align: center;
    box-shadow: 0 6px 20px rgba(123,26,26,0.3);
}}

.personal-total .total-label {{
    margin: 0;
    font-size: 1.6rem;
    font-weight: 600;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

.personal-total .total-value {{
    margin: 5px 0 0;
    font-size: 6.5rem;
    font-weight: 800;
    line-height: 1;
}}

.personal-cards {{
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    justify-content: center;
}}

.personal-card {{
    flex: 1;
    min-width: 110px;
    background: white;
    padding: 15px;
    border-radius: 14px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}}

.personal-card .card-label {{
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #555;
}}

.personal-card .card-value {{
    margin: 5px 0 0;
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
}}

.xaxis-mobile-label {{
    display: none;
    text-align: center;
    font-size: 0.85rem;
    color: #555;
    margin: -6px 0 12px;
}}

.alert-card {{
    background-color: #F5E6E4;
    border: 2px solid #8B1A2B;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: 0 4px 15px rgba(139,26,43,0.2);
}}

.alert-card .alert-icon {{
    font-size: 4.5rem;
    margin-bottom: 10px;
    line-height: 1;
}}

.alert-card .alert-title {{
    color: #8B1A2B;
    margin-top: 0;
    font-size: 1.6rem;
    font-weight: 800;
}}

.alert-card .alert-text {{
    font-size: 1.15rem;
    color: #444;
    margin-bottom: 15px;
}}

@media (max-width: 768px) {{
    .map-title {{ font-size: 0.95rem; }}
    .map-responsive-anchor + div [data-testid="stPlotlyChart"] > div {{
        height: 60vh !important;
        min-height: 320px !important;
        max-height: 520px !important;
    }}
    .personal-title {{ font-size: 1.2rem; }}
    .personal-wrap {{ padding: 6px; gap: 14px; }}
    .personal-total {{ padding: 18px; }}
    .personal-total .total-label {{ font-size: 0.9rem; }}
    .personal-total .total-value {{ font-size: 3.2rem; }}
    .personal-cards {{ gap: 10px; }}
    .personal-card {{ min-width: 140px; flex: 1 1 45%; padding: 12px; }}
    .personal-card .card-label {{ font-size: 0.9rem; }}
    .personal-card .card-value {{ font-size: 1.8rem; }}
    .pers-pie-anchor + div [data-testid="stPlotlyChart"] > div {{
        height: 45vh !important;
        min-height: 300px !important;
        max-height: 420px !important;
    }}
    .xaxis-mobile-label {{ display: block; }}
    .kpi-wrap {{ margin-bottom: 12px; }}
    .kpi-card {{ height: auto; padding: 16px 14px; }}
    .kpi-val {{ font-size: 2.1rem; }}
    .kpi-card.kpi-split {{ flex-direction: column; gap: 10px; }}
    .kpi-card.kpi-split > div {{ width: 100%; }}
    .kpi-card.kpi-split .kpi-divider {{ display: none; }}
    .alert-card {{ padding: 14px; }}
    .alert-card .alert-icon {{ font-size: 3.2rem; }}
    .alert-card .alert-title {{ font-size: 1.2rem; }}
    .alert-card .alert-text {{ font-size: 1rem; margin-bottom: 8px; }}
}}
</style>
""",
    unsafe_allow_html=True,
)

# ── Data loader ──────────────────────────────────────────────────────────────
EXCEL_PATH = os.path.join(DATA_DIR, "data.xlsx")


@st.cache_data
def load_data(_excel_mtime, _excel_size):
    xls = pd.ExcelFile(EXCEL_PATH)
    cp = xls.parse("Carga Procesal")
    cp.columns = ["Año", "Especialidad", "Ingresos", "CargaProcesal", "Resueltos"]
    cp["Especialidad"] = cp["Especialidad"].str.title()
    cp["Especialidad"] = cp["Especialidad"].apply(
        lambda x: "Extinción Dominio" if "Extinci" in str(x) else x
    )
    for _col in ["Ingresos", "CargaProcesal", "Resueltos"]:
        cp[_col] = (
            pd.to_numeric(
                cp[_col].astype(str).str.replace(",", "", regex=False).str.strip(),
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )
    cp["Año"] = pd.to_numeric(cp["Año"], errors="coerce").dropna().astype(int)
    cp = cp.dropna(subset=["Año"])

    pob = xls.parse("Poblacion_Data", skiprows=1)
    pob.columns = [
        "Provincia",
        "Año",
        "TipoAnio",
        "Varones",
        "Mujeres",
        "Total",
        "PctV",
        "PctM",
        "TasaCrec",
    ]
    pob["Provincia"] = pob["Provincia"].apply(
        lambda x: (
            "Concepción"
            if "Concepci" in str(x)
            else ("Junín (prov.)" if "prov" in str(x) else x)
        )
    )

    # Detalle individual: usar hoja "Detalle_Provincia" (refleja registros actualizados por provincia)
    dp_raw = xls.parse("Detalle_Provincia", header=None).iloc[2:, :8].copy()
    dp_raw.columns = [
        "ProvinciaRaw",
        "TipoOrgano",
        "Especialidad",
        "Numero",
        "Sede",
        "Nombre",
        "Sexo",
        "CondicionLabel",
    ]

    dp_rows = []
    current_prov = None
    for _, row in dp_raw.iterrows():
        prov_raw = (
            str(row["ProvinciaRaw"]).strip() if pd.notna(row["ProvinciaRaw"]) else ""
        )
        if prov_raw and "PROVINCIA DE" in prov_raw.upper():
            current_prov = prov_raw.upper().replace("PROVINCIA DE", "").strip()
            continue

        if current_prov is None:
            continue
        if pd.isna(row["TipoOrgano"]) and pd.isna(row["Nombre"]):
            continue

        dp_rows.append(
            {
                "Provincia": current_prov,
                "Sede": row["Sede"],
                "TipoOrgano": row["TipoOrgano"],
                "Especialidad": row["Especialidad"],
                "Numero": row["Numero"],
                "Nombre": row["Nombre"],
                "Sexo": row["Sexo"],
                "CondicionLabel": row["CondicionLabel"],
            }
        )

    dp = pd.DataFrame(dp_rows)
    if not dp.empty:

        def normalize_prov_name(value):
            u = str(value).upper()
            if "HUANCAY" in u:
                return "Huancayo"
            if "TARMA" in u:
                return "Tarma"
            if "JAUJA" in u:
                return "Jauja"
            if "TAYACAJA" in u:
                return "Tayacaja"
            if "CHUPACA" in u:
                return "Chupaca"
            if "CONCEP" in u:
                return "Concepción"
            if "YAULI" in u:
                return "Yauli"
            if u.strip().startswith("JUN"):
                return "Junín"
            return str(value).title()

        dp["Provincia"] = dp["Provincia"].apply(normalize_prov_name)
        dp["Condicion"] = dp["CondicionLabel"].astype(str).str[0]
    else:
        # Fallback por si cambia estructura de "Detalle_Provincia"
        dp = xls.parse("Data_Plana", skiprows=1)
        dp.columns = [
            "Provincia",
            "Sede",
            "TipoOrgano",
            "Especialidad",
            "Numero",
            "Nombre",
            "Sexo",
            "Condicion",
            "CondicionLabel",
        ]

    rp = xls.parse("Resumen_Provincia", skiprows=1)

    # Mapeo dinámico según cantidad de columnas reales
    n_cols = len(rp.columns)
    # Estructura (8 cols): Provincia,Total,JESP,Sala,... sin JPL separado
    col_names_8 = [
        "Provincia",
        "Total",
        "JESP",
        "Sala",
        "Varones",
        "Mujeres",
        "Titulares",
        "SupernProv",
    ]
    # Estructura (9 cols) MAGISTRADOS POR PROVINCIA: J. ESP, JPL, SALA por separado
    col_names_9 = [
        "Provincia",
        "Total",
        "JESP",
        "JPL",
        "Sala",
        "Varones",
        "Mujeres",
        "Titulares",
        "SupernProv",
    ]
    # Estructura legada (10 cols): JPL,JIP,JUP + … → se fusiona a JESP
    col_names_10 = [
        "Provincia",
        "Total",
        "JPL",
        "JIP",
        "JUP",
        "Sala",
        "Varones",
        "Mujeres",
        "Titulares",
        "SupernProv",
    ]

    if n_cols == 9:
        rp.columns = col_names_9
    elif n_cols == 8:
        rp.columns = col_names_8
        rp["JPL"] = 0
    elif n_cols >= 10:
        rp.columns = (
            col_names_10[:n_cols]
            if n_cols <= 10
            else col_names_10 + [f"Extra{i}" for i in range(n_cols - 10)]
        )
        # Convertir formato legado a nuevo: fusionar JPL+JIP+JUP → JESP
        for c in ["JPL", "JIP", "JUP"]:
            if c not in rp.columns:
                rp[c] = 0
        rp["JESP"] = rp["JPL"] + rp["JIP"] + rp["JUP"]
        # JPL/JIP/JUP conservan sus valores por columna; JESP es el total de los tres
        if "Titulares" not in rp.columns:
            rp["Titulares"] = 0
        if "SupernProv" not in rp.columns:
            rp["SupernProv"] = 0
    else:
        # 1–7 cols u otros: nombres parciales
        if n_cols < 8:
            base_cols = col_names_8[:n_cols]
        else:
            base_cols = list(col_names_8) + [
                f"Extra{i}" for i in range(n_cols - len(col_names_8))
            ]
        rp.columns = base_cols
        for missing in [
            "JESP",
            "JPL",
            "Sala",
            "Varones",
            "Mujeres",
            "Titulares",
            "SupernProv",
        ]:
            if missing not in rp.columns:
                rp[missing] = 0
    if "JPL" not in rp.columns:
        rp["JPL"] = 0

    aud = xls.parse("Audiencias_Data")
    aud.columns = [
        "Sede",
        "Año",
        "TipoAnio",
        "Programadas",
        "Atendidas",
        "Suspendidas",
        "TasaAtencion",
    ]

    # Bloque SNEJ dentro de la hoja "Resumen" (encabezado: año, juzgado, ...)
    res_raw = xls.parse("Resumen", header=None)
    snej_header_idx = None
    for idx, val in enumerate(res_raw.iloc[:, 0].astype(str).str.strip().str.lower()):
        if val in ("año", "ano"):
            snej_header_idx = idx
            break
    if snej_header_idx is not None:
        snej = res_raw.iloc[snej_header_idx + 1 :, :7].copy()
        snej.columns = [
            "Año",
            "Juzgado",
            "Programadas",
            "Realizadas",
            "Suspendidas",
            "PctAtencion",
            "PctSuspension",
        ]
        snej = snej.dropna(subset=["Año", "Juzgado"])
        snej = snej[pd.to_numeric(snej["Año"], errors="coerce").notna()].copy()
        snej["Año"] = snej["Año"].astype(int)
        for c in [
            "Programadas",
            "Realizadas",
            "Suspendidas",
            "PctAtencion",
            "PctSuspension",
        ]:
            snej[c] = pd.to_numeric(snej[c], errors="coerce")
        snej = snej.dropna(
            subset=[
                "Programadas",
                "Realizadas",
                "Suspendidas",
                "PctAtencion",
                "PctSuspension",
            ]
        )
        # Abreviaciones SNEJ para visualización consistente
        snej["Juzgado"] = (
            snej["Juzgado"]
            .astype(str)
            .str.strip()
            .str.replace("Juzgado de Investigación Preparatoria", "JIP", regex=False)
            .str.replace("Juzgado de Investigacion Preparatoria", "JIP", regex=False)
            .str.replace("Juzgado de Penal Unipersonal", "JUP", regex=False)
            .str.replace("Juzgado Penal Colegiado Conformado", "JPCC", regex=False)
            .str.replace(
                "Primer Juzgado Penal Colegiado Transitorio", "1 JPCT", regex=False
            )
            .str.replace(
                "Segundo Juzgado Penal Colegiado Transitorio", "2 JPCT", regex=False
            )
            .str.replace("Primer ", "1 ", regex=False)
            .str.replace("Segundo ", "2 ", regex=False)
            .str.replace("Tercer ", "3 ", regex=False)
        )
    else:
        snej = pd.DataFrame(
            columns=[
                "Año",
                "Juzgado",
                "Programadas",
                "Realizadas",
                "Suspendidas",
                "PctAtencion",
                "PctSuspension",
            ]
        )

    # ── Hojas de datos antes hardcodeados ─────────────────────────────────────
    df_alerta = xls.parse("Alerta_Sobrecarga") if "Alerta_Sobrecarga" in xls.sheet_names else pd.DataFrame()
    df_pob_proy = xls.parse("Pob_Proyeccion") if "Pob_Proyeccion" in xls.sheet_names else pd.DataFrame()
    df_jueces = xls.parse("Jueces_Pob_2026") if "Jueces_Pob_2026" in xls.sheet_names else pd.DataFrame()
    df_regimen = xls.parse("Personal_Regimen") if "Personal_Regimen" in xls.sheet_names else pd.DataFrame()
    df_cargos_xls = xls.parse("Personal_Cargos") if "Personal_Cargos" in xls.sheet_names else pd.DataFrame()
    for _c in ["LEY 29277", "728", "276", "CAS", "RECAS", "Total"]:
        if _c in df_cargos_xls.columns:
            df_cargos_xls[_c] = pd.to_numeric(df_cargos_xls[_c], errors="coerce").fillna(0).astype(int)

    return cp, pob, dp, rp, aud, snej, df_alerta, df_pob_proy, df_jueces, df_regimen, df_cargos_xls


excel_mtime = os.path.getmtime(EXCEL_PATH) if os.path.exists(EXCEL_PATH) else 0
excel_size = os.path.getsize(EXCEL_PATH) if os.path.exists(EXCEL_PATH) else 0
cp, pob, dp, rp, aud, snej, df_alerta, df_pob_proy, df_jueces, df_regimen, df_cargos_xls = load_data(excel_mtime, excel_size)

with st.sidebar:
    st.markdown("### 🔄 Datos")
    if st.button("Recargar Excel", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ── HEADER ───────────────────────────────────────────────────────────────────
font_path = _ANDINA_FONT
font_b64 = _font_b64_early

logo_path = os.path.join(_ASSET_IMAGES, "image.png")
if os.path.exists(logo_path):
    logo_b64 = get_base64_of_bin_file(logo_path)
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="logo" style="height: 80px;">'
    )
else:
    logo_html = '<div class="escudo">⚖️</div>'

st.markdown(
    f"""
<div class="header-bar">
  <div class="header-logo">{logo_html}</div>
  <div class="header-text">
    <h1>Corte Superior de Justicia de Junín</h1>
    <h3>Aplicativo Tukuy Rikuy</h3>
    <p>Presidente: Dr. Ricardo Corrales Melgarejo &nbsp;|&nbsp; Gestión: 2025-2026 &nbsp;|&nbsp; Justicia pronta, honesta e inclusiva.</p>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── KPIs globales ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f"""
    <div class="kpi-wrap">
      <div class="kpi-card">
        <div class="kpi-val">121</div>
        <div class="kpi-lbl">Jueces y Juezas</div>
        <div class="kpi-delta" style="font-size:1.2rem; font-weight:600; color:#555;">101 Órganos Jurisdiccionales</div>
      </div>
    </div>""",
        unsafe_allow_html=True,
    )

with c2:
    juez_path = os.path.join(_ASSET_IMAGES, "juez.png")
    jueza_path = os.path.join(_ASSET_IMAGES, "jueza.png")
    juez_b64 = get_base64_of_bin_file(juez_path) if os.path.exists(juez_path) else ""
    jueza_b64 = get_base64_of_bin_file(jueza_path) if os.path.exists(jueza_path) else ""

    juez_icon = (
        f'<img src="data:image/png;base64,{juez_b64}" style="height:22px; vertical-align:middle; margin-right:5px; margin-bottom:3px;">'
        if juez_b64
        else "♂ "
    )
    jueza_icon = (
        f'<img src="data:image/png;base64,{jueza_b64}" style="height:22px; vertical-align:middle; margin-right:5px; margin-bottom:3px;">'
        if jueza_b64
        else "♀ "
    )

    st.markdown(
        f"""
    <div class="kpi-wrap">
      <div class="kpi-card kpi-split" style="display:flex; flex-direction:row; justify-content:space-around; align-items:center;">
        <div style="text-align:center;">
          <div style="font-size:3.2rem; font-weight:800; color:#01497c; line-height:1;">80</div>
          <div style="font-size:1.2rem; font-weight:600; color:#555; margin-top:2px;">{juez_icon}Varones</div>
        </div>
        <div class="kpi-divider" style="width:2px; height:50px; background:#eee;"></div>
        <div style="text-align:center;">
          <div style="font-size:3.2rem; font-weight:800; color:#ff97b7; line-height:1;">41</div>
          <div style="font-size:1.2rem; font-weight:600; color:#555; margin-top:2px;">{jueza_icon}Mujeres</div>
        </div>
      </div>
    </div>""",
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
    <div class="kpi-wrap">
      <div class="kpi-card kpi-split" style="display:flex; flex-direction:row; justify-content:space-around; align-items:center;">
        <div style="text-align:center;">
          <div style="font-size:2.8rem; font-weight:800; color:{VERDE}; line-height:1;">47</div>
          <div style="font-size:1.1rem; font-weight:600; color:#555; margin-top:2px;">Titulares</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:2.8rem; font-weight:800; color:{ROJO}; line-height:1;">51</div>
          <div style="font-size:1.1rem; font-weight:600; color:#555; margin-top:2px;">Supernumerarios</div>
        </div>
        <div style="text-align:center;">
          <div style="font-size:2.8rem; font-weight:800; color:#e67e22; line-height:1;">23</div>
          <div style="font-size:1.1rem; font-weight:600; color:#555; margin-top:2px;">Provisionales</div>
        </div>
      </div>
    </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────
T_POB, T_RES, T_CAR, T_AUD, T_PER = st.tabs(
    [
        "📈  Proyecciones Poblacionales",
        "🏛️  Resumen & Detalle Provincia",
        "📂  Carga Procesal",
        "🎙️  Audiencias",
        "👥  Personal Jurisdiccional",
    ]
)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — CARGA PROCESAL
# ═══════════════════════════════════════════════════════════════════════════
with T_CAR:
    st.markdown(
        '<div class="section-title">Evolución de la Carga Procesal por Especialidad en Trámite</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="margin: 6px 0 14px 0; display: flex; flex-wrap: wrap; gap: 10px;">
            <a href="https://drive.google.com/file/d/1SGrXdbKbevXpjRKkMHKs3RiILczEFTyF/view?usp=sharing" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
                <span style="display: inline-block; background: linear-gradient(135deg, #8B1A2B 0%, #6B0F1A 100%); color: #ffffff; padding: 10px 18px; border-radius: 10px; font-weight: 800; font-size: 1rem; letter-spacing: 0.3px; box-shadow: 0 4px 12px rgba(107,15,26,0.35);">
                    VER BOLETIN
                </span>
            </a>
            <a href="https://drive.google.com/file/d/1pRExmTMKLBpif4rcb8J8_u0AlRZJFZ8m/view?usp=sharing" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
                <span style="display: inline-block; background: linear-gradient(135deg, #1565C0 0%, #0D47A1 100%); color: #ffffff; padding: 10px 18px; border-radius: 10px; font-weight: 800; font-size: 1rem; letter-spacing: 0.3px; box-shadow: 0 4px 12px rgba(21,101,192,0.35);">
                    RESUMEN 2026
                </span>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cp_resumen = (
        cp.groupby("Año", as_index=False)[["Ingresos", "CargaProcesal", "Resueltos"]]
        .sum()
        .rename(columns={"CargaProcesal": "Carga Procesal"})
    )
    cp_resumen_long = cp_resumen.melt(
        id_vars="Año",
        value_vars=["Ingresos", "Carga Procesal", "Resueltos"],
        var_name="Indicador",
        value_name="Cantidad",
    )
    fig_resumen_cp = px.bar(
        cp_resumen_long,
        x="Año",
        y="Cantidad",
        color="Indicador",
        barmode="group",
        title="<b>Resumen Anual: Ingresos, Carga Procesal y Resueltos</b>",
        color_discrete_map={
            "Ingresos": "#1f77b4",
            "Carga Procesal": "#ff7f0e",
            "Resueltos": "#2ca02c",
        },
        text=cp_resumen_long["Cantidad"].apply(lambda v: f"{v:,.0f}"),
    )
    fig_resumen_cp.update_traces(
        textposition="outside",
        textfont=dict(size=14, color="#333333"),
        cliponaxis=False,
    )
    fig_resumen_cp.update_layout(
        template="custom_theme",
        legend_title="",
        legend=dict(
            orientation="h",
            y=-0.05,
            x=0.5,
            xanchor="center",
            yanchor="top",
        ),
        height=520,
        title_font_size=16,
        xaxis=dict(title="", tickfont=dict(size=14)),
        yaxis=dict(title="", tickformat=",", tickfont=dict(size=14)),
        margin=dict(b=40, t=70, l=40, r=20),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    st.plotly_chart(fig_resumen_cp, width="stretch", theme=None)

    ESP_COLORS = {
        "Civil": "#00ACC1",
        "Constitucional": "#1565C0",
        "Extinción Dominio": "#6A1B9A",
        "Familia": "#D81B60",
        "Laboral": "#F9A825",
        "Penal": "#6B0F1A",
    }

    # Inject CSS to color each multiselect chip with its chart color
    chip_css_rules = ""
    for esp_name, esp_color in ESP_COLORS.items():
        # Use attribute selector on the chip text to target each specialty
        chip_css_rules += f"""
        [data-baseweb="tag"] span[title="{esp_name}"] ~ div,
        [data-baseweb="tag"]:has(span[title="{esp_name}"]) {{
            background-color: {esp_color} !important;
            color: #ffffff !important;
            border: 1.5px solid {esp_color} !important;
        }}
        """
    st.markdown(f"<style>{chip_css_rules}</style>", unsafe_allow_html=True)

    esp_all = sorted(cp["Especialidad"].unique())

    sel_esp = st.multiselect(
        "Filtrar especialidades:", esp_all, default=esp_all, key="esp"
    )
    anio_range = st.slider(
        "Rango de años:",
        int(cp["Año"].min()),
        int(cp["Año"].max()),
        (int(cp["Año"].min()), int(cp["Año"].max())),
        key="anio_cp",
    )
    df_cp = cp[cp["Especialidad"].isin(sel_esp) & cp["Año"].between(*anio_range)]

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.line(
            df_cp,
            x="Año",
            y="Ingresos",
            color="Especialidad",
            markers=True,
            title="<b>Ingresos por Año</b>",
            color_discrete_map=ESP_COLORS,
        )
        fig.update_layout(
            template="custom_theme",
            legend_title="",
            height=450,
            title_font_size=16,
            legend=dict(font=dict(size=18), title=dict(font=dict(size=18))),
            xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
        )
        st.plotly_chart(fig, width="stretch", theme=None)
    with col_b:
        fig2 = px.bar(
            df_cp,
            x="Año",
            y="Resueltos",
            color="Especialidad",
            barmode="group",
            title="<b>Expedientes Resueltos</b>",
            color_discrete_map=ESP_COLORS,
        )
        fig2.update_layout(
            template="custom_theme",
            legend_title="",
            height=450,
            title_font_size=16,
            legend=dict(font=dict(size=18), title=dict(font=dict(size=18))),
            xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
        )
        st.plotly_chart(fig2, width="stretch", theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        fig3 = px.bar(
            df_cp,
            x="Año",
            y="CargaProcesal",
            color="Especialidad",
            barmode="stack",
            title="<b>Carga Procesal Acumulada</b>",
            color_discrete_map=ESP_COLORS,
        )
        fig3.update_layout(
            template="custom_theme",
            legend_title="",
            height=450,
            title_font_size=16,
            legend=dict(font=dict(size=18), title=dict(font=dict(size=18))),
            xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
        )
        st.plotly_chart(fig3, width="stretch", theme=None)
    with col_d:
        df_ratio = df_cp.copy()
        df_ratio["Tasa_Resolucion"] = (
            df_ratio["Resueltos"] / df_ratio["Ingresos"].replace(0, 1) * 100
        ).round(2)
        fig4 = px.line(
            df_ratio,
            x="Año",
            y="Tasa_Resolucion",
            color="Especialidad",
            markers=True,
            title="<b>Tasa de Resolución (%)</b>",
            color_discrete_map=ESP_COLORS,
        )
        fig4.add_hline(
            y=100, line_dash="dash", line_color="#4A7C59", annotation_text="100%"
        )
        fig4.update_layout(
            template="custom_theme",
            legend_title="",
            height=450,
            title_font_size=16,
            legend=dict(font=dict(size=18), title=dict(font=dict(size=18))),
            xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)),
        )
        st.plotly_chart(fig4, width="stretch", theme=None)

    with st.expander("🗂️ Ver tabla de datos"):
        st.dataframe(df_cp.reset_index(drop=True), width="stretch")

    st.markdown(
        '<div class="section-title" style="color: #8B1A2B; border-left-color: #8B1A2B;">⚠️ Alerta: Situación de Carga Procesal Proyectada a Diciembre 2026</div>',
        unsafe_allow_html=True,
    )

    # Datos de alerta leídos desde la hoja Alerta_Sobrecarga del Excel
    df_alert = df_alerta.copy()
    df_alert.columns = ["ÓRGANOS JURISDICCIONALES", "CARGA_MÁXIMA", "CARGA_PROYECTADA", "PORC_SOBRECARGA"]
    df_alert["ÓRGANO_ABREV"] = (
        df_alert["ÓRGANOS JURISDICCIONALES"]
        .str.replace("JUZGADO DE INVESTIGACIÓN PREPARATORIA", "JIP", regex=False)
        .str.replace("JUZGADO PENAL UNIPERSONAL", "JUP", regex=False)
        .str.replace(
            "SUPRAPROVINCIAL ESPECIALIZADO EN DELITOS DE CORRUPCIÓN DE FUNCIONARIOS",
            "SUPRA ESP. CORRUPCIÓN",
            regex=False,
        )
        .str.replace(
            "SUPRAPROVINCIAL ESPECIALIZADO EN DELITO DE CORRUPCIÓN DE FUNCIONARIOS",
            "SUPRA ESP. CORRUPCIÓN",
            regex=False,
        )
        .str.replace("DE HUANCAYO", "HUANCAYO", regex=False)
        .str.replace("DE CHUPACA", "CHUPACA", regex=False)
    )
    df_alert["SOBRECARGA"] = df_alert["CARGA_PROYECTADA"] - df_alert["CARGA_MÁXIMA"]
    df_alert["ESTADO"] = "SOBRECARGA"

    st.markdown(
        f"""
        <div class="alert-card">
            <div class="alert-icon">🚨</div>
            <h3 class="alert-title">ALERTA CRÍTICA</h3>
            <p class="alert-text">
                Se proyecta que <b>{len(df_alert)}</b> órganos jurisdiccionales alcanzarán un estado crítico de <b>sobrecarga procesal</b> para <b>Diciembre de 2026</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_alert_plot = df_alert.copy()
    fig_alert = go.Figure()
    fig_alert.add_trace(
        go.Bar(
            y=df_alert_plot["ÓRGANO_ABREV"],
            x=df_alert_plot["CARGA_MÁXIMA"],
            orientation="h",
            name="Carga máxima",
            marker_color="#C9CED6",
            customdata=df_alert_plot[["ÓRGANOS JURISDICCIONALES"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>" "Carga máxima: %{x:,.0f}<extra></extra>"
            ),
        )
    )
    fig_alert.add_trace(
        go.Bar(
            y=df_alert_plot["ÓRGANO_ABREV"],
            x=df_alert_plot["SOBRECARGA"],
            orientation="h",
            name="Sobrecarga",
            marker_color="#8B1A2B",
            customdata=df_alert_plot[
                ["ÓRGANOS JURISDICCIONALES", "CARGA_PROYECTADA"]
            ].values,
            text=df_alert_plot["SOBRECARGA"].map(lambda v: f"+{v:,.0f}"),
            textposition="outside",
            textfont=dict(size=14, color="#6B0F1A"),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Carga proyectada: %{customdata[1]:,.0f}<br>"
                "Sobrecarga: %{x:,.0f}<br>"
                "Diferencia: +%{x:,.0f}<extra></extra>"
            ),
        )
    )
    fig_alert.update_layout(
        template="custom_theme",
        height=700,
        title_font_size=18,
        title="<b>Órganos en Sobrecarga: Carga Máxima vs Proyectada (Dic. 2026)</b>",
        barmode="stack",
        xaxis=dict(
            title="Expedientes",
            tickformat=",.0f",
            title_font=dict(size=16),
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=12),
            categoryorder="array",
            categoryarray=df_alert_plot["ÓRGANO_ABREV"].tolist()[::-1],
        ),
        legend=dict(orientation="h", y=1.0, x=0, yanchor="bottom", font=dict(size=13)),
        margin=dict(l=10, r=30, t=95, b=10),
    )
    st.plotly_chart(fig_alert, width="stretch", theme=None)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — PROYECCIONES POBLACIONALES
# ═══════════════════════════════════════════════════════════════════════════
with T_POB:
    st.markdown(
        '<div class="section-title">Proyecciones Poblacionales — Región Junín  2026 - 2031 (Fuente: Población Proyectada INEI al 2026)</div>',
        unsafe_allow_html=True,
    )

    pob_provs = pob[pob["Provincia"] != "Junín (región)"].copy()
    provs = sorted(pob_provs["Provincia"].unique())

    # Colores de altísimo contraste para evitar confusiones visuales
    DISTINCT_COLORS = [
        "#1565C0",  # Azul
        "#D81B60",  # Rosa
        "#2E7D32",  # Verde
        "#F9A825",  # Amarillo
        "#00ACC1",  # Celeste
        "#F4511E",  # Naranja
        "#5D4037",  # Marrón
        "#6A1B9A",  # Morado
        "#E53935",  # Rojo
        "#6B0F1A",  # Guindo
        "#546E7A",  # Gris
    ]
    PROV_COLORS = {
        prov: DISTINCT_COLORS[i % len(DISTINCT_COLORS)] for i, prov in enumerate(provs)
    }

    chip_css_rules_prov = ""
    for prov_name, prov_color in PROV_COLORS.items():
        chip_css_rules_prov += f"""
        .st-key-prov_pob [data-baseweb="tag"]:has(span[title="{prov_name}"]),
        .st-key-prov_pob [data-baseweb="tag"]:has(span[aria-label="{prov_name}"]) {{
            background-color: {prov_color} !important;
            color: #ffffff !important;
            border: 1.5px solid {prov_color} !important;
        }}
        .st-key-prov_pob [data-baseweb="tag"]:has(span[title="{prov_name}"]) span,
        .st-key-prov_pob [data-baseweb="tag"]:has(span[aria-label="{prov_name}"]) span {{
            color: #ffffff !important;
        }}
        """
    st.markdown(f"<style>{chip_css_rules_prov}</style>", unsafe_allow_html=True)

    sel_prov_pob = st.multiselect(
        "Seleccionar provincias:", provs, default=provs, key="prov_pob"
    )
    df_pb = pob_provs[pob_provs["Provincia"].isin(sel_prov_pob)]

    # Proyecciones leídas desde la hoja Pob_Proyeccion del Excel
    _year_cols = [c for c in df_pob_proy.columns if str(c).isdigit()]
    _pob_proj_data = []
    for _, _row in df_pob_proy.iterrows():
        for _yr_col in _year_cols:
            _pob_proj_data.append({"Provincia": _row["Provincia"], "Año": int(_yr_col), "Total": int(_row[_yr_col])})
    df_pb_proj = pd.DataFrame(_pob_proj_data)
    df_pb_proj = df_pb_proj[df_pb_proj["Provincia"].isin(sel_prov_pob)]

    _tasas_html = " &nbsp;|&nbsp; ".join(
        f"{r['Provincia']}: <b>{r['TasaCrec']:+.1f}%</b>"
        for _, r in df_pob_proy.iterrows()
    )
    st.markdown(
        f"""
        <div style="display:flex; justify-content:flex-end; margin: 4px 0 10px 0;">
            <div style="background: linear-gradient(135deg, #ffffff 0%, #f8ecef 100%); border: 1.5px solid #8B1A2B; border-radius: 12px; padding: 8px 12px; box-shadow: 0 2px 10px rgba(139,26,43,0.12);">
                <div style="font-size: 0.86rem; color: #6B0F1A; font-weight: 800; margin-bottom: 3px;">Tasas de crecimiento anual (INEI)</div>
                <div style="font-size: 0.78rem; color: #333; line-height: 1.5;">{_tasas_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig = px.line(
        df_pb_proj,
        x="Año",
        y="Total",
        color="Provincia",
        markers=True,
        title="<b>Población Total Proyectada</b>",
        color_discrete_map=PROV_COLORS,
        labels={"Total": "Población", "Año": "Año", "Provincia": "Provincia"},
    )
    fig.update_layout(
        template="custom_theme",
        height=360,
        title_font_size=16,
        yaxis_title="Población",
        margin=dict(t=60, r=20, b=30, l=20),
    )
    st.plotly_chart(fig, width="stretch", theme=None)

    st.markdown(
        '<div class="section-title">Jueces por Población (Proyección 2026)</div>',
        unsafe_allow_html=True,
    )
    # Jueces por población leídos desde la hoja Jueces_Pob_2026 del Excel
    ind_2026 = df_jueces.rename(columns={
        "CATEGORIA": "CATEGORÍA",
        "CANTIDAD_JUECES": "CANTIDAD DE JUECES",
        "PROY_POB_2026": "PROYECCIÓN DE POBLACIÓN AL 2026",
        "JUECES_POR_100K": "CANTIDAD DE JUECES POR POBLACIÓN",
    })
    ind_2026["COLOR"] = ind_2026["CATEGORÍA"].apply(
        lambda c: (
            "#8B1A2B"
            if "DISTRITO JUDICIAL" in c
            else ("#1565C0" if "Huancayo" in c else "#C4952A")
        )
    )
    fig_ind = go.Figure(
        go.Bar(
            y=ind_2026["CATEGORÍA"],
            x=ind_2026["CANTIDAD DE JUECES POR POBLACIÓN"],
            orientation="h",
            marker_color=ind_2026["COLOR"],
            text=ind_2026["CANTIDAD DE JUECES POR POBLACIÓN"].map(lambda v: f"{v}"),
            textposition="outside",
            customdata=ind_2026[
                ["CANTIDAD DE JUECES", "PROYECCIÓN DE POBLACIÓN AL 2026"]
            ].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Jueces: %{customdata[0]:,.0f}<br>"
                "Población 2026: %{customdata[1]:,.0f}<br>"
                "Jueces por 100 mil hab.: %{x}<extra></extra>"
            ),
        )
    )
    fig_ind.update_layout(
        template="custom_theme",
        title="<b>Cantidad de Jueces por cada 100 mil Habitantes</b>",
        height=460,
        title_font_size=16,
        xaxis_title="Jueces por cada 100 mil habitantes",
        xaxis_title_font=dict(size=12),
        yaxis_title="",
        margin=dict(l=10, r=40, t=45, b=60),
    )
    fig_ind.update_yaxes(autorange="reversed")
    col_ind_graph, col_ind_note = st.columns([4, 1])
    with col_ind_graph:
        st.plotly_chart(fig_ind, width="stretch", theme=None)
        st.markdown(
            '<div class="xaxis-mobile-label">Jueces por 100 mil habitantes</div>',
            unsafe_allow_html=True,
        )
    with col_ind_note:
        st.markdown(
            """
            <div style="background: #fff7ef; border: 1.5px solid #d8b98a; border-left: 5px solid #8B1A2B; border-radius: 10px; padding: 10px 12px; margin: 34px 0 12px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                <div style="font-size: 0.83rem; color: #8B1A2B; font-weight: 800; margin-bottom: 6px;">
                    Fuente y notas
                </div>
                <div style="font-size: 0.78rem; color: #5a4a36; line-height: 1.4;">
                    <div><b>(1)</b> Población a nivel nacional elaborada por el Instituto Nacional de Estadística e Informática (INEI), sobre la base de las proyecciones de población 2018-2026; información preliminar y de carácter referencial. Se presenta la cantidad de jueces por cada 100 mil habitantes.</div>
                    <div style="margin-top: 5px;"><b>(2)</b> Población del Distrito Judicial de Junín elaborada por la Coordinación de Estudios, Proyectos y Racionalización de la Corte Superior de Justicia de Junín, considerando la población de las provincias que lo conforman. Se presenta la cantidad de jueces por cada 100 mil habitantes.</div>
                    <div style="margin-top: 5px;"><b>(3)</b> Huancayo. Se presenta la cantidad de jueces por cada 100 mil habitantes.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_c, col_d = st.columns(2)
    with col_c:
        df_melt = df_pb.melt(
            id_vars=["Provincia", "Año"],
            value_vars=["Varones", "Mujeres"],
            var_name="Sexo",
            value_name="Poblacion",
        )

        n_provs = len(df_pb["Provincia"].unique())
        n_rows = (n_provs + 1) // 2
        fig3_height = max(400, n_rows * 200)

        fig3 = px.line(
            df_melt,
            x="Año",
            y="Poblacion",
            color="Sexo",
            facet_col="Provincia",
            facet_col_wrap=2,
            title="<b>Varones vs Mujeres por Provincia</b>",
            color_discrete_map={"Varones": "#01497c", "Mujeres": "#ff97b7"},
        )
        fig3.update_traces(mode="lines+markers")
        fig3.update_yaxes(matches=None, showticklabels=True)
        fig3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig3.update_layout(
            template="custom_theme",
            height=fig3_height,
            title_font_size=16,
            legend=dict(
                orientation="h",
                y=-0.1,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            margin=dict(t=50, b=80, l=10, r=10),
        )
        st.plotly_chart(fig3, width="stretch", theme=None)
    with col_d:
        df_2031 = pob_provs[pob_provs["Año"] == 2031].sort_values(
            "Total", ascending=True
        )

        fig4 = go.Figure(
            go.Bar(
                y=df_2031["Provincia"],
                x=df_2031["Total"],
                orientation="h",
                marker=dict(
                    color=[PROV_COLORS.get(p, "#1565C0") for p in df_2031["Provincia"]]
                ),
                text=df_2031["Total"].apply(lambda x: f"{x:,.0f}"),
                textposition="outside",
            )
        )
        fig4.update_layout(
            template="custom_theme",
            title="<b>Población Proyectada 2031 por Provincia</b>",
            height=fig3_height,
            title_font_size=16,
            xaxis_title="Habitantes",
        )
        st.plotly_chart(fig4, width="stretch", theme=None)

    with st.expander("🗂️ Ver tabla de datos"):
        df_show = df_pb.copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — RESUMEN & DETALLE PROVINCIA
# ═══════════════════════════════════════════════════════════════════════════
with T_RES:
    st.markdown(
        '<div class="section-title">Mapa Interactivo — Distrito Judicial de Junín</div>',
        unsafe_allow_html=True,
    )

    rp_filt = rp[rp["Provincia"] != "TOTAL CSJJ"].copy()
    _total_row = rp[rp["Provincia"] == "TOTAL CSJJ"]
    _tot = int(_total_row["Total"].values[0]) if not _total_row.empty else int(rp_filt["Total"].sum())
    _var = int(_total_row["Varones"].values[0]) if not _total_row.empty else int(rp_filt["Varones"].sum())
    _muj = int(_total_row["Mujeres"].values[0]) if not _total_row.empty else int(rp_filt["Mujeres"].sum())

    # Resumen de jueces (magistrados)
    st.markdown(
        f"""
        <div style="background: #eef2f6; padding: 12px 20px; border-radius: 8px; margin-bottom: 16px; border-left: 5px solid {AZUL};">
            <strong style="color: {AZUL}; font-size: 1.15rem;">Resumen General CSJJ:</strong>
            <span style="font-size: 1.1rem; margin-left: 10px;">
                <b>{_var}</b> Jueces (Varones) | <b>{_muj}</b> Juezas (Mujeres) | <b>{_tot}</b> Total
            </span>
        </div>
    """,
        unsafe_allow_html=True,
    )

    GEOJSON_PATH = os.path.join(DATA_DIR, "peru_provincial_simple.geojson")
    PROVINCIAS_DJ = {
        "HUANCAYO",
        "TARMA",
        "JAUJA",
        "CHUPACA",
        "CONCEPCION",
        "YAULI",
        "JUNIN",
        "TAYACAJA",
    }
    PROV_MAP = {
        "HUANCAYO": "Huancayo",
        "TARMA": "Tarma",
        "JAUJA": "Jauja",
        "CHUPACA": "Chupaca",
        "CONCEPCION": "Concepción",
        "YAULI": "Yauli",
        "JUNIN": "Junín",
        "TAYACAJA": "Tayacaja",
    }

    # Selector de variable para colorear el mapa
    VAR_OPTIONS = {
        "Total Jueces y Juezas": "Total",
        "Jueces (Varones)": "Varones",
        "Juezas (Mujeres)": "Mujeres",
        "Juzgados Especializados (J. ESP)": "JESP",
        "Juzgados de Paz Letrado (JPL)": "JPL",
        "Salas": "Sala",
        "Titulares": "Titulares",
        "Supernumerarios/Provisionales": "SupernProv",
    }
    sel_var_label = st.selectbox(
        "🎨 Variable a visualizar en el mapa:",
        list(VAR_OPTIONS.keys()),
        index=0,
        key="map_var",
    )
    sel_var = VAR_OPTIONS[sel_var_label]

    col_map, col_charts = st.columns([3, 2])
    map_row_h = 560  # se recalcula en col_map según bbox (fallback para col_charts)
    with col_map:
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            geo_all = json.load(f)
        geo_dj = {
            "type": "FeatureCollection",
            "features": [
                ft
                for ft in geo_all["features"]
                if ft["properties"].get("NOMBPROV", "") in PROVINCIAS_DJ
            ],
        }

        # Enrich features with ALL variables
        rp_lookup_all = {row["Provincia"]: row for _, row in rp_filt.iterrows()}
        for ft in geo_dj["features"]:
            key = ft["properties"]["NOMBPROV"]
            prov_label = PROV_MAP.get(key, key.title())
            row_data = rp_lookup_all.get(prov_label, {})
            ft["properties"]["PROV_LABEL"] = prov_label
            ft["properties"]["Jueces y Juezas"] = (
                _safe_int(row_data.get("Total", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["VARONES"] = (
                _safe_int(row_data.get("Varones", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["MUJERES"] = (
                _safe_int(row_data.get("Mujeres", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["JESP"] = (
                _safe_int(row_data.get("JESP", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["JPL"] = (
                _safe_int(row_data.get("JPL", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["SALA"] = (
                _safe_int(row_data.get("Sala", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["TITULARES"] = (
                _safe_int(row_data.get("Titulares", 0)) if hasattr(row_data, "get") else 0
            )
            ft["properties"]["SUPERN"] = (
                _safe_int(row_data.get("SupernProv", 0)) if hasattr(row_data, "get") else 0
            )

        # Map variable → GeoJSON field name
        GEO_FIELD = {
            "Total": "Jueces y Juezas",
            "Varones": "VARONES",
            "Mujeres": "MUJERES",
            "JESP": "JESP",
            "JPL": "JPL",
            "Sala": "SALA",
            "Titulares": "TITULARES",
            "SupernProv": "SUPERN",
        }
        geo_field = GEO_FIELD[sel_var]

        # Color scales per variable removed to use PLOTLY_CSCALES globally

        # Pre-calculate bounds from province geometries
        all_lats, all_lons = [], []
        for ft in geo_dj["features"]:
            coords = ft["geometry"]["coordinates"]
            geom_type = ft["geometry"]["type"]
            if geom_type == "Polygon":
                for ring in coords:
                    for lon, lat in ring:
                        all_lats.append(lat)
                        all_lons.append(lon)
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        for lon, lat in ring:
                            all_lats.append(lat)
                            all_lons.append(lon)

        sw = [min(all_lats), min(all_lons)] if all_lats else [-12.5, -75.5]
        ne = [max(all_lats), max(all_lons)] if all_lats else [-11.0, -74.5]
        center_lat = (sw[0] + ne[0]) / 2
        center_lon = (sw[1] + ne[1]) / 2

        # Altura del mapa (~ratio bbox geográfico) para evitar letterboxing vertical
        # (figura muy alta + zona horizontal → bandas vacías arriba/abajo).
        _dlat = max(ne[0] - sw[0], 0.06)
        _dlon = max(ne[1] - sw[1], 0.06)
        _mid_lat_rad = math.radians((sw[0] + ne[0]) / 2)
        _geo_aspect = (_dlon * math.cos(_mid_lat_rad)) / _dlat
        _est_map_w_px = 520
        map_row_h = int(_est_map_w_px / max(_geo_aspect, 0.35))
        map_row_h = max(320, min(map_row_h, 680))

        # ── Mapa Plotly 100% offline (go.Choroplethmapbox + white-bg) ────────
        map_df = rp_filt[["Provincia", sel_var]].copy()

        CS_GUINDO = [[0, "#F5E6E4"], [0.5, "#C4748A"], [1, "#8B1A2B"]]
        CS_AZUL = [[0, "#B8D4EE"], [0.5, "#5B9BD5"], [1, "#2E6DA4"]]
        CS_VERDE = [[0, "#C8E6C9"], [0.5, "#7DB88A"], [1, "#4A7C59"]]
        CS_TIERRA = [[0, "#F2E8D9"], [0.5, "#D4A574"], [1, "#B5622B"]]
        CS_VIOLETA = [[0, "#EDE3F5"], [0.5, "#B89CC8"], [1, "#7B4F8E"]]
        CS_DORADO = [[0, "#FAF0C8"], [0.5, "#E8C568"], [1, "#C4952A"]]
        CS_VARONES = [[0, "#e6f0f7"], [0.5, "#4682B4"], [1, "#01497c"]]
        CS_MUJERES = [[0, "#ffeef3"], [0.5, "#ffb8cd"], [1, "#ff97b7"]]

        CS_CELESTE_MAP = [[0, "#E0F7FA"], [0.5, "#4DD0E1"], [1, "#00838F"]]
        PLOTLY_CSCALES = {
            "Total": CS_GUINDO,
            "Varones": CS_VARONES,
            "Mujeres": CS_MUJERES,
            "JESP": CS_DORADO,
            "JPL": CS_CELESTE_MAP,
            "Sala": CS_GUINDO,
            "Titulares": CS_VERDE,
            "SupernProv": CS_TIERRA,
        }

        # Construir hover personalizado
        hover_texts = []
        for _, row in map_df.iterrows():
            prov = row["Provincia"]
            # Buscar la feature correspondiente
            feat_data = None
            for ft in geo_dj["features"]:
                if ft["properties"].get("PROV_LABEL") == prov:
                    feat_data = ft["properties"]
                    break
            if feat_data:
                hover_texts.append(
                    f"📍 {feat_data['PROV_LABEL']}<br>"
                    f"⚖️ Jueces y Juezas: {feat_data['Jueces y Juezas']}<br>"
                    f"♂ Jueces: {feat_data['VARONES']}  ♀ Juezas: {feat_data['MUJERES']}<br>"
                    f"J. Esp.: {feat_data['JESP']}  JPL: {feat_data['JPL']}  Salas: {feat_data['SALA']}<br>"
                    f"Titulares: {feat_data['TITULARES']}  Supern.: {feat_data['SUPERN']}"
                )
            else:
                hover_texts.append(prov)

        fig_map = go.Figure(
            go.Choropleth(
                geojson=geo_dj,
                locations=map_df["Provincia"],
                featureidkey="properties.PROV_LABEL",
                z=map_df[sel_var],
                colorscale=PLOTLY_CSCALES.get(sel_var, "OrRd"),
                marker_line_color="#6B0F1A",
                marker_line_width=2,
                text=hover_texts,
                hoverinfo="text",
                colorbar=dict(
                    title=dict(text=sel_var_label, font=dict(size=12)),
                    tickfont=dict(size=11),
                    orientation="h",
                    x=0.5,
                    xpad=2,
                    xanchor="center",
                    y=-0.18,
                    yanchor="top",
                    len=0.8,
                    thickness=11,
                ),
            )
        )

        # ── Etiquetas de provincia sobre el mapa ─────────────────────────
        label_lats, label_lons, label_texts = [], [], []
        for ft in geo_dj["features"]:
            prov_label = ft["properties"].get("PROV_LABEL", "")
            lat, lon = _label_point_latlon_for_feature(ft)
            if lat is not None and lon is not None:
                label_lats.append(lat)
                label_lons.append(lon)
                label_texts.append(prov_label.upper())

        # Capa inferior con trazo muy fino para mejorar legibilidad
        fig_map.add_trace(
            go.Scattergeo(
                lat=label_lats,
                lon=label_lons,
                mode="text",
                text=label_texts,
                textfont=dict(
                    size=12,
                    color="rgba(255,255,255,0.92)",
                    family="Arial Black, Inter, sans-serif",
                ),
                textposition="middle center",
                hoverinfo="none",
                showlegend=False,
            )
        )

        fig_map.add_trace(
            go.Scattergeo(
                lat=label_lats,
                lon=label_lons,
                mode="text",
                text=label_texts,
                textfont=dict(
                    size=11, color="#000000", family="Arial Black, Inter, sans-serif"
                ),
                textposition="middle center",
                hoverinfo="none",
                showlegend=False,
            )
        )

        fig_map.update_layout(
            geo=dict(
                fitbounds="locations",
                visible=False,
                bgcolor="rgba(242,232,217,0)",
                domain=dict(x=[0,1], y=[0,1]),
            ),
            template="custom_theme",
            height=map_row_h,
            autosize=True,
            margin=dict(l=2, r=20, t=0, b=2, pad=80),
            title=None,
            paper_bgcolor="rgba(242,232,217,0)",
        )
        # Título fuera del Figure: Plotly reserva mucho espacio vertical al `layout.title`
        st.markdown(
            f'<p class="map-title">Mapa: {sel_var_label} por provincia</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="map-responsive-anchor"></div>', unsafe_allow_html=True)
        st.plotly_chart(
            fig_map,
            use_container_width=True,
            theme=None,
            config={"displayModeBar": True, "responsive": True},
        )

        clicked_prov = None

    # ── Side charts (full height, bigger) ──────────────────────────────
    with col_charts:
        # Horizontal bar — dynamic variable
        fig_bar = px.bar(
            rp_filt.sort_values(sel_var),
            x=sel_var,
            y="Provincia",
            orientation="h",
            color=sel_var,
            color_continuous_scale=PLOTLY_CSCALES.get(sel_var, CS_GUINDO),
            title=f"<b>{sel_var_label} por Provincia</b>",
            text=sel_var,
        )
        fig_bar.update_traces(textposition="outside", textfont_size=13)
        fig_bar.update_layout(
            template="custom_theme",
            height=map_row_h,
            title_font_size=16,
            coloraxis_showscale=False,
            margin=dict(l=10, r=40, t=36, b=10),
            yaxis_title="",
            xaxis_title="",
        )
        st.plotly_chart(fig_bar, use_container_width=True, theme=None)

    # ── Gráficos resumen ────────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">Análisis Comparativo por Provincia</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        rp_plot = rp_filt.copy()
        fig = px.bar(
            rp_plot,
            x="Provincia",
            y=["Sala", "JPL", "JESP"],
            title="<b>Órganos Jurisdiccionales por Instancia</b>",
            labels={
                "value": "Cantidades",
                "variable": "Tipo",
                "JESP": "J. Especializados",
                "JPL": "JPL",
                "Sala": "Sala",
            },
            color_discrete_map={
                "Sala": "#E53935",
                "JPL": "#00ACC1",
                "JESP": "#F9A825",
            },
            barmode="stack",
        )
        fig.update_layout(
            template="custom_theme",
            height=400,
            legend_title="Tipo",
            title_font_size=16,
            yaxis_title="Cantidades",
        )
        st.plotly_chart(fig, width="stretch", theme=None)
    with col_b:
        fig2 = px.bar(
            rp_filt,
            x="Provincia",
            y=["Varones", "Mujeres"],
            title="<b>Jueces y Juezas por Provincia</b>",
            labels={
                "value": "Cantidades",
                "variable": "Sexo",
                "Provincia": "Provincia",
            },
            color_discrete_map={"Varones": "#01497c", "Mujeres": "#ff97b7"},
            barmode="group",
        )
        fig2.update_layout(
            template="custom_theme",
            height=370,
            legend_title="Sexo",
            title_font_size=16,
            yaxis_title="Cantidades",
        )
        st.plotly_chart(fig2, width="stretch", theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        cond_prov = (
            dp.groupby(["Provincia", "CondicionLabel"])
            .size()
            .reset_index(name="Cantidad")
        )
        cond_prov = cond_prov[cond_prov["Provincia"].isin(rp_filt["Provincia"])]
        fig3 = px.bar(
            cond_prov,
            x="Provincia",
            y="Cantidad",
            color="CondicionLabel",
            title="<b>Condición del Magistrado por Provincia</b>",
            labels={"CondicionLabel": "Condición"},
            color_discrete_map={
                "Titular": "#4A7C59",
                "Provisionales": "#D4A574",
                "Supernumerarios": "#8B1A2B",
            },
            barmode="stack",
        )
        fig3.update_layout(
            template="custom_theme",
            height=370,
            title_font_size=16,
            yaxis_title="Magistrados",
        )
        st.plotly_chart(fig3, width="stretch", theme=None)
    with col_d:
        # Radar chart
        cats = ["Sala", "JESP", "JPL", "Varones", "Mujeres"]
        rp_rad = rp_filt.copy()
        fig_rad = go.Figure()
        for i, (_, row) in enumerate(rp_rad.iterrows()):
            fig_rad.add_trace(
                go.Scatterpolar(
                    r=[row[c] for c in cats] + [row[cats[0]]],
                    theta=cats + [cats[0]],
                    name=row["Provincia"],
                    fill="toself",
                    opacity=0.6,
                    line=dict(color=NUEVA_PALETA[i % len(NUEVA_PALETA)]),
                    fillcolor=NUEVA_PALETA[i % len(NUEVA_PALETA)],
                )
            )
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title="<b>Radar: Composición por Provincia</b>",
            height=370,
            title_font_size=16,
            template="custom_theme",
        )
        st.plotly_chart(fig_rad, width="stretch", theme=None)

    # ── Detalle individual ──────────────────────────────────────────────
    st.markdown(
        '<div class="section-title">Detalle Individual de Jueces y Juezas</div>',
        unsafe_allow_html=True,
    )
    default_prov = (
        clicked_prov if clicked_prov else sorted(dp["Provincia"].dropna().unique())[0]
    )
    prov_sel = st.selectbox(
        "Seleccionar provincia (o haz clic en el mapa):",
        sorted(dp["Provincia"].dropna().unique()),
        index=(
            list(sorted(dp["Provincia"].dropna().unique())).index(default_prov)
            if default_prov in list(dp["Provincia"].dropna().unique())
            else 0
        ),
        key="prov_det",
    )
    df_det = dp[dp["Provincia"] == prov_sel].copy()
    df_det["TipoOrgano"] = df_det["TipoOrgano"].replace(
        {"JIP": "J. Esp.", "JUP": "J. Esp.", "JESP": "J. Esp."}
    )

    col_e, col_f = st.columns([1, 2])
    with col_e:
        sexo_cnt = df_det["Sexo"].value_counts().reset_index()
        sexo_cnt.columns = ["Sexo", "Cantidad"]
        fig5 = px.pie(
            sexo_cnt,
            names="Sexo",
            values="Cantidad",
            title=f"<b>Sexo — {prov_sel}</b>",
            color="Sexo",
            color_discrete_map={"Varón": "#01497c", "Mujer": "#ff97b7"},
            hole=0.5,
        )
        fig5.update_layout(height=310, title_font_size=16)
        st.plotly_chart(fig5, width="stretch", theme=None)

        cond_cnt = df_det["CondicionLabel"].value_counts().reset_index()
        cond_cnt.columns = ["Condición", "Cantidad"]
        fig6 = px.pie(
            cond_cnt,
            names="Condición",
            values="Cantidad",
            title="<b>Condición</b>",
            color_discrete_sequence=[VERDE, "#B5622B", ROJO],
            hole=0.5,
        )
        fig6.update_layout(height=310, title_font_size=16)
        st.plotly_chart(fig6, width="stretch", theme=None)
    with col_f:
        tipo_sex = df_det.groupby(["TipoOrgano", "Sexo"]).size().reset_index(name="N")
        fig7 = px.bar(
            tipo_sex,
            x="TipoOrgano",
            y="N",
            color="Sexo",
            barmode="group",
            title="<b>Jueces y Juezas por Tipo de Órgano y Sexo</b>",
            color_discrete_map={"Varón": "#01497c", "Mujer": "#ff97b7"},
        )
        fig7.update_layout(template="custom_theme", height=310, title_font_size=16)
        st.plotly_chart(fig7, width="stretch", theme=None)

        show_cols = [
            "Nombre",
            "Sexo",
            "TipoOrgano",
            "Especialidad",
            "Numero",
            "CondicionLabel",
        ]
        df_show = df_det[show_cols].copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — AUDIENCIAS
# ═══════════════════════════════════════════════════════════════════════════
with T_AUD:
    st.markdown(
        '<div class="section-title">Audiencias — PENAL NCPP</div>',
        unsafe_allow_html=True,
    )

    aud_anual = aud[aud["TipoAnio"] == "Anual"].copy()
    sedes_all = sorted(aud_anual["Sede"].unique())
    sel_sedes = st.multiselect("Sedes:", sedes_all, default=sedes_all, key="sedes_aud")
    df_aud = aud_anual[aud_anual["Sede"].isin(sel_sedes)]

    # Paleta de altísimo contraste
    DISTINCT_COLORS_SEDE = [
        "#1565C0",
        "#D81B60",
        "#2E7D32",
        "#F9A825",
        "#00ACC1",
        "#F4511E",
        "#5D4037",
        "#6A1B9A",
        "#E53935",
        "#6B0F1A",
        "#546E7A",
    ]
    SEDE_COLORS = {
        sede: DISTINCT_COLORS_SEDE[i % len(DISTINCT_COLORS_SEDE)]
        for i, sede in enumerate(sedes_all)
    }

    chip_css_rules_sedes = ""
    for sede_name, sede_color in SEDE_COLORS.items():
        chip_css_rules_sedes += f"""
        [data-baseweb="tag"] span[title="{sede_name}"] ~ div,
        [data-baseweb="tag"]:has(span[title="{sede_name}"]) {{
            background-color: {sede_color} !important;
            color: #ffffff !important;
            border: 1.5px solid {sede_color} !important;
        }}
        """
    st.markdown(f"<style>{chip_css_rules_sedes}</style>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.line(
            df_aud,
            x="Año",
            y="Programadas",
            color="Sede",
            markers=True,
            title="<b>Audiencias Programadas (NCPP)</b>",
            color_discrete_map=SEDE_COLORS,
        )
        fig.update_layout(template="custom_theme", height=350, title_font_size=16)
        st.plotly_chart(fig, width="stretch", theme=None)
    with col_b:
        fig2 = px.line(
            df_aud,
            x="Año",
            y="TasaAtencion",
            color="Sede",
            markers=True,
            title="<b>Tasa de Atención por Sede (NCPP) (%)</b>",
            color_discrete_map=SEDE_COLORS,
        )
        fig2.update_yaxes(tickformat=".0%")
        fig2.add_hline(
            y=0.95,
            line_dash="dash",
            line_color="#4A7C59",
            annotation_text="Meta 95%",
            annotation_font_color="#4A7C59",
        )
        fig2.update_layout(template="custom_theme", height=350, title_font_size=16)
        st.plotly_chart(fig2, width="stretch", theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        tot = (
            df_aud.groupby("Sede")[["Programadas", "Atendidas", "Suspendidas"]]
            .sum()
            .reset_index()
        )
        fig3 = px.bar(
            tot.melt(id_vars="Sede"),
            x="Sede",
            y="value",
            color="variable",
            barmode="group",
            title="<b>Total Acumulado Programadas/Atendidas/Suspendidas (NCPP)</b>",
            color_discrete_sequence=["#1565C0", "#2E7D32", "#E53935"],
            labels={"variable": "", "value": "Audiencias"},
        )
        fig3.update_layout(template="custom_theme", height=360, title_font_size=16)
        st.plotly_chart(fig3, width="stretch", theme=None)
    with col_d:
        df_2025 = (
            aud_anual[aud_anual["Año"] == "2025"].dropna(subset=["TasaAtencion"]).copy()
        )
        df_2025 = df_2025.sort_values("TasaAtencion", ascending=True)
        df_2025["Pct"] = (df_2025["TasaAtencion"] * 100).round(1)
        df_2025["Color"] = df_2025["Pct"].apply(
            lambda v: "#4A7C59" if v >= 95 else ("#C4952A" if v >= 80 else "#8B1A2B")
        )
        df_2025["Estado"] = df_2025["Pct"].apply(
            lambda v: (
                "✅ Meta cumplida"
                if v >= 95
                else ("⚠️ En proceso" if v >= 80 else "❌ Bajo meta")
            )
        )
        fig4 = go.Figure()
        fig4.add_trace(
            go.Bar(
                y=df_2025["Sede"],
                x=df_2025["Pct"],
                orientation="h",
                marker_color=df_2025["Color"],
                text=df_2025["Pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
                textfont=dict(size=13, color="#333"),
                customdata=df_2025[["Estado", "Programadas", "Atendidas"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Tasa: %{x:.1f}%<br>"
                    "%{customdata[0]}<br>"
                    "Programadas: %{customdata[1]:,.0f}<br>"
                    "Atendidas: %{customdata[2]:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        fig4.add_vline(
            x=95,
            line_dash="dash",
            line_color="#4A7C59",
            line_width=2,
            annotation_text="Meta 95%",
            annotation_position="top right",
            annotation_font_color="#4A7C59",
            annotation_font_size=11,
        )
        fig4.update_layout(
            title="<b>Tasa de Atención 2025 por Provincia (NCPP)</b>",
            template="custom_theme",
            height=360,
            title_font_size=16,
            xaxis=dict(title="%", range=[0, 108], showgrid=True, gridcolor="#eee"),
            yaxis=dict(title=""),
            margin=dict(l=10, r=60, t=45, b=10),
        )
        st.plotly_chart(fig4, width="stretch", theme=None)

    with st.expander("🗂️ Ver tabla de audiencias"):
        df_show = df_aud.copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, width="stretch")

    st.markdown(
        '<div class="section-title">Audiencias — PENAL SNEJ</div>',
        unsafe_allow_html=True,
    )

    if snej.empty:
        st.info("No se encontró información de PENAL SNEJ en la hoja 'Resumen'.")
    else:
        juzgados_all = sorted(snej["Juzgado"].unique())
        sel_juzgados = st.multiselect(
            "Juzgados SNEJ:", juzgados_all, default=juzgados_all, key="juzgados_snej"
        )
        df_snej = snej[snej["Juzgado"].isin(sel_juzgados)].copy()

        DISTINCT_COLORS_JUZ = [
            "#1565C0",
            "#D81B60",
            "#2E7D32",
            "#F9A825",
            "#00ACC1",
            "#F4511E",
            "#5D4037",
            "#6A1B9A",
            "#E53935",
            "#6B0F1A",
            "#546E7A",
        ]
        JUZ_COLORS = {
            j: DISTINCT_COLORS_JUZ[i % len(DISTINCT_COLORS_JUZ)]
            for i, j in enumerate(juzgados_all)
        }

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fig_s1 = px.line(
                df_snej,
                x="Año",
                y="Programadas",
                color="Juzgado",
                markers=True,
                title="<b>Audiencias Programadas (SNEJ)</b>",
                color_discrete_map=JUZ_COLORS,
            )
            fig_s1.update_layout(
                template="custom_theme",
                height=350,
                title_font_size=16,
                yaxis_title="Programadas",
            )
            st.plotly_chart(fig_s1, width="stretch", theme=None)
        with col_s2:
            fig_s2 = px.line(
                df_snej,
                x="Año",
                y="PctAtencion",
                color="Juzgado",
                markers=True,
                title="<b>Tasa de Atención por Juzgado (SNEJ)</b>",
                color_discrete_map=JUZ_COLORS,
            )
            fig_s2.update_yaxes(tickformat=".0%")
            fig_s2.add_hline(
                y=0.95,
                line_dash="dash",
                line_color="#4A7C59",
                annotation_text="Meta 95%",
                annotation_font_color="#4A7C59",
            )
            fig_s2.update_layout(
                template="custom_theme",
                height=350,
                title_font_size=16,
                yaxis_title="% Atención",
            )
            st.plotly_chart(fig_s2, width="stretch", theme=None)

        col_s3, col_s4 = st.columns(2)
        with col_s3:
            tot_snej = (
                df_snej.groupby("Juzgado")[["Programadas", "Realizadas", "Suspendidas"]]
                .sum()
                .reset_index()
            )
            fig_s3 = px.bar(
                tot_snej.melt(id_vars="Juzgado"),
                x="Juzgado",
                y="value",
                color="variable",
                barmode="group",
                title="<b>Total Acumulado Programadas/Realizadas/Suspendidas (SNEJ)</b>",
                color_discrete_sequence=["#1565C0", "#2E7D32", "#E53935"],
                labels={"variable": "", "value": "Audiencias"},
            )
            fig_s3.update_layout(
                template="custom_theme", height=380, title_font_size=16, xaxis_title=""
            )
            st.plotly_chart(fig_s3, width="stretch", theme=None)
        with col_s4:
            anio_ref = int(df_snej["Año"].max())
            df_ref = (
                df_snej[df_snej["Año"] == anio_ref]
                .copy()
                .sort_values("PctAtencion", ascending=True)
            )
            df_ref["Pct"] = (df_ref["PctAtencion"] * 100).round(1)
            fig_s4 = go.Figure(
                go.Bar(
                    y=df_ref["Juzgado"],
                    x=df_ref["Pct"],
                    orientation="h",
                    marker_color=df_ref["Pct"].apply(
                        lambda v: (
                            "#4A7C59"
                            if v >= 95
                            else ("#C4952A" if v >= 80 else "#8B1A2B")
                        )
                    ),
                    text=df_ref["Pct"].apply(lambda v: f"{v:.1f}%"),
                    textposition="outside",
                    customdata=df_ref[
                        ["Programadas", "Realizadas", "Suspendidas"]
                    ].values,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        "Tasa de atención: %{x:.1f}%<br>"
                        "Programadas: %{customdata[0]:,.0f}<br>"
                        "Realizadas: %{customdata[1]:,.0f}<br>"
                        "Suspendidas: %{customdata[2]:,.0f}<extra></extra>"
                    ),
                )
            )
            fig_s4.add_vline(
                x=95,
                line_dash="dash",
                line_color="#4A7C59",
                line_width=2,
                annotation_text="Meta 95%",
                annotation_position="top right",
                annotation_font_color="#4A7C59",
                annotation_font_size=11,
            )
            fig_s4.update_layout(
                title=f"<b>Tasa de Atención {anio_ref} por Juzgado (SNEJ)</b>",
                template="custom_theme",
                height=380,
                title_font_size=16,
                xaxis=dict(title="%", range=[0, 108], showgrid=True, gridcolor="#eee"),
                yaxis=dict(title=""),
                margin=dict(l=10, r=60, t=45, b=10),
            )
            st.plotly_chart(fig_s4, width="stretch", theme=None)

        with st.expander("🗂️ Ver tabla de audiencias SNEJ"):
            df_snej_show = df_snej.copy()
            df_snej_show["% Atención"] = (df_snej_show["PctAtencion"] * 100).round(2)
            df_snej_show["% Suspensión"] = (df_snej_show["PctSuspension"] * 100).round(
                2
            )
            df_snej_show = df_snej_show.rename(columns={"Realizadas": "Atendidas"})
            df_snej_show = df_snej_show[
                [
                    "Año",
                    "Juzgado",
                    "Programadas",
                    "Atendidas",
                    "Suspendidas",
                    "% Atención",
                    "% Suspensión",
                ]
            ]
            df_snej_show.index = range(1, len(df_snej_show) + 1)
            st.dataframe(df_snej_show, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — PERSONAL JURISDICCIONAL
# ═══════════════════════════════════════════════════════════════════════════
with T_PER:
    # ── Personal Jurisdiccional ──────────────────────────────────────────────
    st.markdown(
        '<div class="section-title personal-title">Personal Jurisdiccional OOJJ por Régimen Laboral</div>',
        unsafe_allow_html=True,
    )

    # Personal por régimen leído desde la hoja Personal_Regimen del Excel
    df_pers = df_regimen.rename(columns={"Regimen": "Régimen"})
    _reg_vals = dict(zip(df_pers["Régimen"], df_pers["Cantidad"]))
    _total_pers = int(df_pers["Cantidad"].sum())

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        fig_pers = px.pie(
            df_pers,
            names="Régimen",
            values="Cantidad",
            hole=0.5,
            title="<b>Distribución por Régimen Laboral</b>",
            color="Régimen",
            color_discrete_sequence=[
                "#1565C0",
                "#F9A825",
                "#2E7D32",
                "#E53935",
                "#6A1B9A",
            ],
        )
        fig_pers.update_traces(
            textinfo="value+percent",
            textfont_size=16,
            marker=dict(line=dict(color="#FFFFFF", width=2)),
        )
        fig_pers.update_layout(height=420, title_font_size=16, margin=dict(t=40, b=10))
        st.markdown('<div class="pers-pie-anchor"></div>', unsafe_allow_html=True)
        st.plotly_chart(fig_pers, width="stretch", theme=None)

    with col_p2:
        st.markdown(
            f"""
        <div class="personal-wrap">
            <div class="personal-total">
                <div class="total-label">TOTAL PERSONAL JURISDICCIONAL</div>
                <div class="total-value">{_total_pers:,}</div>
            </div>
            <div class="personal-cards">
                <div class="personal-card" style="border-bottom:6px solid #F9A825;">
                    <div class="card-label">728</div>
                    <div class="card-value" style="color:#F9A825;">{_reg_vals.get('728', 0)}</div>
                </div>
                <div class="personal-card" style="border-bottom:6px solid #E53935;">
                    <div class="card-label">CAS</div>
                    <div class="card-value" style="color:#E53935;">{_reg_vals.get('CAS', 0)}</div>
                </div>
                <div class="personal-card" style="border-bottom:6px solid #6A1B9A;">
                    <div class="card-label">RECAS</div>
                    <div class="card-value" style="color:#6A1B9A;">{_reg_vals.get('RECAS', 0)}</div>
                </div>
                <div class="personal-card" style="border-bottom:6px solid #1565C0;">
                    <div class="card-label">LEY 29277</div>
                    <div class="card-value" style="color:#1565C0;">{_reg_vals.get('LEY 29277', 0)}</div>
                </div>
                <div class="personal-card" style="border-bottom:6px solid #2E7D32;">
                    <div class="card-label">276</div>
                    <div class="card-value" style="color:#2E7D32;">{_reg_vals.get('276', 0)}</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🗂️ Ver desglose detallado por Cargo"):
        st.dataframe(df_cargos_xls, width="stretch")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div style="text-align:center;padding:22px 0 8px;color:#aaa;font-size:.74rem;">
  ⚖️ Corte Superior de Justicia de Junín | Fuente: Portal de Informes &nbsp;
</div>""",
    unsafe_allow_html=True,
)
