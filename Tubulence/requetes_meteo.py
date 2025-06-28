import requests
import numpy as np

class OpenMeteo:

    #base de l'url de l'api d'open-meteo
    url = "https://api.open-meteo.com/v1/forecast"
    #Liste des niveaus de pression disponibles sur l'api
    niveaux_possibles = np.array(
        [1000, 975, 950, 925, 900, 850, 800, 700, 600,
         500, 400, 300, 250,200, 150, 100, 70, 50, 30])

    def __init__(self, array):
        """
        `array` : ndarray (N, 3) – lat, lon, alt [ft]

        À l'instanciation :
        1) conversion pieds → hPa
        2) requêtes API
        3) stockage des résultats dans `self.resultats` (ndarray (N, 2))
        """
        self.resultats = (
            self.donnees_vent(self.conversion_altitude_en_hpa(array)))

    @staticmethod
    def conversion_altitude_en_hpa(arr_ft):
        """
        Convertit un tableau de coordonnées (latitude, longitude, altitude en pieds)
        en un tableau identique dont l'altitude est remplacée par une estimation de la
        pression atmosphérique standard (en hPa), selon l’atmosphère standard ISA.

        Cette méthode applique la formule barométrique standard pour convertir
        une altitude géométrique en pression atmosphérique théorique :

            P = P0 * (1 - (L * h / T0)) ^ (g*M / (R*L))

        :param arr_ft: Un tableau numpy de forme (N, 3), où chaque ligne correspond à
            un point géographique. La troisième colonne représente l'altitude en pieds.
        :type arr_ft: numpy.ndarray

        :return: Une copie du tableau d’entrée de forme (N, 3), où la troisième colonne
            contient la pression atmosphérique estimée en hPa, calculée selon l’altitude.
        :rtype: numpy.ndarray
        """
        out = arr_ft.copy()  # ne modifie pas l’original
        z_m = out[:, 2] # mètres
        p0, L, T0, gM_RL = 1013.25, 0.0065, 288.15, 5.255877
        out[:, 2] = p0 * (1 - L * z_m / T0) ** gM_RL
        return out



    def niveau_proche(self, hpa):
        """Renvoie le niveau (hPa) le plus proche parmi ceux acceptés par l’API."""
        return self.niveaux_possibles[np.abs(self.niveaux_possibles - hpa).argmin()]

    def donnees_vent(self, array_hpa):
        """Récupère les données de vent pour un tableau de turbulences actives,
        basé sur leur position géographique et leur niveau de pression en hPa.

        Pour chaque point, cette méthode interroge l’API météo afin de récupérer :
        - la vitesse du vent (m/s)
        - la direction du vent (°)
        - le cisaillement vertical au-dessus et en dessous du point

        :param array_hpa: Tableau des turbulences actives de forme (N, 5).
            Chaque ligne représente une turbulence sous la forme :
            [latitude, longitude, pression_hPa, diamètre, confiance].
            Seules les 3 premières colonnes sont utilisées ici.
        :type array_hpa: numpy.ndarray

        :return: Tableau de forme (N, 4) contenant pour chaque turbulence :
            - vitesse du vent (m/s)
            - direction du vent (degrés)
            - cisaillement vertical au-dessus (m/s)
            - cisaillement vertical en dessous (m/s)
        :rtype: numpy.ndarray
        """
        # Création d'un array pour stocker les résultats
        n = len(array_hpa)
        result = np.empty((n, 4), dtype=float)

        # Itèration sur chaque turbulence active
        for turb, (lat, lon, niv, _, _) in enumerate(array_hpa):

            # Normalisation du niveau souhaité au plus proche disponible`
            niveau = int(self.niveau_proche(niv))

            # Récupération des niveaux supérieurs et inférieurs
            indice_niveau = np.where(self.niveaux_possibles == niveau)[0][0]
            niveau_plus = int(self.niveaux_possibles[indice_niveau+1])
            niveau_moins = int(self.niveaux_possibles[indice_niveau-1])

            niveaux_a_demander = (
                f"wind_speed_{niveau_moins}hPa",
                f"wind_speed_{niveau}hPa",
                f"wind_speed_{niveau_plus}hPa,"
                f"wind_direction_{niveau}hPa")

            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": ",".join(niveaux_a_demander),
                "timezone": "UTC",
            }
            #On récupère le résultat de la requête à l'api
            hourly = requests.get(self.url, params=params, timeout=10).json()["hourly"]

            #Vitesse et direction du vent
            result[turb, 0] = hourly[f"wind_speed_{niveau}hPa"][0]  # vitesse
            result[turb, 1] = hourly[f"wind_direction_{niveau}hPa"][0]  # direction

            #Cisaillement verticaux
            result[turb, 2] = (hourly[f"wind_speed_{niveau_plus}hPa"][0] -
                               result[turb, 0])
            result[turb, 3] = (result[turb, 0] -
                               hourly[f"wind_speed_{niveau_moins}hPa"][0])

        return result
