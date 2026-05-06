import json
import plotly.graph_objects as go
import plotly.io as pio

with open("peru_provincial_simple.geojson", encoding="utf-8") as f:
    geo_all = json.load(f)

PROVINCIAS_DJ = {"HUANCAYO","TARMA","JAUJA","CHUPACA","CONCEPCION","YAULI","JUNIN","TAYACAJA"}

geo_dj = {"type":"FeatureCollection",
          "features":[ft for ft in geo_all["features"]
                       if ft["properties"].get("NOMBPROV","") in PROVINCIAS_DJ]}

label_lats, label_lons, label_texts = [], [], []
for ft in geo_dj["features"]:
    prov_label = ft["properties"].get("NOMBPROV", "")
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
        label_texts.append(prov_label.upper())

fig = go.Figure(go.Choroplethmapbox(
    geojson=geo_dj,
    locations=[f["properties"]["NOMBPROV"] for f in geo_dj["features"]],
    featureidkey="properties.NOMBPROV",
    z=[1]*len(geo_dj["features"]),
    colorscale="Blues",
    marker_line_color="#6B0F1A",
    marker_line_width=2,
    marker_opacity=0.85,
    showscale=False
))

fig.add_trace(go.Scattermapbox(
    lat=label_lats, lon=label_lons,
    mode="text",
    text=label_texts,
    textfont=dict(size=15, color="#000000", family="Arial Black, Inter, sans-serif"),
    textposition="middle center",
    showlegend=False,
))

fig.update_layout(
    mapbox_style="white-bg",
    mapbox=dict(center=dict(lat=-11.8, lon=-75.3), zoom=7.5),
    margin=dict(l=0, r=0, t=40, b=0),
    paper_bgcolor="rgba(242,232,217,0)"
)
fig.write_html("test_map.html")
