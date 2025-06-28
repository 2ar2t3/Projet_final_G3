import numpy as np

# Rajouter dans le numpy array de turbulence la confiance a 100

def deplacement_turbulence(turbulence_data, meteo_data, delta_t=60):
    """
        Simule le déplacement et l'évolution des zones de turbulence sous l'effet du vent et du cisaillement.

        Cette fonction prend en entrée des données représentant des zones de turbulence, ainsi que des
        données météorologiques correspondantes. Elle calcule le nouveau positionnement de chaque zone
        en tenant compte du déplacement dû au vent (direction et vitesse), du cisaillement vertical
        de l'air (modifiant l'altitude et le diamètre), et d'une décroissance de la confiance associée.
        Les zones dont la confiance devient trop faible sont ignorées dans le résultat final.


        :param turbulence_data: Un tableau contenant les zones de turbulence à simuler. Chaque ligne doit contenir :
            ``latitude``, ``longitude``, ``altitude``, ``diamètre``, ``confiance``.
        :type turbulence_data: numpy.ndarray

        :param meteo_data: Un tableau contenant les données météorologiques associées à chaque zone.
            Chaque ligne doit contenir : ``vitesse du vent (m/s)``, ``direction (degrés)``,
            ``cisaillement haut``, ``cisaillement bas``.
        :type meteo_data: numpy.ndarray

        :param delta_t: Durée du pas de temps en secondes pour le calcul du déplacement. Par défaut : 60.
        :type delta_t: float

        :return: Un tableau numpy contenant les nouvelles zones de turbulence conservées,
            avec leurs nouvelles positions, altitudes, diamètres et niveaux de confiance.
        :rtype: numpy.ndarray
        """
    # Constantes pour conversion approximative
    METERS_PER_DEG_LAT = 111_000
    METERS_PER_DEG_LON = 85_000  # à adapter selon latitude pour plus de précision

    new_data = []

    for i in range(turbulence_data.shape[0]):
        lat, lon, alt, diam, conf = turbulence_data[i]
        vitesse, direction_deg, cis_haut, cis_bas = meteo_data[i]

        # Déplacement horizontal causé par le vent
        direction_rad = np.deg2rad(direction_deg)
        dx = vitesse * delta_t * np.cos(direction_rad)  # en mètres
        dy = vitesse * delta_t * np.sin(direction_rad)

        # Conversion en degrés
        dlon = dx / METERS_PER_DEG_LON
        dlat = dy / METERS_PER_DEG_LAT

        # Modification de l'altitude basée sur le cisaillement (simplifiée)
        delta_alt = (cis_haut - cis_bas) * 0.1  # facteur arbitraire à calibrer

        # Expansion ou contraction du diamètre
        delta_diam = (abs(cis_haut) + abs(cis_bas)) * 0.01  # facteur arbitraire

        nouvelle_confiance = conf*0.95

        if nouvelle_confiance <= 0.2:
            continue

        new_data.append([
            lat + dlat,
            lon + dlon,
            alt + delta_alt,
            max(diam + delta_diam, 0),  # éviter diamètre négatif
            nouvelle_confiance,
        ])


    return np.array(new_data)


