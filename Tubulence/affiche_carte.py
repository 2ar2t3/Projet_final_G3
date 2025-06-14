import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import math
import time

st.set_page_config(layout="wide")

# streamlit run C:\Users\laloi\PycharmProjects\Projet_final_G3\Tubulence\affiche_carte.py

class Data:
    def __init__(self, tableau_turbulences):
        self.turbulences = tableau_turbulences

    def generer_dataframe(self):
        df = pd.DataFrame(self.turbulences, columns=['latitude', 'longitude', 'altitude'])
        df['Turbulences'] = [f'Zone {i + 1}' for i in range(len(df))]
        df['diametre'] = 50000
        return df

        # Fonction pour générer un polygone circulaire autour d'un point lat/lon
    def generer_polygone_cercle(self, lat, lon, rayon_m, nb_points=30):
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


class Carte:
    def __init__(self, Data):
        self.Data = Data

    def affichage(self):

        st.title("🌍 Zones de turbulences volumétriques selon altitude")

        carte_container = st.empty()

        df = self.Data.generer_dataframe()

        # Créer une liste de polygones avec extrusion
        polygones = []
        for _, row in df.iterrows():
            poly = {
                  "polygon": self.Data.generer_polygone_cercle(row.latitude, row.longitude, row.diametre / 2),
                  "elevation": row.altitude,
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

"""
if __name__ == "__main__":
    turbulences_array = np.array([
        [48.8566, 2.3522, 10000],
        [34.0522, -118.2437, 11000],
        [35.6895, 139.6917, 12000]
    ])
    data = Data(turbulences_array)
    carte = Carte(data)
    carte.affichage()
"""