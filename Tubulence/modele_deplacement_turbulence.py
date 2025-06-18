import numpy as np


def deplacement_turbulence(turbulence_data, meteo_data, delta_t=60):
    """
    Simule le déplacement de turbulences sur une période delta_t (en secondes).

    Paramètres :
    - turbulence_data : np.ndarray (n, 4) -> [latitude, longitude, altitude, diamètre]
    - meteo_data : np.ndarray (n, 4) -> [vitesse_vent (m/s), direction_vent (°), cisaillement_haut, cisaillement_bas]
    - delta_t : temps écoulé en secondes (par défaut 60s)

    Retourne :
    - np.ndarray (n, 4) avec les nouvelles positions
    """
    # Constantes pour conversion approximative
    METERS_PER_DEG_LAT = 111_000
    METERS_PER_DEG_LON = 85_000  # à adapter selon latitude pour plus de précision

    new_data = []

    for i in range(turbulence_data.shape[0]):
        lat, lon, alt, diam = turbulence_data[i]
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

        new_data.append([
            lat + dlat,
            lon + dlon,
            alt + delta_alt,
            max(diam + delta_diam, 0)  # éviter diamètre négatif
        ])

    return np.array(new_data)