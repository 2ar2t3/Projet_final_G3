import requests
import pandas as pd


class OpenSky:

    #Définition de variable de classes
    identifiant = "2ar2t-api-client"
    mdp = "46k6mXbu7YekAdU7uI7UcKfXQfcrOWre"

    url_token = ("https://auth.opensky-network.org/auth/"
           "realms/opensky-network/protocol/openid-connect/token")
    url_json = "https://opensky-network.org/api/states/all"


    def get_token(self):
        """Fonction qui récupère et retourne le token temporaire"""
        resp = requests.post(
            self.url_token, #On demande au serveur un token temporaire
            data={
                "grant_type": "client_credentials",
                "client_id": self.identifiant, #On y indique notre id
                "client_secret": self.mdp},    #Et notre mdp
            timeout=15,
        )
        return resp.json()["access_token"]


    def conversion_df(self, doc):
        """
        Construit un DataFrame à partir d’une liste de listes OpenSky.

        Garde les indices 0, 5, 6, 7, 11
        · Ignore l’avion si states[i][8] == True      (au sol)
        · Si states[i][7] est 0 ou None, utilise states[i][13] pour l’altitude

        Returns
        -------
        pd.DataFrame  colonnes = ['nom', 'longitude', 'latitude', 'altitude', 'vertical_rate']
        """
        colonnes = ['nom', 'longitude', 'latitude', 'altitude', 'vertical_rate']
        lignes = []

        for avion in doc:
            #On retourne l'altitude géo si la barométrique n'est pas disponible
            altitude = avion[7] if avion[7] not in (None, 0) else avion[13]
            #On n'ajoute que les colonnes souhaitées
            lignes.append([avion[0], avion[5], avion[6], altitude, avion[11]])

        return pd.DataFrame(lignes, columns=colonnes)

    def get_json(self, bbox = None):
        """Fonction qui retourne le state array complet sous format json"""
        #Si aucune zone n'est précisée on récupère la carte mondiale
        if not bbox:
            bbox = {}

        token = self.get_token()
        #On inclue notre token dans le header de la requête
        headers = {"Authorization": f"Bearer {token}"}

        #La requête inclue la zone de recherche et le token
        r = requests.get(self.url_json, headers=headers,
                         params=bbox, timeout=15)

        return self.conversion_df(r.json()["states"])




