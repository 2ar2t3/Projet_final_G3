"""
Visualisation interactive de zones de turbulence avec Streamlit et PyDeck.

Ce script définit deux classes :
- `Data` : structure et enrichit des données de turbulences (latitude, longitude, altitude, diamètre, confiance),
           en les convertissant en un DataFrame prêt à être visualisé.
- `Carte` : prend un ou plusieurs objets `Data` et génère une carte interactive avec PyDeck pour afficher
            les zones de turbulence sous forme de cercles colorés selon le niveau de confiance.

L’interface est conçue pour être utilisée dans une application Streamlit, permettant une exploration
géographique intuitive des zones de turbulence.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk


class Data:
    """
        Représente un ensemble de zones de turbulence avec leur origine (étiquette).
        Permet la conversion vers un DataFrame enrichi pour visualisation.
    """
    def __init__(self, tableau_turbulences, label="originale",):
        """
               Initialise les données de turbulence.

               :param tableau_turbulences: Tableau (liste ou ndarray) contenant les zones de turbulence.
                   Chaque entrée doit être [latitude, longitude, altitude, diamètre, confiance].
               :param label: Étiquette utilisée pour identifier l’origine des données.
        """

        self.turbulences = tableau_turbulences
        self.label = label

    def generer_dataframe(self):
        """
                Génère un DataFrame pandas enrichi à partir des données.

                :return: Un DataFrame avec colonnes géographiques, attributs et métadonnées.
                :rtype: pandas.DataFrame
        """
        df = pd.DataFrame(self.turbulences, columns=['latitude', 'longitude', 'altitude', 'diametre', 'confiance'])
        df['Turbulences'] = [f'Zone {i + 1} ({self.label})' for i in range(len(df))]
        df['source'] = self.label
        return df

class Carte:
    """
       Affiche une carte interactive des zones de turbulence à l’aide de PyDeck et Streamlit.
    """
    def __init__(self, *data_objects):
        """
                Initialise la carte avec un ou plusieurs objets `TurbulenceData`.

                :param data_objects: Un ou plusieurs objets TurbulenceData.
        """
        self.data_objects = data_objects

    def affichage(self):
        """
                Affiche la carte avec toutes les zones de turbulence.
                Utilise une seule couche `ScatterplotLayer` avec des couleurs variables selon la confiance.
        """
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
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            tooltip={"text": "{Turbulences}\nAltitude: {altitude} m"}
        )

        st.pydeck_chart(deck)
