import threading

from Requetes_OpenSky import *
from turbulence import *

class Main:
    """Classe Principale"""
    def __init__(self, bbox = None):
        """On initialise et on lance un timer à l'appel de la classe"""
        self.timer = None
        self.bbox = bbox if bbox else {}
        self.turbulence_detector = Turbulence()  # ← Keep a persistent instance
        self.start_timer()

    def start_timer(self):
        """Fonction timer qui appelle recup_donnees 6s après son appel"""
        self.timer = threading.Timer(6, self.recup_donnees)
        #Le timer est relancé
        self.timer.start()

    def recup_donnees(self):
        """Fonction qui appelle un objet OpenSky() contenant le state array brut"""

        #States est un dataframe
        states = OpenSky().get_json(self.bbox)
        turbulences = self.turbulence_detector.get_turbulences(states)


        self.start_timer()  #On relance le timer dès que la requête est parvenue



main = Main()
