import math
from collections import deque
import numpy as np
import pandas as pd

class TurbulenceDetector:
    def __init__(self, window_size=5):
        """
        Initialise le détecteur de turbulences.
        :param window_size: nombre de ticks à conserver dans l'historique pour chaque avion.
        """
        self.window_size = window_size
        # Historique des derniers états pour chaque avion: {nom_avion: deque[maxlen=window_size] de tuples (lat, lon, alt, vr)}
        self.history = {}
        # Instabilités provisoires: {nom_avion: {"count": nb_ticks_instables_consecutifs, "start": (lat, lon, alt)}}
        self.instabilite_provisoire = {}
        # Turbulences en cours: {nom_avion: {"start": (lat, lon, alt), "end": (lat, lon, alt) ou None, "stable_count": nb_ticks_stables_consecutifs}}
        self.turbulence_en_cours = {}

    def update(self, states_df):
        """
        Met à jour les données avec le nouveau DataFrame d'états 'states_df' (colonnes: name, latitude, longitude, altitude, vertical_rate).
        Renvoie une liste d'événements de turbulence terminés (s'il y en a) sous forme de dictionnaires.
        """
        # On transforme l'index numérique en nom pour regrouper les données par avion
        if 'nom' in states_df.columns:
            states_df = states_df.set_index('nom')

        # Liste des événements de turbulences terminés à retourner
        turbulences_terminees = []

        # 1. Mise à jour de l'historique des avions
        # Ajouter nouveaux avions et mettre à jour les existants
        for plane_name, row in states_df.iterrows():
            lat = row['latitude']; lon = row['longitude']
            alt = row['altitude']; vr = row['vertical_rate']

            if plane_name not in self.history:
                # Nouvel avion détecté: initialiser une deque pour son historique
                self.history[plane_name] = deque(maxlen=self.window_size)

            # Ajouter l'état courant de l'avion à son historique
            self.history[plane_name].append((lat, lon, alt, vr))

        # Identifier les avions qui ont disparu (présents auparavant mais pas dans le states_df actuel)
        existing_planes = set(self.history.keys()) #avions des 5 ticks précédents
        current_planes = set(states_df.index) #avions du tick récent
        disappeared = existing_planes - current_planes

        for plane_name in disappeared:
            # Supprimer l'avion disparu de tous les tableaux
            self.history.pop(plane_name, None)
            self.instabilite_provisoire.pop(plane_name, None)
            self.turbulence_en_cours.pop(plane_name, None)


        # 2. Détection des instabilités et mise à jour des états de turbulence
        for plane_name, hist_deque in list(self.history.items()):
            # Ne vérifier que si l'historique est complet (deque pleine)
            if len(hist_deque) < self.window_size:
                continue  # passer si historique pas encore suffisamment rempli

            # Récupérer les N derniers vertical_rate de l'historique pour analyse
            vertical_rates = [state[3] for state in hist_deque]  # index 3 correspond à vertical_rate
            # Vérifier l'instabilité du vertical_rate sur ces N valeurs
            instable = self.instabilite_detectee(vertical_rates)

            # Si l'avion est actuellement en turbulence confirmée, on gère directement la logique de fin potentielle
            if plane_name in self.turbulence_en_cours:
                if instable:
                    # Si l'avion est en turbulence et reste instable, reset du compteur de stabilité
                    self.turbulence_en_cours[plane_name]['stable_count'] = 0
                else:
                    # Avion en turbulence qui devient stable
                    self.turbulence_en_cours[plane_name]['stable_count'] += 1

                    if self.turbulence_en_cours[plane_name]['stable_count'] == 1:
                        lat_end, lon_end, alt_end, _ = hist_deque[-2]
                        self.turbulence_en_cours[plane_name]['candidate_end'] = (
                            lat_end, lon_end, alt_end)

                    if self.turbulence_en_cours[plane_name]['stable_count'] == 2:
                        # Deux ticks stables consécutifs -> fin de la turbulence
                        # Calculer le "diamètre" basé sur la distance entre début et fin

                        start_coords = self.turbulence_en_cours[plane_name]['start']
                        end_coords = self.turbulence_en_cours[plane_name].get(
                            'candidate_end')

                        distance_km = self.distance_horizontale_km(start_coords, end_coords)
                        # Préparer l'événement de turbulence terminé
                        event = {
                            "plane": plane_name,
                            "start": {"lat": start_coords[0], "lon": start_coords[1], "alt": start_coords[2]},
                            "end": {"lat": end_coords[0], "lon": end_coords[1], "alt": end_coords[2]},
                            "distance_km": round(distance_km, 3)
                        }
                        turbulences_terminees.append(event)
                        # Retirer l'événement de turbulence en cours (l'avion redevient normal)
                        self.turbulence_en_cours.pop(plane_name, None)
                # Si l'avion est en turbulence confirmée, on ne traite pas la partie "instabilite_provisoire" ci-dessous
                continue

            # Si on arrive ici, l'avion n'est pas (ou plus) en turbulence confirmée.
            if instable:
                # Cas 3a. Avion instable actuellement (détecté par instabilite())
                if plane_name in self.instabilite_provisoire:
                    # Incrémenter le compteur d'instabilité consécutive
                    self.instabilite_provisoire[plane_name]['count'] += 1
                else:
                    # Ajouter l'avion en instabilité provisoire avec compteur = 1
                    lat0, lon0, alt0, _ = hist_deque[-1]  # coordonnées au tick actuel (début de l'instabilité)
                    self.instabilite_provisoire[plane_name] = {"count": 1, "start": (lat0, lon0, alt0)}
                # Vérifier si on atteint 3 instabilités consécutives
                if self.instabilite_provisoire[plane_name]['count'] >= 3:
                    # Valider la turbulence
                    start_coords = self.instabilite_provisoire[plane_name]['start']
                    # Initialiser un enregistrement de turbulence en cours avec le point de début
                    self.turbulence_en_cours[plane_name] = {"start": start_coords, "end": None, "stable_count": 0}
                    # Enlever l'avion de la liste provisoire
                    self.instabilite_provisoire.pop(plane_name, None)
                    # (Optionnel: on pourrait signaler immédiatement le début de turbulence ici, selon les besoins)
            else:
                # Cas 3b. Avion stable actuellement
                if plane_name in self.instabilite_provisoire:
                    # Il redevient stable avant 3 -> annuler l'instabilité provisoire
                    self.instabilite_provisoire.pop(plane_name, None)
                # (Si l'avion n'était ni instable provisoire ni en turbulence, ne rien faire)

        print('taille = ', len(self.history))
        for plane_name, deque_avion in self.history.items():
            print(f"{plane_name} ➜ {deque_avion}")
        print(self.turbulence_en_cours)

        return turbulences_terminees

    def instabilite_detectee(self, vertical_rates):
        """(a, c, c, d, g)
        Analyse une liste des derniers vertical_rate pour déterminer s'il y a instabilité.
        Retourne True si instabilité détectée, False sinon.
        (Critère à affiner en fonction des besoins : ici simple écart-type ou variation brusque par exemple)
        """
        # Exemple de critère simplifié: instabilité si la variation absolue max du vertical_rate dépasse un seuil.
        variations = [abs(vertical_rates[i] - vertical_rates[i-1]) for i in range(1, len(vertical_rates))]
        # Seuil arbitraire: par exemple 500 (ft/min) - à ajuster selon les données réelles
        return max(variations) > 500

    def distance_horizontale_km(self, coord1, coord2):
        """
        Calcule la distance horizontale (en kilomètres) entre deux points géographiques (lat, lon, alt).
        On ignore la différence d'altitude pour le calcul horizontal.
        """
        lat1, lon1, _ = coord1
        lat2, lon2, _ = coord2
        # Conversion degrés -> radians
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        # Rayon de la Terre en km (sphère moyenne)
        R = 6371.0
        # Formule de haversine
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        return distance