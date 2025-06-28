"""
affiche_carte.py ― Visualisation Streamlit/PyDeck
=================================================

Module d’affichage du projet *ETS_en_Turbulence* (MGA802, ÉTS Montréal).

Il expose deux classes :

* **Data**  – Convertit un tableau NumPy/Python en :class:`pandas.DataFrame`
  enrichi (colonnes géographiques + métadonnées).
* **Carte** – Affiche toutes les zones de turbulence dans une unique
  :class:`pydeck.Layer` *Scatterplot*, avec couleur/diamètre/opacité
  paramétrés par la confiance et le diamètre estimé.
"""


import streamlit as st
import pandas as pd
import pydeck as pdk


class Data:
    """
    Convertit un tableau de turbulences en DataFrame prêt pour PyDeck.

    Parameters
    ----------
    tableau_turbulences : list | numpy.ndarray
        Tableau *(N, 5)* – `[lat, lon, alt, diam, confiance]`.
    label : str, default ``"originale"``
        Étiquette de provenance (p. ex. « originale », « prédite »).

    Attributes
    ----------
    turbulences : numpy.ndarray | list
        Données brutes conservées telles quelles.
    label : str
        Étiquette passée au constructeur.
    """
    def __init__(self, tableau_turbulences, label="originale",):
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
    Carte interactive PyDeck des turbulences en cours.

    Parameters
    ----------
    *data_objects : Data
        Un ou plusieurs objets :class:`Data` fournissant chacun un
        DataFrame à afficher.
    """

    def __init__(self, *data_objects):
        self.data_objects = data_objects

    def affichage(self):
        """
        Affiche la carte dans Streamlit (`st.pydeck_chart`).

        - Concatène tous les DataFrames.
        - Calcule une couleur RGBA par ligne
          (rouge = confiance 100 %, bleu translucide sinon).
        - Rend une seule *ScatterplotLayer* pour plus de performance.
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
