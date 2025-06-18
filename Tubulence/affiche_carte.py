import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from modele_deplacement_turbulence import *

class Data:
    def __init__(self, tableau_turbulences, label="originale"):
        self.turbulences = tableau_turbulences
        self.label = label

    def generer_dataframe(self):
        df = pd.DataFrame(self.turbulences, columns=['latitude', 'longitude', 'altitude', 'diametre'])
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

        # Création d'un Scatterplot par type
        colors = {
            'originale': [255, 0, 0, 160],   # Rouge
            'predite': [0, 0, 255, 160]      # Bleu
        }

        layers = []
        for source in df_all['source'].unique():
            df_part = df_all[df_all['source'] == source]
            color = colors.get(source, [0, 255, 0, 160])  # Vert par défaut
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