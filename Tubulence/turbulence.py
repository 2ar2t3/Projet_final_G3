import pandas as pd
import numpy as np
from collections import deque

class Turbulence():

    def __init__(self, maxlen=5):
        self.last_states = deque(maxlen=maxlen)# Liste circulaire des derniers DataFrames uniques
        self.prev_state = None  # Pour comparer avec le nouveau


    def get_turbulences(self, states):
        """
        Met a jour les 5 derniers etats si le nouvel etat est différent.
        Appelle search_turbulences si 5 etats uniques sont disponibles.
        """

        # Comparaison avec l'etat precedent
        if self.prev_state is None or not states.equals(self.prev_state):
            self.prev_state = states.copy()

            # Ajout a la liste, on garde les 5 derniers
            self.last_states.append(states)
            print(f"length of states: {len(self.last_states)}")
            if len(self.last_states) > 5:
                self.last_states.pop(0)

        # Si on a au moins 5 etats, on les analyse
        if len(self.last_states) == 5:
            five_states = pd.concat(self.last_states, keys=range(5), names=['TimeIndex'])
            return self.search_turbulences(five_states)
        else:
            return None  # Pas encore assez de données


    def search_turbulences(self, states):
        """
        Analyse les 5 derniers états et détecte des turbulences.
        Implémentation factice ici.
        """

        # Group by 'nom' pour avoir les altitudes pour chaque avion
        alt_stats = states.groupby('nom')['altitude'].agg(['mean', 'std']).rename(
            columns={'mean': 'alt_mean', 'std': 'alt_std'})

        # Rejoin les statistiques dans le DF
        states = states.reset_index().merge(alt_stats, on='nom')

        # Identifie les rangees ou l'altitude est en dehors ±1 ecart type
        outliers = states[
            (states['altitude'] > states['alt_mean'] + states['alt_std']) |
            (states['altitude'] < states['alt_mean'] - states['alt_std'])
            ]

        # Extrait la longitude et latitude en NumPy array
        resultat = outliers[['longitude', 'latitude']].to_numpy()
        # Utilise pour tester quelles longitudes et lattitudes sont retournees ////////////////////////////////////////
        # print(resultat[0])

        return resultat






