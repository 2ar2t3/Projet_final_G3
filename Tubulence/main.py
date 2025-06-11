import threading
from Requetes_OpenSky import *

class Main:
    """Classe Principale"""
    def __init__(self):
        """On initialise et on lance un timer à l'appel de la classe"""
        self.timer = None
        self.start_timer()

    def start_timer(self):
        """Fonction timer qui appelle recup_donnees 6s après son appel"""
        self.timer = threading.Timer(6, self.recup_donnees)
        #Le timer est relancé
        self.timer.start()

    def recup_donnees(self, data_count, num_avions):
        """Fonction qui appelle un objet OpenSky() contenant le state array brut
        Ajoute une fonctionallite qui retourne un nombre d'appels au API egal a data_count
        Ajoute une fonctionallite qui filtre le nombre de lignes egal a num_avions
        """

        """ -------------------------- a completer ----------------------------
        if data_count == 0:
            # retoune nombre infini/live

        else:
            # retourne data_count nombre d'appels au API
        ------------------------------------------------------------------------
        """


        state = OpenSky().get_json()["states"]
        self.start_timer()  #On relance le timer dès que la requête est parvenue
        print(state[0])
        return state[0]

main = Main()
main.recup_donnees()