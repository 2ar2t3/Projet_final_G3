import threading, time, numpy as np

from Requetes_OpenSky import OpenSky
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
        self.turbulences_actives = np.empty((0, 4), float)
        self.to_display = np.empty((0, 4), float)

        self.lock = threading.Lock()

        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        """Tourne en tâche de fond : collecte + affichage + pause 3 s."""
        while True:
            states = OpenSky().get_json(self.bbox)
            turbulences_recentes = self.detector.update(states)

            if turbulences_recentes.size:
                if self.turbulences_actives.size:
                    meteo_old = OpenMeteo(self.turbulences_actives).resultats

                    #On déplace les anciennes turbulences
                    turbulences_deplacees = deplacement_turbulence(self.turbulences_actives, meteo_old)

                    #On ajoute toutes les turbulences ensembles
                    self.turbulences_actives = np.vstack(
                        (turbulences_deplacees, turbulences_recentes))

                    "affichage toutes avec météo pour anciennes"
                    with self.lock:
                        self.to_display = self.turbulences_actives.copy()

                else:
                    self.turbulences_actives = turbulences_recentes.copy()
                    "affichage recentes sans météo"
                    with self.lock:
                        self.to_display = self.turbulences_actives.copy()

            if self.turbulences_actives.size and not turbulences_recentes.size:
                meteo_old = OpenMeteo(self.turbulences_actives).resultats
                #On déplace les anciennes
                turbulences_deplacees = deplacement_turbulence(self.turbulences_actives, meteo_old)

                with self.lock:
                    self.to_display = turbulences_deplacees.copy()
                "affichage anciennes avec météo pour anciennes"

            time.sleep(3)



            meteo_new = OpenMeteo(self.turbulences_actives).resultats
            turbulences_deplacees = deplacement_turbulence(self.turbulences_actives, meteo_new)

            "affichage toutes avec météo pour toutes"
            with self.lock:
                self.to_display = turbulences_deplacees.copy()

            time.sleep(3)


