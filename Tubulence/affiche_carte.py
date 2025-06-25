import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from modele_deplacement_turbulence import *

class Data:
    def __init__(self, tableau_turbulences, label="originale",):
        self.turbulences = tableau_turbulences
        self.label = label

    def generer_dataframe(self):
        df = pd.DataFrame(self.turbulences, columns=['latitude', 'longitude', 'altitude', 'diametre', 'confiance'])
        df['Turbulences'] = [f'Zone {i + 1} ({self.label})' for i in range(len(df))]
        df['source'] = self.label
        return df

class Carte:
    def __init__(self, *data_objects):
        self.data_objects = data_objects

    def affichage(self):
        # Fusion de tous les DataFrames
        dfs = [data_obj.generer_dataframe() for data_obj in self.data_objects]
        df_all = pd.concat(dfs)

        layers = []
        for _, df_part in df_all.groupby(["source"]):
            conf = df_part['confiance'].iloc[0]
            if "originale" in df_part["source"].iloc[0]:
                color = [255, 0, 0 , 160]
            else:
                facteur_opacite = conf/100
                color = [0, 0, 255, int(160*facteur_opacite)]

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_part,
                get_position='[longitude, latitude]',
                get_radius='diametre / 2',
                get_fill_color=color,
                pickable=True,
                opacity=0.6,
                stroked=True,
                filled=True
            )
            layers.append(layer)

        view_state = pdk.ViewState(
            latitude=df_all["latitude"].mean(),
            longitude=df_all["longitude"].mean(),
            zoom=3,
            pitch=0,
            bearing=0
        )

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/light-v9",
            tooltip={"text": "{Turbulences}\nAltitude: {altitude} m"}
        )

        st.pydeck_chart(deck)

"""
# Jeu de données initial : [lat, lon, alt, diam, confiance]
turb_array = np.array([[45.0, -73.0, 10000, 5000, 100]])
meteo_array = np.array([[20, 90, 0.2, -0.1]])

nb_iterations = 10
data_list = [Data(turb_array, label="originale")]

current = turb_array.copy()

for i in range(nb_iterations):
    # déplace et décrémente confiance (10 points par itération)
    current = deplacement_turbulence(current, meteo_array)

    # filtre les turbulences dont la confiance est > 0
    current = current[current[:, 4] > 0]

    # si tout est effacé, on s'arrête
    if current.size == 0:
        break

    # on ajoute pour affichage
    confiance = int(current[0, 4])
    data_list.append(Data(current.copy(), label=f"predite {i + 1}"))

# Affichage final
carte = Carte(*data_list)
carte.affichage()
"""