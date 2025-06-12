import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import time
import math

# streamlit run C:\Users\laloi\PycharmProjects\Projet_final_G3\Tubulence\affiche_carte.py

st.set_page_config(layout="wide")
st.title("🌍 Zones de turbulences volumétriques selon altitude")

def generer_dataframe(nb_points=5):
    data = {
        'latitude': np.random.uniform(-60, 60, size=nb_points),
        'longitude': np.random.uniform(-180, 180, size=nb_points),
        'altitude': np.random.uniform(8000, 13000, size=nb_points),
        'nom': [f'Zone {i+1}' for i in range(nb_points)],
        'diametre': [50000] * nb_points  # diamètre en mètres
    }
    return pd.DataFrame(data)

# Fonction pour générer un polygone circulaire autour d'un point lat/lon
def generer_polygone_cercle(lat, lon, rayon_m, nb_points=30):
    """
    Génère une liste de points (lat, lon) formant un cercle autour du centre
    rayon_m: rayon en mètres
    """
    coords = []
    # Rayon de la terre approx
    R = 6371000
    for i in range(nb_points):
        angle = 2 * math.pi * i / nb_points
        dlat = (rayon_m / R) * math.cos(angle)
        dlon = (rayon_m / (R * math.cos(math.pi * lat / 180))) * math.sin(angle)
        point_lat = lat + dlat * 180 / math.pi
        point_lon = lon + dlon * 180 / math.pi
        coords.append([point_lon, point_lat])
    coords.append(coords[0])  # Fermer le polygone
    return coords

carte_container = st.empty()

while True:
    df = generer_dataframe()

    # Créer une liste de polygones avec extrusion
    polygones = []
    for _, row in df.iterrows():
        poly = {
            "polygon": generer_polygone_cercle(row.latitude, row.longitude, row.diametre / 2),
            "elevation": row.altitude,
            "nom": row.nom,
            "couleur": [255, 0, 0, 150]
        }
        polygones.append(poly)

    layer = pdk.Layer(
        "PolygonLayer",
        data=polygones,
        get_polygon="polygon",
        get_fill_color="couleur",
        get_elevation="elevation",
        elevation_scale=1,
        extruded=True,
        stroked=True,
        filled=True,
        wireframe=True,
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=1.5,
        pitch=45,
        bearing=0
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v9",
        tooltip={"text": "{nom}\nAltitude: {elevation} m"}
    )

    carte_container.pydeck_chart(deck)
    time.sleep(5)
