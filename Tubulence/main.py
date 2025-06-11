import threading

from Requetes_OpenSky import *

class Main:
    """Classe Principale"""
    def __init__(self, bbox = None):
        """On initialise et on lance un timer à l'appel de la classe"""
        self.timer = None
        if not bbox:
            self.bbox = {}
        else:
            self.bbox = bbox
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
        self.start_timer()  #On relance le timer dès que la requête est parvenue

main = Main()