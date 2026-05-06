import sys
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Define SEDE_COLORS and inject CSS in T_AUD
old_taud = """with T_AUD:
    st.markdown('<div class="section-title">Audiencias por Sede y Año (2017–2026)</div>',
                unsafe_allow_html=True)

    aud_anual = aud[aud["TipoAnio"] == "Anual"].copy()
    sedes_all = sorted(aud_anual["Sede"].unique())
    sel_sedes = st.multiselect("Sedes:", sedes_all, default=sedes_all, key="sedes_aud")"""

new_taud = """with T_AUD:
    st.markdown('<div class="section-title">Audiencias por Sede y Año (2017–2026)</div>',
                unsafe_allow_html=True)

    SEDE_COLORS = {
        "HUANCAYO": "#2E86C1",
        "TARMA": "#27AE60",
        "JAUJA": "#8E44AD",
        "CHUPACA": "#C0392B",
        "CONCEPCION": "#F39C12",
        "YAULI": "#16A085",
        "JUNIN": "#D35400",
        "TAYACAJA": "#34495E"
    }

    aud_anual = aud[aud["TipoAnio"] == "Anual"].copy()
    sedes_all = sorted(aud_anual["Sede"].unique())

    chip_css_sedes = ""
    for sede_name, sede_color in SEDE_COLORS.items():
        chip_css_sedes += f\"\"\"
        [data-baseweb="tag"] span[title="{sede_name}"] ~ div,
        [data-baseweb="tag"]:has(span[title="{sede_name}"]) {{
            background-color: {sede_color} !important;
            color: #fff !important;
            border: 1.5px solid {sede_color} !important;
        }}
        \"\"\"
    st.markdown(f"<style>{{chip_css_sedes}}</style>", unsafe_allow_html=True)
    
    legend_html_sedes = '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">'
    for sede in sedes_all:
        color = SEDE_COLORS.get(sede, "#CCC")
        legend_html_sedes += f'<div style="display: flex; align-items: center; gap: 5px;"><div style="width: 14px; height: 14px; background-color: {color}; border-radius: 3px; border: 1px solid rgba(0,0,0,0.1);"></div><span style="font-size: 0.9rem; color: #555; font-weight: 600;">{{sede}}</span></div>'
    legend_html_sedes += '</div>'
    st.markdown(legend_html_sedes, unsafe_allow_html=True)

    sel_sedes = st.multiselect("Sedes:", sedes_all, default=sedes_all, key="sedes_aud")"""
content = content.replace(old_taud, new_taud)

# 2. Fix the charts in T_AUD to use SEDE_COLORS
old_chart1 = """fig = px.line(df_aud, x="Año", y="Programadas", color="Sede",
                      markers=True, title="Audiencias Programadas",
                      color_discrete_map=ESP_COLORS)"""
new_chart1 = """fig = px.line(df_aud, x="Año", y="Programadas", color="Sede",
                      markers=True, title="Audiencias Programadas",
                      color_discrete_map=SEDE_COLORS)"""
content = content.replace(old_chart1, new_chart1)

old_chart2 = """fig2 = px.line(df_aud, x="Año", y="TasaAtencion", color="Sede",
                       markers=True, title="Tasa de Atención por Sede (%)",
                       color_discrete_map=ESP_COLORS)"""
new_chart2 = """fig2 = px.line(df_aud, x="Año", y="TasaAtencion", color="Sede",
                       markers=True, title="Tasa de Atención por Sede (%)",
                       color_discrete_map=SEDE_COLORS)"""
content = content.replace(old_chart2, new_chart2)

# 3. Add bargap to fig4 (Tasa de Atencion 2025)
old_fig4_layout = """        fig4.update_layout(
            title="Tasa de Atención 2025 por Sede",
            template="custom_theme", height=360,"""
new_fig4_layout = """        fig4.update_layout(
            title="Tasa de Atención 2025 por Sede",
            template="custom_theme", height=360,
            bargap=0.4,"""
content = content.replace(old_fig4_layout, new_fig4_layout)

# 4. Insert apply_big_fonts
helper_func = """def apply_big_fonts(fig):
    if hasattr(fig, "update_xaxes"):
        fig.update_xaxes(title_font=dict(size=20), tickfont=dict(size=14))
        fig.update_yaxes(title_font=dict(size=20), tickfont=dict(size=14))
    return fig

"""
# Find "# ── HEADER ───────────────────────────────────────────────────────────────────"
content = content.replace("# ── HEADER", helper_func + "# ── HEADER")

# Replace st.plotly_chart(fig_something
content = re.sub(r'st\.plotly_chart\((fig\w*)', r'st.plotly_chart(apply_big_fonts(\1)', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
