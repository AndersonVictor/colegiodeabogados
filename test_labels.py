import json

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

for t, lat, lon in zip(label_texts, label_lats, label_lons):
    print(f"{t}: {lat:.3f}, {lon:.3f}")
