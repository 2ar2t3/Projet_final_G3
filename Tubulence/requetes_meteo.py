import requests
import numpy as np

class OpenMeteo:

    url = "https://api.open-meteo.com/v1/forecast"
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
    def  conversion_altitude_en_hpa(arr_ft):
        """
        Copie le tableau `(lat, lon, altitude_ft)` et remplace la 3ᵉ colonne
        par la pression standard (hPa) selon l’atmosphère ISA.

        Paramètres
        ----------
        arr_ft : ndarray (N, 3)
            Colonne 0 : latitude
            Colonne 1 : longitude
            Colonne 2 : altitude en pieds

        Retour
        ------
        ndarray (N, 3)
            Copie du tableau, mais la colonne 2 contient la pression en hPa.
        """
        out = arr_ft.copy()  # ne modifie pas l’original
        z_m = out[:, 2] * 0.3048  # pieds → mètres
        p0, L, T0, gM_RL = 1013.25, 0.0065, 288.15, 5.255877
        out[:, 2] = p0 * (1 - L * z_m / T0) ** gM_RL
        return out



    def niveau_proche(self, hpa):
        """Renvoie le niveau (hPa) le plus proche parmi ceux acceptés par l’API."""
        return self.niveaux_possibles[np.abs(self.niveaux_possibles - hpa).argmin()]

    def donnees_vent(self, array_hpa):
        """
        Entrée
        ------
        turb_array : ndarray (N, 3)
            Colonne 0 → latitude
            Colonne 1 → longitude
            Colonne 2 → niveau-pression en hPa

        Sortie
        ------
        ndarray (N, 2)
            Colonne 0 → vitesse du vent (m/s)
            Colonne 1 → direction du vent (°)
        """
        n = array_hpa.shape[0]
        result = np.empty((n, 2), dtype=float)

        for i, (lat, lon, niv) in enumerate(array_hpa):
            niveau = self.niveau_proche(niv)
            suffixe = f"{int(niveau)}hPa"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": f"wind_speed_{suffixe},wind_direction_{suffixe}",
                "timezone": "UTC",
            }
            hourly = requests.get(self.url, params=params, timeout=10).json()["hourly"]
            result[i, 0] = hourly[f"wind_speed_{suffixe}"][0]  # vitesse
            result[i, 1] = hourly[f"wind_direction_{suffixe}"][0]  # direction

        return result


points_ft = np.array([
    [46.50, 7.00, 35000],
    [47.10, 8.25, 30000],
    [45.80, 6.80, 26000],
], dtype=float)

test = OpenMeteo(points_ft).resultats
print(test)