"""
turbulence.py ― Détection d’instabilités sur trajectoires ADS-B
===============================================================

Composant cœur du projet **ETS_en_Turbulence** (MGA802, ÉTS Montréal).

Rôle
----
Analyse, pour chaque avion suivi, une fenêtre glissante de vitesses
verticales (`vertical_rate`) afin de confirmer ou non la présence
d’une **turbulence** :

1. **Historique** par appareil (latitude, longitude, altitude, *vr*).
2. **Instabilité provisoire** : au moins 3 ticks instables consécutifs.
3. **Turbulence confirmée** : fin lorsque l’avion redevient stable 2 ticks.
4. **Sortie** : événements terminés ⟶ centre + diamètre en km.
"""


import math
from collections import deque
import numpy as np

class TurbulenceDetector:
    """
    Détecteur d’instabilités verticales sur une fenêtre glissante.

    Parameters
    ----------
    window_size : int, default ``5``
        Nombre de ticks conservés dans l’historique pour chaque avion.

    Attributes
    ----------
    history : dict[str, deque[tuple]]
        Derniers états `(lat, lon, alt, vr)` par appareil.
    instabilite_provisoire : dict[str, dict]
        Compteurs d’instabilité en attente de validation.
    turbulence_en_cours : dict[str, dict]
        Turbulences confirmées non encore clôturées.
    """

    def __init__(self, window_size=5):
        self.window_size = window_size

        # Historique des derniers états pour chaque avion: {nom_avion: deque[maxlen=window_size] de tuples (lat, lon, alt, vr)}
        self.history = {}

        # Instabilités provisoires: {nom_avion: {"count": nb_ticks_instables_consecutifs, "start": (lat, lon, alt)}}
        self.instabilite_provisoire = {}

        # Turbulences en cours: {nom_avion: {"start": (lat, lon, alt), "end": (lat, lon, alt) ou None, "stable_count": nb_ticks_stables_consecutifs}}
        self.turbulence_en_cours = {}

    def update(self, states_df):
        """
        Met à jour les états des avions suivis et détecte les événements de turbulence.

        Cette méthode prend en entrée un DataFrame contenant les données d'état actuelles des avions.
        Elle met à jour l’historique de chaque avion et utilise une fenêtre glissante pour analyser
        les variations du taux de montée/descente (``vertical_rate``). Si une instabilité est détectée
        de manière prolongée, cela peut déclencher un événement de turbulence. Lorsqu’un avion redevient
        stable, un événement de fin de turbulence est enregistré et retourné.

        Les avions qui ne sont plus présents dans les données actuelles sont supprimés du suivi.

        :param states_df: Un DataFrame contenant les données actuelles des avions.
            Doit contenir les colonnes suivantes : ``latitude``, ``longitude``, ``altitude``, ``vertical_rate``.
            Une colonne ``nom`` est également attendue pour l'identification des avions.
        :type states_df: pandas.DataFrame

        :return: Une liste d’événements de turbulence terminés. Chaque événement est représenté par un dictionnaire
            contenant les coordonnées de début et de fin, ainsi que la distance horizontale entre les deux points.
        :rtype: list of dict
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

            # Ajouter l'état courant de l'avion à son historiquen
            self.history[plane_name].append((lat, lon, alt, vr))

        # Identifier les avions qui ont disparu (présents auparavant mais pas dans le states_df actuel)
        existing_planes = set(self.history.keys()) #avions des 5 ticks précédents
        current_planes = set(states_df.index) #avions du tick récent
        # print(f"Nombre d'avions en vol: {len(current_planes)}") # ///////////////////////////////////////////////////////////////////
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

        print(f"Nombre d'avions en turbulence: {len(self.turbulence_en_cours)}")# //////////////////////////////////////////////////////
        return self.centre_turbulence(turbulences_terminees)

    def instabilite_detectee(self, vr_list):
        """Détecte une instabilité verticale (turbulence) à partir d'une série de vitesses verticales.

        Cette méthode analyse une fenêtre de 5 valeurs successives de taux de montée/descente
        (``vertical_rate`` en m/s) et évalue plusieurs critères d’instabilité basés sur
        les variations de direction et d’amplitude. Elle retourne `True` si un comportement
        turbulent est détecté, `False` sinon.

        Critères :\n
        - Saut instantané important (variation >= 10 m/s entre deux pas)\n
        - Au moins deux inversions de direction avec un mouvement cumulé > 12 m\n
        - Une seule inversion avec un mouvement cumulé > 15 m\n

        :param vr_list: Liste de 5 valeurs successives de vertical_rate (m/s)
        :type vr_list: list of float

        :raises ValueError: Si la liste contient moins de 5 éléments

        :return: `True` si une turbulence est détectée, sinon `False`
        :rtype: bool
        """

        # Vérifier que 5 valeurs sont fournies
        if vr_list is None or len(vr_list) < 5:
            raise ValueError("La liste vr_list doit contenir 5 valeurs de vertical_rate.")
        # Calcul des variations successives (différences) de vertical_rate entre
        diffs = [vr_list[i + 1] - vr_list[i] for i in range(len(vr_list) - 1)]
        # Compter les changements de signe des variations (ignorer les diffs nulles)
        sign_changes = 0
        last_sign = 0
        for d in diffs:
            if d == 0:
                continue  # on ignore les variations nulles (pas de changement)
            sign = 1 if d > 0 else -1
            if last_sign == 0:
                last_sign = sign
            elif sign != last_sign:
                sign_changes += 1
                last_sign = sign

        # Calcul de l'amplitude totale de variation sur la fenêtre (somme des variations absolues)
        total_movement = sum(abs(d) for d in diffs)
        # Définition des critères de turbulence basés sur les seuils heuristiques
        # Critère 1 : saut instantané grand
        large_jump = any(abs(d) >= 10 for d in diffs)
        # Critère 2 : au moins 2 inversions de direction (oscillation marquée) avec mouvement total > 12m
        multi_flip = (sign_changes >= 2 and total_movement > 12)
        # Critère 3 : 1 inversion de direction (une oscillation) mais avec mouvement total > 15m
        one_flip = (sign_changes == 1 and total_movement > 15)

        # Décision : turbulence détectée si l'un des critères est rempli
        if large_jump or multi_flip or one_flip:
            return True
        else:
            return False

    def distance_horizontale_km(self, coord1, coord2):
        """Calcule la distance horizontale entre deux points géographiques.

        Cette méthode utilise la formule de Haversine pour calculer la distance
        horizontale (ignorant l'altitude) entre deux points donnés sous la
        forme (latitude, longitude, altitude).

        :param coord1: Coordonnées du premier point (lat, lon, alt)
        :type coord1: tuple of float

        :param coord2: Coordonnées du second point (lat, lon, alt)
        :type coord2: tuple of float

        :return: Distance horizontale en kilomètres
        :rtype: float
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
        distance = R * c * 10000
        return distance

    def centre_turbulence(self, turb):
        """Calcule le centre estimé des turbulences détectées.

        Chaque événement de turbulence est représenté par un dictionnaire contenant
        un point de départ et un point de fin avec coordonnées (lat, lon, alt).
        Le centre est défini comme la moyenne des coordonnées de début et de fin.
        On ajoute également le diamètre horizontal (distance_km) et une confiance
        (fixée ici à 100).

        :param turb: Liste d'événements de turbulence renvoyés par `update()`.
            Chaque événement est un dictionnaire contenant les clés 'start', 'end' et 'distance_km'.
        :type turb: list of dict

        :return: Tableau numpy de forme (N, 5) contenant :
            latitude, longitude, altitude du centre, diamètre, niveau de confiance
        :rtype: numpy.ndarray
        """
        centres = []
        for evt in turb:  # evt est un dict 'start' / 'end'
            lat_c = (evt['start']['lat'] + evt['end']['lat']) / 2.0
            lon_c = (evt['start']['lon'] + evt['end']['lon']) / 2.0
            alt_c = (evt['start']['alt'] + evt['end']['alt']) / 2.0
            diam = evt['distance_km']
            confiance = 100
            centres.append((lat_c, lon_c, alt_c, diam, confiance))

        return np.asarray(centres, dtype=float)