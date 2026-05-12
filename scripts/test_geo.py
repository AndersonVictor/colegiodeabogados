import json
import os

import plotly.graph_objects as go
import plotly.io as pio

_ROOT = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_ROOT)
_GEOJSON = os.path.join(_PROJECT, "data", "peru_provincial_simple.geojson")

with open(_GEOJSON, encoding="utf-8") as f:
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

fig_map = go.Figure(go.Choropleth(
    geojson=geo_dj,
    locations=[f["properties"]["NOMBPROV"] for f in geo_dj["features"]],
    featureidkey="properties.NOMBPROV",
    z=[1]*len(geo_dj["features"]),
    colorscale="Blues",
    marker_line_color="#6B0F1A",
    marker_line_width=2,
    showscale=False
))

fig_map.add_trace(go.Scattergeo(
    lat=label_lats, lon=label_lons,
    mode="text",
    text=label_texts,
    textfont=dict(size=15, color="#000000", family="Arial Black, Inter, sans-serif"),
    showlegend=False,
))

fig_map.update_layout(
    geo=dict(
        fitbounds="locations",
        visible=False,
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    paper_bgcolor="rgba(242,232,217,0)"
)
fig_map.write_html(os.path.join(_ROOT, "test_geo.html"))
