import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update ESP_COLORS
old_colors = '''    ESP_COLORS = {
        "CIVIL":            "#2E86C1",  # Azul vibrante
        "FAMILIA":          "#27AE60",  # Verde fuerte
        "LABORAL":          "#8E44AD",  # Morado oscuro
        "PENAL":            "#C0392B",  # Rojo carmín
        "CONSTITUCIONAL":   "#F39C12",  # Naranja
        "EXTINCION DOMINIO":"#16A085",  # Verde mar
    }'''

new_colors = '''    ESP_COLORS = {
        "CIVIL":            "#1f77b4",  # Azul clásico
        "FAMILIA":          "#2ca02c",  # Verde esmeralda
        "LABORAL":          "#9467bd",  # Púrpura profundo
        "PENAL":            "#d62728",  # Rojo alerta
        "CONSTITUCIONAL":   "#e377c2",  # Rosa fuerte
        "EXTINCION DOMINIO":"#8c564b",  # Marrón
    }'''
content = content.replace(old_colors, new_colors)

# 2. Remove legend block
legend_block = '''    # Leyenda visual de colores encima del filtro
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">'
    for esp in esp_all:
        color = ESP_COLORS.get(esp, "#CCC")
        legend_html += f'<div style="display: flex; align-items: center; gap: 5px;"><div style="width: 14px; height: 14px; background-color: {color}; border-radius: 3px; border: 1px solid rgba(0,0,0,0.1);"></div><span style="font-size: 0.9rem; color: #555; font-weight: 600;">{esp}</span></div>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)

'''
content = content.replace(legend_block, '')

# 3. Add theme=None
content = re.sub(r'st\.plotly_chart\(([^,]+),\s*use_container_width=True\)', r'st.plotly_chart(\1, use_container_width=True, theme=None)', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
