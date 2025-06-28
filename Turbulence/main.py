import threading, time, numpy as np

from requetes_opensky import OpenSky
from turbulence       import TurbulenceDetector
from requetes_meteo   import OpenMeteo
# from mon_module_ui   import affichage
from modele_deplacement_turbulence import deplacement_turbulence

# streamlit run affichage_streamlit.py

class Main:
    """Collecte ADS-B, cumule les turbulences, déclenche l’affichage."""
    def __init__(self, bbox=None):
        self.bbox = bbox
        self.detector = TurbulenceDetector(window_size=5)

        # lon, lat, alt, diametre  (historique complet)
        self.turbulences_actives = np.empty((0, 5), float)
        self.to_display = np.empty((0, 5), float)

        self.lock = threading.Lock()

        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        """
        Boucle principale exécutée en arrière-plan, combinant acquisition de données, détection de turbulences,
        ajustement météorologique et mise à jour de l’affichage.

        Cette méthode tourne en continu (bloquante) :
        - Récupère les données d'avions via l'API OpenSky dans une zone définie (`self.bbox`)
        - Met à jour la détection de turbulences avec les nouveaux états reçus
        - Si de nouvelles turbulences sont détectées, elles sont fusionnées avec les précédentes
          après ajustement par la météo
        - Met à jour la variable `self.to_display` pour un affichage thread-safe
        - Applique un décalage météorologique régulier à toutes les turbulences détectées
        - Fait une pause de 3 secondes entre chaque cycle de traitement

        :note: Cette fonction doit être exécutée dans un thread séparé car elle ne se termine jamais.
        """
        while True:
            # Récupération des données d'états d'avions dans la zone bbox
            states = OpenSky().get_json(self.bbox)

            # Détection des turbulences récentes à partir des états récupérés
            turbulences_recentes = self.detector.update(states)

            if turbulences_recentes.size:
                if self.turbulences_actives.size:
                    # Récupération des données météo pour les anciennes turbulences
                    meteo_old = OpenMeteo(self.turbulences_actives).resultats

                    # Déplacement des anciennes turbulences en fonction des vents
                    turbulences_deplacees = deplacement_turbulence(self.turbulences_actives, meteo_old)

                    # Fusion des anciennes turbulences déplacées avec les nouvelles détectées
                    self.turbulences_actives = np.vstack((turbulences_deplacees, turbulences_recentes))

                    # Mise à jour thread-safe de la variable à afficher (copie complète)
                    with self.lock:
                        self.to_display = self.turbulences_actives.copy()
                else:
                    # Si aucune turbulence active : on initialise avec les récentes
                    self.turbulences_actives = turbulences_recentes.copy()

                    # Mise à jour affichage (sans données météo)
                    with self.lock:
                        self.to_display = self.turbulences_actives.copy()

            # Si plus de nouvelles turbulences, mais toujours des actives en mémoire
            if self.turbulences_actives.size and not turbulences_recentes.size:
                # Mise à jour météo des anciennes turbulences
                meteo_old = OpenMeteo(self.turbulences_actives).resultats
                turbulences_deplacees = deplacement_turbulence(self.turbulences_actives, meteo_old)

                # Mise à jour affichage uniquement avec les turbulences précédentes ajustées
                with self.lock:
                    self.to_display = turbulences_deplacees.copy()

            # Pause de 3 secondes avant prochain traitement
            time.sleep(3)

            # Nouveau déplacement des turbulences avec la météo mise à jour
            meteo_new = OpenMeteo(self.turbulences_actives).resultats
            turbulences_deplacees = deplacement_turbulence(self.turbulences_actives, meteo_new)

            # Mise à jour affichage après déplacement météo global
            with self.lock:
                self.to_display = turbulences_deplacees.copy()

            # Nouvelle pause de 3 secondes
            time.sleep(3)


