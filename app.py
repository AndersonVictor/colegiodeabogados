import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import json, os

import plotly.io as pio

# ── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard CSJJ Junín",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Set base plotly font size globally
pio.templates["custom_theme"] = pio.templates["plotly_white"]
pio.templates["custom_theme"].layout.paper_bgcolor = "#F2E8D9"  # Color crema para el fondo del gráfico
pio.templates["custom_theme"].layout.plot_bgcolor = "#F2E8D9"   # Color crema para el área del gráfico
pio.templates["custom_theme"].layout.font.size = 14
pio.templates["custom_theme"].layout.title.font.size = 16
pio.templates["custom_theme"].layout.legend.font.size = 18
pio.templates["custom_theme"].layout.legend.title.font.size = 18
pio.templates["custom_theme"].layout.xaxis.title.font.size = 20
pio.templates["custom_theme"].layout.xaxis.tickfont.size = 14
pio.templates["custom_theme"].layout.yaxis.title.font.size = 20
pio.templates["custom_theme"].layout.yaxis.tickfont.size = 14
pio.templates.default = "custom_theme"

ROJO   = "#6B0F1A"
ROJO2  = "#8B1A2B"
DORADO = "#C4952A"
AZUL   = "#2E6DA4"
VERDE  = "#4A7C59"
GRIS   = "#F2E8D9"

# Paleta de colores solicitada para gráficos generales
NUEVA_PALETA = [
    "#6B0F1A", # Guindo
    "#E53935", # Rojo
    "#F4511E", # Naranja
    "#F9A825", # Amarillo
    "#2E7D32", # Verde
    "#00ACC1", # Celeste
    "#1565C0", # Azul
    "#6A1B9A", # Morado
    "#D81B60", # Rosa
    "#5D4037", # Marrón
    "#546E7A", # Gris
]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: #F2E8D9 !important; }}

.block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}

.header-bar {{
    background: linear-gradient(135deg, {ROJO} 0%, {ROJO2} 60%, #3D0A14 100%);
    border-radius: 14px;
    padding: 22px 32px;
    margin-bottom: 22px;
    display: flex; align-items: center; gap: 18px;
    box-shadow: 0 6px 30px rgba(123,26,26,0.35);
}}
.header-bar h1 {{ 
    font-family: 'Montserrat', sans-serif; 
    color: #ffffff; 
    font-size: 2.4rem; 
    font-weight: 800; 
    margin: 0; 
    letter-spacing: .5px; 
}}
.header-bar h3 {{ 
    font-family: 'Montserrat', sans-serif; 
    color: rgba(255,255,255,0.95); 
    font-size: 1.3rem; 
    font-weight: 500; 
    margin: 6px 0 0; 
    letter-spacing: .3px; 
}}
.header-bar p  {{ color: rgba(255,255,255,.9); font-size: 1.15rem; margin: 6px 0 0; }}
.escudo {{ font-size: 3rem; line-height: 1; }}

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

.stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: #fff; border-radius: 14px; padding: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; padding: 10px 26px; font-weight: 700; font-size: 1rem;
    color: #555; border: none; background: transparent;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {ROJO}, {ROJO2}) !important;
    color: #fff !important; box-shadow: 0 3px 14px rgba(123,26,26,.35);
}}
</style>
""", unsafe_allow_html=True)

# ── Data loader ──────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

@st.cache_data
def load_data():
    xls = pd.ExcelFile(os.path.join(BASE, "DASHBOARD INGE.xlsx"))
    cp  = xls.parse("Carga Procesal")
    cp.columns = ["Año","Especialidad","Ingresos","CargaProcesal","Resueltos"]
    cp["Especialidad"] = cp["Especialidad"].str.title()
    cp["Especialidad"] = cp["Especialidad"].apply(lambda x: "Extinción Dominio" if "Extinci" in str(x) else x)

    pob = xls.parse("Poblacion_Data", skiprows=1)
    pob.columns = ["Provincia","Año","TipoAnio","Varones","Mujeres","Total","PctV","PctM","TasaCrec"]
    pob["Provincia"] = pob["Provincia"].apply(lambda x: "Concepción" if "Concepci" in str(x) else ("Junín (prov.)" if "prov" in str(x) else x))

    dp  = xls.parse("Data_Plana", skiprows=1)
    dp.columns = ["Provincia","Sede","TipoOrgano","Especialidad","Numero","Nombre","Sexo","Condicion","CondicionLabel"]

    rp  = xls.parse("Resumen_Provincia", skiprows=1)
    rp.columns = ["Provincia","Total","JPL","JIP","JUP","Sala","Varones","Mujeres","Titulares","SupernProv"]

    aud = xls.parse("Audiencias_Data")
    aud.columns = ["Sede","Año","TipoAnio","Programadas","Atendidas","Suspendidas","TasaAtencion"]
    return cp, pob, dp, rp, aud

cp, pob, dp, rp, aud = load_data()

import base64

# ── HEADER ───────────────────────────────────────────────────────────────────
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_path = os.path.join(BASE, "image.png")
if os.path.exists(logo_path):
    logo_b64 = get_base64_of_bin_file(logo_path)
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="logo" style="height: 80px;">'
else:
    logo_html = '<div class="escudo">⚖️</div>'

st.markdown(f"""
<div class="header-bar">
  {logo_html}
  <div>
    <h1>Corte Superior de Justicia de Junín</h1>
    <h3>Dashboard de Gestión Jurisdiccional</h3>
    <p style="font-size: 1.2rem; margin-top: 10px; font-weight: 600; color: #F9E79F; letter-spacing: 0.5px;">
      Presidente: Dr. Ricardo Corrales Melgarejo
      | Gestión: 2025-2026 | Justica pronta, honesta e inclusiva.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs globales ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'''
    <div class="kpi-card">
      <div class="kpi-val">121</div>
      <div class="kpi-lbl">Magistrados</div>
      <div class="kpi-delta" style="font-size:1.05rem; color:#555;">101 Órganos Jurisdiccionales</div>
    </div>''', unsafe_allow_html=True)

with c2:
    juez_path = os.path.join(BASE, "juez.png")
    jueza_path = os.path.join(BASE, "jueza.png")
    juez_b64 = get_base64_of_bin_file(juez_path) if os.path.exists(juez_path) else ""
    jueza_b64 = get_base64_of_bin_file(jueza_path) if os.path.exists(jueza_path) else ""
    
    juez_icon = f'<img src="data:image/png;base64,{juez_b64}" style="height:22px; vertical-align:middle; margin-right:5px; margin-bottom:3px;">' if juez_b64 else '♂ '
    jueza_icon = f'<img src="data:image/png;base64,{jueza_b64}" style="height:22px; vertical-align:middle; margin-right:5px; margin-bottom:3px;">' if jueza_b64 else '♀ '

    st.markdown(f'''
    <div class="kpi-card" style="display:flex; flex-direction:row; justify-content:space-around; align-items:center;">
      <div style="text-align:center;">
        <div style="font-size:3.2rem; font-weight:800; color:#01497c; line-height:1;">80</div>
        <div style="font-size:1.2rem; font-weight:600; color:#555; margin-top:2px;">{juez_icon}Varones</div>
      </div>
      <div style="width:2px; height:50px; background:#eee;"></div>
      <div style="text-align:center;">
        <div style="font-size:3.2rem; font-weight:800; color:#ff97b7; line-height:1;">41</div>
        <div style="font-size:1.2rem; font-weight:600; color:#555; margin-top:2px;">{jueza_icon}Mujeres</div>
      </div>
    </div>''', unsafe_allow_html=True)

with c3:
    st.markdown(f'''
    <div class="kpi-card" style="display:flex; flex-direction:row; justify-content:space-around; align-items:center;">
      <div style="text-align:center;">
        <div style="font-size:2.8rem; font-weight:800; color:{VERDE}; line-height:1;">47</div>
        <div style="font-size:1.1rem; font-weight:600; color:#555; margin-top:2px;">Titulares</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:2.8rem; font-weight:800; color:{ROJO}; line-height:1;">51</div>
        <div style="font-size:1.1rem; font-weight:600; color:#555; margin-top:2px;">Supernum.</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:2.8rem; font-weight:800; color:#e67e22; line-height:1;">23</div>
        <div style="font-size:1.1rem; font-weight:600; color:#555; margin-top:2px;">Provisional</div>
      </div>
    </div>''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────
T_POB, T_RES, T_CAR, T_AUD, T_PER = st.tabs([
    "📈  Proyecciones Poblacionales",
    "🏛️  Resumen & Detalle Provincia",
    "📂  Carga Procesal",
    "🎙️  Audiencias",
    "👥  Personal Jurisdiccional",
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — CARGA PROCESAL
# ═══════════════════════════════════════════════════════════════════════════
with T_CAR:
    st.markdown('<div class="section-title">Evolución de la Carga Procesal por Especialidad</div>', unsafe_allow_html=True)

    ESP_COLORS = {
        "Civil":             "#00ACC1",
        "Constitucional":    "#1565C0",
        "Extinción Dominio": "#6A1B9A",
        "Familia":           "#D81B60",
        "Laboral":           "#F9A825",
        "Penal":             "#6B0F1A",
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
    
    sel_esp = st.multiselect("Filtrar especialidades:", esp_all, default=esp_all, key="esp")
    anio_range = st.slider("Rango de años:", int(cp["Año"].min()), int(cp["Año"].max()),
                           (int(cp["Año"].min()), int(cp["Año"].max())), key="anio_cp")
    df_cp = cp[cp["Especialidad"].isin(sel_esp) & cp["Año"].between(*anio_range)]

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.line(df_cp, x="Año", y="Ingresos", color="Especialidad",
                      markers=True, title="<b>Ingresos por Año</b>",
                      color_discrete_map=ESP_COLORS)
        fig.update_layout(template="custom_theme", legend_title="", height=450, title_font_size=16, legend=dict(font=dict(size=18), title=dict(font=dict(size=18))), xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)), yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)))
        st.plotly_chart(fig, width='stretch', theme=None)
    with col_b:
        fig2 = px.bar(df_cp, x="Año", y="Resueltos", color="Especialidad",
                      barmode="group", title="<b>Expedientes Resueltos</b>",
                      color_discrete_map=ESP_COLORS)
        fig2.update_layout(template="custom_theme", legend_title="", height=450, title_font_size=16, legend=dict(font=dict(size=18), title=dict(font=dict(size=18))), xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)), yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)))
        st.plotly_chart(fig2, width='stretch', theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        fig3 = px.bar(df_cp, x="Año", y="CargaProcesal", color="Especialidad",
                      barmode="stack", title="<b>Carga Procesal Acumulada</b>",
                      color_discrete_map=ESP_COLORS)
        fig3.update_layout(template="custom_theme", legend_title="", height=450, title_font_size=16, legend=dict(font=dict(size=18), title=dict(font=dict(size=18))), xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)), yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)))
        st.plotly_chart(fig3, width='stretch', theme=None)
    with col_d:
        df_ratio = df_cp.copy()
        df_ratio["Tasa_Resolucion"] = (df_ratio["Resueltos"] / df_ratio["Ingresos"].replace(0,1) * 100).round(2)
        fig4 = px.line(df_ratio, x="Año", y="Tasa_Resolucion", color="Especialidad",
                       markers=True, title="<b>Tasa de Resolución (%)</b>",
                       color_discrete_map=ESP_COLORS)
        fig4.add_hline(y=100, line_dash="dash", line_color="#4A7C59", annotation_text="100%")
        fig4.update_layout(template="custom_theme", legend_title="", height=450, title_font_size=16, legend=dict(font=dict(size=18), title=dict(font=dict(size=18))), xaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)), yaxis=dict(title=dict(font=dict(size=20)), tickfont=dict(size=14)))
        st.plotly_chart(fig4, width='stretch', theme=None)

    with st.expander("🗂️ Ver tabla de datos"):
        st.dataframe(df_cp.reset_index(drop=True), width='stretch')

    st.markdown('<div class="section-title" style="color: #8B1A2B; border-left-color: #8B1A2B;">⚠️ Alerta: Situación de Carga Procesal Proyectada a Diciembre 2026</div>', unsafe_allow_html=True)
    
    alert_data = [
        "SALA CIVIL DE HUANCAYO",
        "2° JUZGADO DE FAMILIA DE HUANCAYO",
        "1° JUZGADO PENAL UNIPERSONAL DE HUANCAYO (PROC. INMEDIATOS)",
        "2° JUZGADO PENAL UNIPERSONAL DE HUANCAYO (PROC. COMUNES)",
        "3° JUZGADO PENAL UNIPERSONAL DE HUANCAYO (PROC. INMEDIATOS)",
        "4° JUZGADO PENAL UNIPERSONAL DE HUANCAYO (PROC. COMUNES)",
        "5° JUZGADO PENAL UNIPERSONAL SUPRAPROVINCIAL ESPECIALIZADO EN DELITOS DE CORRUPCIÓN DE FUNCIONARIOS HUANCAYO",
        "6° JUZGADO PENAL UNIPERSONAL SUPRAPROVINCIAL ESPECIALIZADO EN DELITOS DE CORRUPCIÓN DE FUNCIONARIOS HUANCAYO",
        "1° JUZGADO DE INVESTIGACIÓN PREPARATORIA DE HUANCAYO (PROC. COMUNES)",
        "2° JUZGADO DE INVESTIGACIÓN PREPARATORIA DE HUANCAYO (PROC. COMUNES)",
        "5° JUZGADO DE INVESTIGACIÓN PREPARATORIA SUPRAPROVINCIAL ESPECIALIZADO EN DELITO DE CORRUPCIÓN DE FUNCIONARIOS DE HUANCAYO",
        "6° JUZGADO DE INVESTIGACIÓN PREPARATORIA DE HUANCAYO (PROC. COMUNES)",
        "8° JUZGADO DE INVESTIGACIÓN PREPARATORIA SUPRAPROVINCIAL ESPECIALIZADO EN DELITO DE CORRUPCIÓN DE FUNCIONARIOS DE HUANCAYO",
        "JUZGADO DE INVESTIGACIÓN PREPARATORIA DE CHUPACA (PROC. INMEDIATOS) (PROC. COMUNES)"
    ]
    df_alert = pd.DataFrame({
        "ÓRGANOS JURISDICCIONALES": alert_data,
        "ESTADO": ["SOBRECARGA"] * len(alert_data),
        "VALOR": [1] * len(alert_data)
    })

    col_alert1, col_alert2 = st.columns([2, 1])
    with col_alert1:
        fig_alert = px.bar(
            df_alert, 
            y="ÓRGANOS JURISDICCIONALES", 
            x="VALOR",
            orientation="h",
            text="ESTADO",
            title="<b>Órganos Jurisdiccionales en Sobrecarga</b>",
            color_discrete_sequence=["#8B1A2B"]
        )
        fig_alert.update_traces(textposition="inside", textfont_size=14, textfont_color="white", hovertemplate="%{y}<extra></extra>")
        fig_alert.update_layout(
            template="custom_theme", 
            height=550, 
            title_font_size=16, 
            xaxis=dict(visible=False),
            yaxis=dict(title="", tickfont=dict(size=10)),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        fig_alert.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_alert, width='stretch', theme=None)
        
    with col_alert2:
        st.markdown(f'''
        <div style="background-color: #F5E6E4; border: 2px solid #8B1A2B; border-radius: 10px; padding: 20px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(139,26,43,0.2);">
            <div style="font-size: 4.5rem; margin-bottom: 10px; line-height: 1;">🚨</div>
            <h3 style="color: #8B1A2B; margin-top: 0; font-size: 1.6rem; font-weight: 800;">ALERTA CRÍTICA</h3>
            <p style="font-size: 1.15rem; color: #444; margin-bottom: 15px;">
                Se proyecta que <b>{len(alert_data)}</b> órganos jurisdiccionales alcanzarán un estado crítico de <b>sobrecarga procesal</b> para <b>Diciembre de 2026</b>.
            </p>
            <p style="font-size: 1rem; color: #666; font-weight: 600;">
                Requiere intervención inmediata y redistribución de carga.
            </p>
        </div>
        ''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — PROYECCIONES POBLACIONALES
# ═══════════════════════════════════════════════════════════════════════════
with T_POB:
    st.markdown('<div class="section-title">Proyecciones Poblacionales — Región Junín (INEI 2007–2031)</div>',
                unsafe_allow_html=True)

    pob_provs = pob[pob["Provincia"] != "Junín (región)"].copy()
    provs = sorted(pob_provs["Provincia"].unique())
    
    # Colores de altísimo contraste para evitar confusiones visuales
    DISTINCT_COLORS = [
        "#1565C0", # Azul
        "#D81B60", # Rosa
        "#2E7D32", # Verde
        "#F9A825", # Amarillo
        "#00ACC1", # Celeste
        "#F4511E", # Naranja
        "#5D4037", # Marrón
        "#6A1B9A", # Morado
        "#E53935", # Rojo
        "#6B0F1A", # Guindo
        "#546E7A", # Gris
    ]
    PROV_COLORS = {prov: DISTINCT_COLORS[i % len(DISTINCT_COLORS)] for i, prov in enumerate(provs)}
    
    chip_css_rules_prov = ""
    for prov_name, prov_color in PROV_COLORS.items():
        chip_css_rules_prov += f"""
        [data-baseweb="tag"] span[title="{prov_name}"] ~ div,
        [data-baseweb="tag"]:has(span[title="{prov_name}"]) {{
            background-color: {prov_color} !important;
            color: #ffffff !important;
            border: 1.5px solid {prov_color} !important;
        }}
        """
    st.markdown(f"<style>{chip_css_rules_prov}</style>", unsafe_allow_html=True)

    sel_prov_pob = st.multiselect("Seleccionar provincias:", provs,
                                  default=provs,
                                  key="prov_pob")
    df_pb = pob_provs[pob_provs["Provincia"].isin(sel_prov_pob)]

    fig = px.line(df_pb, x="Año", y="Total", color="Provincia",
                  markers=True, title="<b>Población Total Proyectada</b>",
                  color_discrete_map=PROV_COLORS)
    fig.update_layout(template="custom_theme", height=360, title_font_size=16)
    st.plotly_chart(fig, width='stretch', theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        df_melt = df_pb.melt(id_vars=["Provincia","Año"], value_vars=["Varones","Mujeres"],
                              var_name="Sexo", value_name="Poblacion")
        
        n_provs = len(df_pb["Provincia"].unique())
        n_rows = (n_provs + 1) // 2
        fig3_height = max(400, n_rows * 200)

        fig3 = px.line(df_melt, x="Año", y="Poblacion", color="Sexo",
                       facet_col="Provincia", facet_col_wrap=2,
                       title="<b>Varones vs Mujeres por Provincia</b>",
                       color_discrete_map={"Varones": "#01497c", "Mujeres": "#ff97b7"})
        fig3.update_traces(mode="lines+markers")
        fig3.update_yaxes(matches=None, showticklabels=True)
        fig3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig3.update_layout(template="custom_theme", height=fig3_height, title_font_size=16, margin=dict(t=50, b=20, l=10, r=10))
        st.plotly_chart(fig3, width='stretch', theme=None)
    with col_d:
        df_2031 = pob_provs[pob_provs["Año"] == 2031].sort_values("Total", ascending=True)
        
        fig4 = go.Figure(go.Bar(
            y=df_2031["Provincia"], x=df_2031["Total"],
            orientation="h",
            marker=dict(color=[PROV_COLORS.get(p, "#1565C0") for p in df_2031["Provincia"]]),
            text=df_2031["Total"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside"
        ))
        fig4.update_layout(template="custom_theme", title="<b>Población Proyectada 2031 por Provincia</b>",
                           height=380, title_font_size=16, xaxis_title="Habitantes")
        st.plotly_chart(fig4, width='stretch', theme=None)

    with st.expander("🗂️ Ver tabla de datos"):
        df_show = df_pb.copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, width='stretch')

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — RESUMEN & DETALLE PROVINCIA
# ═══════════════════════════════════════════════════════════════════════════
with T_RES:
    st.markdown('<div class="section-title">Mapa Interactivo — Distrito Judicial de Junín</div>',
                unsafe_allow_html=True)

    rp_filt = rp[rp["Provincia"] != "TOTAL CSJJ"].copy()
    
    # Resumen de jueces (magistrados)
    st.markdown(f'''
        <div style="background: #eef2f6; padding: 12px 20px; border-radius: 8px; margin-bottom: 16px; border-left: 5px solid {AZUL};">
            <strong style="color: {AZUL}; font-size: 1.15rem;">Resumen General CSJJ:</strong>
            <span style="font-size: 1.1rem; margin-left: 10px;">
                <b>80</b> Jueces (Varones) | <b>41</b> Juezas (Mujeres) | <b>121</b> Total
            </span>
        </div>
    ''', unsafe_allow_html=True)

    GEOJSON_PATH = os.path.join(BASE, "peru_provincial_simple.geojson")
    PROVINCIAS_DJ = {"HUANCAYO","TARMA","JAUJA","CHUPACA","CONCEPCION","YAULI","JUNIN","TAYACAJA"}
    PROV_MAP = {"HUANCAYO":"Huancayo","TARMA":"Tarma","JAUJA":"Jauja","CHUPACA":"Chupaca",
                "CONCEPCION":"Concepción","YAULI":"Yauli","JUNIN":"Junín","TAYACAJA":"Tayacaja"}

    # Selector de variable para colorear el mapa
    VAR_OPTIONS = {
        "Total Magistrados": "Total",
        "Jueces (Varones)": "Varones",
        "Juezas (Mujeres)": "Mujeres",
        "Juzgados de Paz Letrado (JPL)": "JPL",
        "Juzgados de Invest. Preparatoria (JIP)": "JIP",
        "Juzgados Unipersonales (JUP)": "JUP",
        "Salas": "Sala",
        "Titulares": "Titulares",
        "Supernumerarios/Provisionales": "SupernProv",
    }
    sel_var_label = st.selectbox(
        "🎨 Variable a visualizar en el mapa:",
        list(VAR_OPTIONS.keys()), index=0, key="map_var"
    )
    sel_var = VAR_OPTIONS[sel_var_label]

    col_map, col_charts = st.columns([3, 2])
    with col_map:
        with open(GEOJSON_PATH, encoding="utf-8") as f:
            geo_all = json.load(f)
        geo_dj = {"type":"FeatureCollection",
                  "features":[ft for ft in geo_all["features"]
                               if ft["properties"].get("NOMBPROV","") in PROVINCIAS_DJ]}

        # Enrich features with ALL variables
        rp_lookup_all = {row["Provincia"]: row for _, row in rp_filt.iterrows()}
        for ft in geo_dj["features"]:
            key = ft["properties"]["NOMBPROV"]
            prov_label = PROV_MAP.get(key, key.title())
            row_data = rp_lookup_all.get(prov_label, {})
            ft["properties"]["PROV_LABEL"]    = prov_label
            ft["properties"]["MAGISTRADOS"]   = int(row_data.get("Total", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["VARONES"]       = int(row_data.get("Varones", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["MUJERES"]       = int(row_data.get("Mujeres", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["JPL"]           = int(row_data.get("JPL", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["JIP"]           = int(row_data.get("JIP", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["JUP"]           = int(row_data.get("JUP", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["SALA"]          = int(row_data.get("Sala", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["TITULARES"]     = int(row_data.get("Titulares", 0)) if hasattr(row_data, "get") else 0
            ft["properties"]["SUPERN"]        = int(row_data.get("SupernProv", 0)) if hasattr(row_data, "get") else 0

        # Map variable → GeoJSON field name
        GEO_FIELD = {"Total":"MAGISTRADOS","Varones":"VARONES","Mujeres":"MUJERES",
                     "JPL":"JPL","JIP":"JIP","JUP":"JUP","Sala":"SALA",
                     "Titulares":"TITULARES","SupernProv":"SUPERN"}
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
                        all_lats.append(lat); all_lons.append(lon)
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        for lon, lat in ring:
                            all_lats.append(lat); all_lons.append(lon)

        sw = [min(all_lats), min(all_lons)] if all_lats else [-12.5, -75.5]
        ne = [max(all_lats), max(all_lons)] if all_lats else [-11.0, -74.5]
        center_lat = (sw[0] + ne[0]) / 2
        center_lon = (sw[1] + ne[1]) / 2

        # ── Mapa Plotly 100% offline (go.Choroplethmapbox + white-bg) ────────
        map_df = rp_filt[["Provincia", sel_var]].copy()

        CS_GUINDO = [[0, "#F5E6E4"], [0.5, "#C4748A"], [1, "#8B1A2B"]]
        CS_AZUL   = [[0, "#B8D4EE"], [0.5, "#5B9BD5"], [1, "#2E6DA4"]]
        CS_VERDE  = [[0, "#C8E6C9"], [0.5, "#7DB88A"], [1, "#4A7C59"]]
        CS_TIERRA = [[0, "#F2E8D9"], [0.5, "#D4A574"], [1, "#B5622B"]]
        CS_VIOLETA= [[0, "#EDE3F5"], [0.5, "#B89CC8"], [1, "#7B4F8E"]]
        CS_DORADO = [[0, "#FAF0C8"], [0.5, "#E8C568"], [1, "#C4952A"]]
        CS_VARONES= [[0, "#e6f0f7"], [0.5, "#4682B4"], [1, "#01497c"]]
        CS_MUJERES= [[0, "#ffeef3"], [0.5, "#ffb8cd"], [1, "#ff97b7"]]

        PLOTLY_CSCALES = {
            "Total": CS_GUINDO, "Varones": CS_VARONES, "Mujeres": CS_MUJERES,
            "JPL": CS_DORADO, "JIP": CS_TIERRA, "JUP": CS_VERDE, "Sala": CS_GUINDO,
            "Titulares": CS_VERDE, "SupernProv": CS_TIERRA
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
                    f"⚖️ Total: {feat_data['MAGISTRADOS']}<br>"
                    f"♂ Jueces: {feat_data['VARONES']}  ♀ Juezas: {feat_data['MUJERES']}<br>"
                    f"JPL: {feat_data['JPL']}  JIP: {feat_data['JIP']}  JUP: {feat_data['JUP']}  Salas: {feat_data['SALA']}<br>"
                    f"Titulares: {feat_data['TITULARES']}  Supern.: {feat_data['SUPERN']}"
                )
            else:
                hover_texts.append(prov)

        fig_map = go.Figure(go.Choropleth(
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
                title=dict(text=sel_var_label, font=dict(size=14)),
                tickfont=dict(size=12),
                len=0.7,
            ),
        ))

        # ── Etiquetas de provincia sobre el mapa ─────────────────────────
        label_lats, label_lons, label_texts = [], [], []
        for ft in geo_dj["features"]:
            prov_label = ft["properties"].get("PROV_LABEL", "")
            ft_lats, ft_lons = [], []
            coords = ft["geometry"]["coordinates"]
            if ft["geometry"]["type"] == "Polygon":
                for ring in coords:
                    for lon, lat in ring:
                        ft_lats.append(lat); ft_lons.append(lon)
            elif ft["geometry"]["type"] == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        for lon, lat in ring:
                            ft_lats.append(lat); ft_lons.append(lon)
            if ft_lats:
                label_lats.append(sum(ft_lats) / len(ft_lats))
                label_lons.append(sum(ft_lons) / len(ft_lons))
                # Enhancing labels to make them more visible and professional
                label_texts.append(prov_label.upper())

        fig_map.add_trace(go.Scattergeo(
            lat=label_lats, lon=label_lons,
            mode="text",
            text=label_texts,
            textfont=dict(size=15, color="#000000", family="Arial Black, Inter, sans-serif"),
            textposition="middle center",
            hoverinfo="none",
            showlegend=False,
        ))

        fig_map.update_layout(
            geo=dict(
                fitbounds="locations",
                visible=False,
                bgcolor="rgba(242,232,217,0)"
            ),
            template="custom_theme", height=650, margin=dict(l=0, r=0, t=40, b=0), 
            title=dict(text=f"<b>Mapa: {sel_var_label} por Provincia</b>", font=dict(size=16)), 
            paper_bgcolor="rgba(242,232,217,0)"
        )
        st.plotly_chart(fig_map, width='stretch', theme=None)

        clicked_prov = None

    # ── Side charts (full height, bigger) ──────────────────────────────
    with col_charts:
        # Horizontal bar — dynamic variable
        fig_bar = px.bar(
            rp_filt.sort_values(sel_var),
            x=sel_var, y="Provincia", orientation="h",
            color=sel_var, color_continuous_scale=PLOTLY_CSCALES.get(sel_var, CS_GUINDO),
            title=f"<b>{sel_var_label} por Provincia</b>",
            text=sel_var,
        )
        fig_bar.update_traces(textposition="outside", textfont_size=13)
        fig_bar.update_layout(
            template="custom_theme", height=650,
            title_font_size=16, coloraxis_showscale=False,
            margin=dict(l=10,r=40,t=40,b=10),
            yaxis_title="", xaxis_title="",
        )
        st.plotly_chart(fig_bar, width='stretch', theme=None)

    # ── Gráficos resumen ────────────────────────────────────────────────
    st.markdown('<div class="section-title">Análisis Comparativo por Provincia</div>',
                unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        rp_plot = rp_filt.copy()
        rp_plot["J. Esp"] = rp_plot["JIP"] + rp_plot["JUP"]
        fig = px.bar(rp_plot, x="Provincia", y=["Sala", "J. Esp", "JPL"],
                     title="<b>Tipos de Órganos Jurisdiccionales</b>",
                     labels={"value": "Cantidades", "variable": "Tipo"},
                     color_discrete_map={"Sala": "#E53935", "J. Esp": "#F9A825", "JPL": "#00ACC1"},
                     barmode="stack")
        fig.update_layout(template="custom_theme", height=400, legend_title="Tipo",
                          title_font_size=16, yaxis_title="Cantidades")
        st.plotly_chart(fig, width='stretch', theme=None)
    with col_b:
        fig2 = px.bar(rp_filt, x="Provincia", y=["Varones","Mujeres"],
                      title="<b>Jueces y Juezas por Provincia</b>",
                      color_discrete_map={"Varones": "#01497c", "Mujeres": "#ff97b7"}, barmode="group")
        fig2.update_layout(template="custom_theme", height=370, legend_title="Sexo", title_font_size=16)
        st.plotly_chart(fig2, width='stretch', theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        cond_prov = dp.groupby(["Provincia", "CondicionLabel"]).size().reset_index(name="Cantidad")
        cond_prov = cond_prov[cond_prov["Provincia"].isin(rp_filt["Provincia"])]
        fig3 = px.bar(cond_prov, x="Provincia", y="Cantidad", color="CondicionLabel",
                      title="<b>Condición del Magistrado por Provincia</b>",
                      labels={"CondicionLabel": "Condición"},
                      color_discrete_map={"Titular": "#4A7C59", "Provisional": "#D4A574", "Supernumerario": "#8B1A2B"},
                      barmode="stack")
        fig3.update_layout(template="custom_theme", height=370, title_font_size=16, yaxis_title="Magistrados")
        st.plotly_chart(fig3, width='stretch', theme=None)
    with col_d:
        # Radar chart
        cats = ["Sala", "J. Esp", "JPL", "Varones", "Mujeres"]
        rp_rad = rp_filt.copy()
        rp_rad["J. Esp"] = rp_rad["JIP"] + rp_rad["JUP"]
        fig_rad = go.Figure()
        for i, (_, row) in enumerate(rp_rad.iterrows()):
            fig_rad.add_trace(go.Scatterpolar(
                r=[row[c] for c in cats] + [row[cats[0]]],
                theta=cats + [cats[0]], name=row["Provincia"],
                fill="toself", opacity=0.6,
                line=dict(color=NUEVA_PALETA[i % len(NUEVA_PALETA)]),
                fillcolor=NUEVA_PALETA[i % len(NUEVA_PALETA)],
            ))
        fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True)),
                              title="<b>Radar: Composición por Provincia</b>",
                              height=370, title_font_size=16, template="custom_theme")
        st.plotly_chart(fig_rad, width='stretch', theme=None)


    # ── Detalle individual ──────────────────────────────────────────────
    st.markdown('<div class="section-title">Detalle Individual de Magistrados</div>',
                unsafe_allow_html=True)
    default_prov = clicked_prov if clicked_prov else sorted(dp["Provincia"].dropna().unique())[0]
    prov_sel = st.selectbox("Seleccionar provincia (o haz clic en el mapa):",
                            sorted(dp["Provincia"].dropna().unique()),
                            index=list(sorted(dp["Provincia"].dropna().unique())).index(default_prov)
                            if default_prov in list(dp["Provincia"].dropna().unique()) else 0,
                            key="prov_det")
    df_det = dp[dp["Provincia"] == prov_sel].copy()

    col_e, col_f = st.columns([1, 2])
    with col_e:
        sexo_cnt = df_det["Sexo"].value_counts().reset_index()
        sexo_cnt.columns = ["Sexo","Cantidad"]
        fig5 = px.pie(sexo_cnt, names="Sexo", values="Cantidad",
                      title=f"<b>Sexo — {prov_sel}</b>", color="Sexo",
                      color_discrete_map={"Varón": "#01497c", "Mujer": "#ff97b7"}, hole=0.5)
        fig5.update_layout(height=310, title_font_size=16)
        st.plotly_chart(fig5, width='stretch', theme=None)

        cond_cnt = df_det["CondicionLabel"].value_counts().reset_index()
        cond_cnt.columns = ["Condición","Cantidad"]
        fig6 = px.pie(cond_cnt, names="Condición", values="Cantidad",
                      title="<b>Condición</b>",
                      color_discrete_sequence=[VERDE,"#B5622B",ROJO], hole=0.5)
        fig6.update_layout(height=310, title_font_size=16)
        st.plotly_chart(fig6, width='stretch', theme=None)
    with col_f:
        tipo_sex = df_det.groupby(["TipoOrgano","Sexo"]).size().reset_index(name="N")
        fig7 = px.bar(tipo_sex, x="TipoOrgano", y="N", color="Sexo",
                      barmode="group", title="<b>Magistrados por Tipo de Órgano y Sexo</b>",
                      color_discrete_map={"Varón": "#01497c", "Mujer": "#ff97b7"})
        fig7.update_layout(template="custom_theme", height=310, title_font_size=16)
        st.plotly_chart(fig7, width='stretch', theme=None)

        show_cols = ["Nombre","Sexo","TipoOrgano","Especialidad","Numero","CondicionLabel"]
        df_show = df_det[show_cols].copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, width='stretch')

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — AUDIENCIAS
# ═══════════════════════════════════════════════════════════════════════════
with T_AUD:
    st.markdown('<div class="section-title">Audiencias por Sede y Año (2017–2026)</div>',
                unsafe_allow_html=True)

    aud_anual = aud[aud["TipoAnio"] == "Anual"].copy()
    sedes_all = sorted(aud_anual["Sede"].unique())
    sel_sedes = st.multiselect("Sedes:", sedes_all, default=sedes_all, key="sedes_aud")
    df_aud = aud_anual[aud_anual["Sede"].isin(sel_sedes)]
    
    # Paleta de altísimo contraste
    DISTINCT_COLORS_SEDE = [
        "#1565C0", "#D81B60", "#2E7D32", "#F9A825", "#00ACC1",
        "#F4511E", "#5D4037", "#6A1B9A", "#E53935", "#6B0F1A", "#546E7A"
    ]
    SEDE_COLORS = {sede: DISTINCT_COLORS_SEDE[i % len(DISTINCT_COLORS_SEDE)] for i, sede in enumerate(sedes_all)}
    
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
        fig = px.line(df_aud, x="Año", y="Programadas", color="Sede",
                      markers=True, title="<b>Audiencias Programadas</b>",
                      color_discrete_map=SEDE_COLORS)
        fig.update_layout(template="custom_theme", height=350, title_font_size=16)
        st.plotly_chart(fig, width='stretch', theme=None)
    with col_b:
        fig2 = px.line(df_aud, x="Año", y="TasaAtencion", color="Sede",
                       markers=True, title="<b>Tasa de Atención por Sede (%)</b>",
                       color_discrete_map=SEDE_COLORS)
        fig2.update_yaxes(tickformat=".0%")
        fig2.add_hline(y=0.95, line_dash="dash", line_color="#4A7C59",
                       annotation_text="Meta 95%", annotation_font_color="#4A7C59")
        fig2.update_layout(template="custom_theme", height=350, title_font_size=16)
        st.plotly_chart(fig2, width='stretch', theme=None)

    col_c, col_d = st.columns(2)
    with col_c:
        tot = df_aud.groupby("Sede")[["Programadas","Atendidas","Suspendidas"]].sum().reset_index()
        fig3 = px.bar(tot.melt(id_vars="Sede"), x="Sede", y="value", color="variable",
                      barmode="group", title="<b>Total Acumulado Programadas/Atendidas/Suspendidas</b>",
                      color_discrete_sequence=["#1565C0", "#2E7D32", "#E53935"],
                      labels={"variable":"","value":"Audiencias"})
        fig3.update_layout(template="custom_theme", height=360, title_font_size=16)
        st.plotly_chart(fig3, width='stretch', theme=None)
    with col_d:
        df_2025 = aud_anual[aud_anual["Año"] == "2025"].dropna(subset=["TasaAtencion"]).copy()
        df_2025 = df_2025.sort_values("TasaAtencion", ascending=True)
        df_2025["Pct"] = (df_2025["TasaAtencion"] * 100).round(1)
        df_2025["Color"] = df_2025["Pct"].apply(
            lambda v: "#4A7C59" if v >= 95 else ("#C4952A" if v >= 80 else "#8B1A2B")
        )
        df_2025["Estado"] = df_2025["Pct"].apply(
            lambda v: "✅ Meta cumplida" if v >= 95 else ("⚠️ En proceso" if v >= 80 else "❌ Bajo meta")
        )
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            y=df_2025["Sede"],
            x=df_2025["Pct"],
            orientation="h",
            marker_color=df_2025["Color"],
            text=df_2025["Pct"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(size=13, color="#333"),
            customdata=df_2025[["Estado","Programadas","Atendidas"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Tasa: %{x:.1f}%<br>"
                "%{customdata[0]}<br>"
                "Programadas: %{customdata[1]:,.0f}<br>"
                "Atendidas: %{customdata[2]:,.0f}"
                "<extra></extra>"
            ),
        ))
        fig4.add_vline(x=95, line_dash="dash", line_color="#4A7C59", line_width=2,
                       annotation_text="Meta 95%", annotation_position="top right",
                       annotation_font_color="#4A7C59", annotation_font_size=11)
        fig4.update_layout(
            title="<b>Tasa de Atención 2025 por Sede</b>",
            template="custom_theme", height=360,
            title_font_size=16,
            xaxis=dict(title="%", range=[0, 108], showgrid=True, gridcolor="#eee"),
            yaxis=dict(title=""),
            margin=dict(l=10, r=60, t=45, b=10),
        )
        st.plotly_chart(fig4, width='stretch', theme=None)

    with st.expander("🗂️ Ver tabla de audiencias"):
        df_show = df_aud.copy()
        df_show.index = range(1, len(df_show) + 1)
        st.dataframe(df_show, width='stretch')

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — PERSONAL JURISDICCIONAL
# ═══════════════════════════════════════════════════════════════════════════
with T_PER:
    # ── Personal Jurisdiccional ──────────────────────────────────────────────
    st.markdown('<div class="section-title" style="font-size: 1.8rem;">Personal Jurisdiccional OOJJ por Régimen Laboral</div>',
                unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        df_pers = pd.DataFrame({
            "Régimen": ["LEY 29277", "728", "276", "CAS", "RECAS"],
            "Cantidad": [121, 482, 3, 331, 137]
        })
        fig_pers = px.pie(df_pers, names="Régimen", values="Cantidad", hole=0.5,
                          title="<b>Distribución por Régimen Laboral</b>",
                          color="Régimen", color_discrete_sequence=["#1565C0", "#F9A825", "#2E7D32", "#E53935", "#6A1B9A"])
        fig_pers.update_traces(textinfo="value+percent", textfont_size=16, 
                               marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_pers.update_layout(height=450, title_font_size=16, margin=dict(t=40, b=10))
        st.plotly_chart(fig_pers, width='stretch', theme=None)
        
    with col_p2:
        st.markdown(f'''
        <div style="display:flex; flex-direction:column; gap:20px; justify-content:center; height:100%; padding:10px;">
            <div style="background:linear-gradient(135deg, {ROJO}, {ROJO2}); padding:25px; border-radius:18px; color:white; text-align:center; box-shadow:0 6px 20px rgba(123,26,26,0.3);">
                <div style="margin:0; font-size:1.6rem; font-weight:600; opacity:0.9; text-transform:uppercase; letter-spacing:1px;">TOTAL PERSONAL JURISDICCIONAL</div>
                <div style="margin:5px 0 0; font-size:6.5rem; font-weight:800; line-height:1;">1,074</div>
            </div>
            <div style="display:flex; gap:15px; flex-wrap:wrap; justify-content:center;">
                <div style="flex:1; min-width: 110px; background:white; padding:15px; border-radius:14px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1); border-bottom:6px solid #F9A825;">
                    <div style="margin:0; font-size:1rem; font-weight:600; color:#555;">728</div>
                    <div style="margin:5px 0 0; font-size:2.5rem; font-weight:800; color:#F9A825; line-height:1;">482</div>
                </div>
                <div style="flex:1; min-width: 110px; background:white; padding:15px; border-radius:14px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1); border-bottom:6px solid #E53935;">
                    <div style="margin:0; font-size:1rem; font-weight:600; color:#555;">CAS</div>
                    <div style="margin:5px 0 0; font-size:2.5rem; font-weight:800; color:#E53935; line-height:1;">331</div>
                </div>
                <div style="flex:1; min-width: 110px; background:white; padding:15px; border-radius:14px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1); border-bottom:6px solid #6A1B9A;">
                    <div style="margin:0; font-size:1rem; font-weight:600; color:#555;">RECAS</div>
                    <div style="margin:5px 0 0; font-size:2.5rem; font-weight:800; color:#6A1B9A; line-height:1;">137</div>
                </div>
                <div style="flex:1; min-width: 110px; background:white; padding:15px; border-radius:14px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1); border-bottom:6px solid #1565C0;">
                    <div style="margin:0; font-size:1rem; font-weight:600; color:#555;">LEY 29277</div>
                    <div style="margin:5px 0 0; font-size:2.5rem; font-weight:800; color:#1565C0; line-height:1;">121</div>
                </div>
                <div style="flex:1; min-width: 110px; background:white; padding:15px; border-radius:14px; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,0.1); border-bottom:6px solid #2E7D32;">
                    <div style="margin:0; font-size:1rem; font-weight:600; color:#555;">276</div>
                    <div style="margin:5px 0 0; font-size:2.5rem; font-weight:800; color:#2E7D32; line-height:1;">3</div>
                </div>
            </div>
        </div>
        '''
        , unsafe_allow_html=True)

    raw_data_pers = """CARGO	LEY 29277	728	276	CAS	RECAS	Total
ADMINISTRADOR		4				4
ADMINISTRADOR DE CORTE SUPERIOR		1				1
ADMINISTRADOR DE MODULO				2		2
ADMINISTRADOR I		1				1
ADMINISTRADOR MÓDULO DEL NUEVO CÓDIGO PROCESAL PENAL		1				1
AGENTE DE  SEGURIDAD				7		7
ANALISTA				1	1	2
ANALISTA ADMINISTRATIVO/A				2		2
ANALISTA DE INFORMATICA				1		1
ANALISTA DE INFORMATICA - DESARROLLADOR				1		1
ANALISTA I		1			1	2
ANALISTA II		7				7
APOYO ADMINISTRATIVO				3	1	4
APOYO ADMINISTRATIVO EN EL ARCHIVO DESCENTRALIZADO DE TARMA Y OTRAS ACTIVIDADES ADMINISTRATIVAS					1	1
APOYO ADMINISTRATIVO EN EL AREA DE NOTIFICACIONES					1	1
APOYO ADMINISTRATIVO EN LAS AREAS DE NOTIFICACIONES					3	3
APOYO EN ACTIVIDADES ADMINISTRATIVAS				1		1
APOYO EN CONTRATACIONES CON EL ESTADO					1	1
APOYO EN EL DESARROLLO DE FUNCIONES DEL EQUIPO ITINERANTE					3	3
APOYO EN INFORMES PSICOLOGICOS					1	1
APOYO EN LA PREPARACION DE ALIMENTOS EN EL WAWA WASI INSTITUCIONAL					1	1
APOYO EN PERICIAS CONTABLES JUDICIALES				1	1	2
APOYO JURISDICCIONAL					2	2
ASESOR DE CORTE		1				1
ASISTENTE ADMINISTRATIVO				6	1	7
ASISTENTE ADMINISTRATIVO I		14		4		18
ASISTENTE ADMINISTRATIVO I MODULO				4		4
ASISTENTE ADMINISTRATIVO II		18		1		19
ASISTENTE DE ATENCION AL PUBLICO				1		1
ASISTENTE DE ATENCIÓN AL PÚBLICO				4		4
ASISTENTE DE COMUNICACIONES				15	2	17
ASISTENTE DE CUSTODIA Y GRABACION				2	1	3
ASISTENTE DE CUSTODIA Y GRABACIÓN				4		4
ASISTENTE DE INFORMÁTICA				4		4
ASISTENTE DE SISTEMAS		2		1		3
ASISTENTE EN INFORMATICA					1	1
ASISTENTE EN SERVICIOS ADMINISTRATIVOS		5		1		6
ASISTENTE EN SERVICIOS DE COMUNICACIONES		13				13
ASISTENTE INFORMÁTICO				3		3
ASISTENTE JUDICIAL		55		20	2	77
ASISTENTE JUDICIAL - PENAL				6		6
ASISTENTE JUDICIAL - PROTECCIÓN				11		11
ASISTENTE JURISDICCIONAL		13		20	2	35
ASISTENTE JURISDICCIONAL DE CUSTODIA DE EXPEDIENTES		3				3
ASISTENTE JURISDICCIONAL DE JUZGADO				22	12	34
ASISTENTE JURISDICCIONAL ITINERANTE					2	2
ASISTENTE LEGAL				9		9
ASISTENTE LEGAL DE JUZGADO				1		1
ASISTENTE SOCIAL				2	1	3
AUXILIAR ADMINISTRATIVO				3		3
AUXILIAR ADMINISTRATIVO I		44				44
AUXILIAR ADMINISTRATIVO II		6				6
AUXILIAR EN VIGILANCIA Y CONTROL				6		6
AUXILIAR JUDICIAL		37		10		47
AUXILIAR JUDICIAL - PROTECCIÓN				5		5
AUXILIAR JUDICIAL I			1			1
AUXILIAR JURISDICCIONAL ITINERANTE					1	1
AUXILIAR LEGAL				1		1
CAJERO		1				1
CHOFER				2	1	3
CHOFER I		3				3
CONDUCCION DE VEHICULO				1	4	5
CONDUCTOR DE VEHÍCULO				1		1
COORDINADOR(CSJ_UE)		16				16
COORDINADOR/A DE CAUSA/ AUDIENCIA				3		3
COORDINADOR/A I				2		2
EDUCADOR (A) DE APOYO AL EQUIPO MULTIDISCIPLINARIO					1	1
ESPECIALISTA EN CONTABILIDAD GUBERNAMENTAL					1	1
ESPECIALISTA JUDICIAL DE AUDIENCIA		19		16	11	46
ESPECIALISTA JUDICIAL DE JUZGADO		30		46	24	100
ESPECIALISTA JUDICIAL DE SALA		4		1		5
ESPECIALISTA LEGAL				11		11
ESPECIALISTA LEGAL DE AUDIENCIA				2		2
ESPECIALISTA LEGAL DE JUZGADO				3		3
ESPECIALISTA LEGAL DE SALA				3		3
JEFE DE UNIDAD		3				3
JEFE/A DE UNIDAD				2		2
JUEZ DE PAZ LETRADO	20					20
JUEZ ESPECIALIZADO	72					72
JUEZ ESPECIALIZADO 7U-4	6					6
JUEZ SUPERIOR	22					22
MADRE CUIDADORA DEL WAWA WASI INSTITUCIONAL					2	2
MEDICO					1	1
NOTIFICADOR				6	3	9
PERITO JUDICIAL		2		2		4
PERSONAL  DE SEGURIDAD				6		6
PRESIDENTE DE CORTE SUPERIOR	1					1
PROFESIONAL LEGAL				2		2
PROFESIONAL LEGAL DE JUZGADO				1		1
PSICOLOGO		5		5	4	14
RELATOR I		4				4
RESGUARDO, CUSTODIA Y VIGILANCIA				6	36	42
REVISOR		1				1
SECRETARIO DE SALA		4				4
SECRETARIO III		1				1
SECRETARIO JUDICIAL		127		4	4	135
SECRETARIO JUDICIAL I			1			1
SECRETARIO/A DE JUZGADO - PROTECCIÓN				7		7
SECRETARIO/A JUDICIAL				11		11
SEGURIDAD				1		1
TECNICO ADMINISTRATIVO I		1				1
TECNICO ADMINISTRATIVO II		1		1		2
TECNICO JUDICIAL		26				26
TECNICO JUDICIAL I			1			1
TRABAJADOR SOCIAL		8				8
TRABAJADORA SOCIAL				1	3	4"""
    
    import io
    df_cargos = pd.read_csv(io.StringIO(raw_data_pers), sep="\t").fillna(0)
    for col in ["LEY 29277", "728", "276", "CAS", "RECAS", "Total"]:
        df_cargos[col] = df_cargos[col].astype(int)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🗂️ Ver desglose detallado por Cargo"):
        st.dataframe(df_cargos, width='stretch')

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:22px 0 8px;color:#aaa;font-size:.74rem;">
  ⚖️ Corte Superior de Justicia de Junín &nbsp;
</div>""", unsafe_allow_html=True)
