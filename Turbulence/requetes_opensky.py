import requests
import pandas as pd


class OpenSky:
    """
    Interface pour interagir avec l’API OpenSky Network :\n
    - Authentification via token temporaire (OAuth2)
    - Récupération des données d'états d'avions (position, altitude, etc.)
    - Transformation des résultats JSON en DataFrame filtré

    Variables de classe
    -------------------
    identifiant : str
        Identifiant client pour l’API OpenSky (OAuth2).
    mdp : str
        Mot de passe client correspondant à l’identifiant.
    url_token : str
        URL d’authentification pour récupérer un token.
    url_json : str
        URL d’accès aux données d’états (positions d’avions).
    """

    #Définition de variable de classes
    identifiant = "2ar2t-api-client"
    mdp = "46k6mXbu7YekAdU7uI7UcKfXQfcrOWre"

    url_token = ("https://auth.opensky-network.org/auth/"
           "realms/opensky-network/protocol/openid-connect/token")
    url_json = "https://opensky-network.org/api/states/all"


    def get_token(self):
        """
        Récupère un token temporaire via OAuth2 pour interroger l’API OpenSky.

        :return: Jeton d’accès temporaire (valable quelques secondes).
        :rtype: str
        """
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
        Convertit une liste brute d’états d’avions en DataFrame exploitable.

        Pour chaque avion :\n
        - Utilise les champs [0, 5, 6, 7, 11] (nom, longitude, latitude, altitude, taux vertical)
        - Si altitude barométrique (index 7) est absente, utilise l’altitude géométrique (index 13)
        - Supprime les lignes incomplètes ou contenant des valeurs `None`
        - Ignore les avions au sol (index 8), mais ce filtre peut être ajouté ici si nécessaire

        :param doc: Données issues de `r.json()["states"]` (liste de listes)
        :type doc: list[list]

        :return: DataFrame contenant uniquement les colonnes utiles à l’analyse.
        :rtype: pandas.DataFrame
        """
        colonnes = ['nom', 'longitude', 'latitude', 'altitude', 'vertical_rate']
        lignes = []

        for avion in doc:
            #On retourne l'altitude géo si la barométrique n'est pas disponible
            altitude = avion[7] if avion[7] not in (None, 0) else avion[13]
            #On n'ajoute que les colonnes souhaitées
            lignes.append([avion[0], avion[5], avion[6], altitude, avion[11]])

        return pd.DataFrame(lignes, columns=colonnes).dropna(how='any')

    def get_json(self, bbox = None):
        """
        Interroge l’API OpenSky pour récupérer les états d’avions dans une zone donnée.

        - Si `bbox` est vide, récupère les données mondiales
        - Utilise un token OAuth2 valide dans l’en-tête HTTP
        - Renvoie un DataFrame filtré via `conversion_df`

        :param bbox: Dictionnaire contenant les clés éventuelles :
            minLatitude, maxLatitude, minLongitude, maxLongitude
        :type bbox: dict, optional

        :return: Un DataFrame contenant les états filtrés des avions détectés.
        :rtype: pandas.DataFrame
        """
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




