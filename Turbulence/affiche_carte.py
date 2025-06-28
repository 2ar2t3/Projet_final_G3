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
        dfs = [data_obj.generer_dataframe() for data_obj in self.data_objects]
        df_all = pd.concat(dfs)

        # Applique les couleurs en une fois
        def couleur(row):
            if row["confiance"] == 100:
                return [255, 0, 0, 160]
            else:
                return [0, 0, 255, int(160 * row["confiance"] / 100)]

        df_all["color"] = df_all.apply(couleur, axis=1)

        # Une seule couche avec tous les points
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_all,
            get_position='[longitude, latitude]',
            get_radius='diametre / 2',
            get_fill_color='color',
            pickable=True,
            opacity=0.6,
            stroked=True,
            filled=True
        )

        view_state = pdk.ViewState(
            latitude=df_all["latitude"].mean(),
            longitude=df_all["longitude"].mean(),
            zoom=3,
            pitch=0,
            bearing=0
        )

        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/light-v9",
            tooltip={"text": "{Turbulences}\nAltitude: {altitude} m"}
        )

        st.pydeck_chart(deck)