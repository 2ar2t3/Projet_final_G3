import threading

from Requetes_OpenSky import *
from turbulence import *
from requetes_meteo import *

class Main:
    """Classe Principale"""
    def __init__(self, bbox = None):
        """On initialise et on lance un timer à l'appel de la classe"""
        self.timer = None
        self.bbox = bbox if bbox else {}
        self.start_timer()
        self.detector = TurbulenceDetector(window_size=5)
        self.turbulences_actives = np.empty((0, 3), dtype=float)

    def start_timer(self):
        """Fonction timer qui appelle recup_donnees 6s après son appel"""
        self.timer = threading.Timer(6, self.recup_donnees)
        #Le timer est relancé
        self.timer.start()

    def recup_donnees(self):
        """Fonction qui appelle un objet OpenSky() contenant le state array brut"""

        #States est un dataframe contenant les informations relatives aux avions
        states = OpenSky().get_json(self.bbox)

        turbulences_recentes = self.detector.update(states)

        if turbulences_recentes.size:  # seulement si le tableau n'est pas vide
            if self.turbulences_actives.size:  # déjà des actives ?
                self.turbulences_actives = np.vstack(
                    (self.turbulences_actives, turbulences_recentes)
                )
            else:  # aucune active encore
                self.turbulences_actives = turbulences_recentes.copy()

        if self.turbulences_actives.size:
            meteo = OpenMeteo(self.turbulences_actives).resultats

        self.start_timer()  #On relance le timer dès que la requête est parvenue

main = Main()
