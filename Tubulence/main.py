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

    def start_timer(self):
        """Fonction timer qui appelle recup_donnees 6s après son appel"""
        self.timer = threading.Timer(6, self.recup_donnees)
        #Le timer est relancé
        self.timer.start()

    def recup_donnees(self):
        """Fonction qui appelle un objet OpenSky() contenant le state array brut"""

        #States est un dataframe contenant les informations relatives aux avions
        states = OpenSky().get_json(self.bbox)

        #Events est un dataframe contenant les informations relatives aux turbulences
        turbulences = self.detector.update(states)

        # if turbulences.size:  # seulement si le tableau n'est pas vide
        #      # Météo est un numpy array contenant la vitesse, direction et cisaillement
        #      # du vent aux coordonées des turbulences
        #      meteo = OpenMeteo(turbulences).resultats

        self.start_timer()  #On relance le timer dès que la requête est parvenue

main = Main()
