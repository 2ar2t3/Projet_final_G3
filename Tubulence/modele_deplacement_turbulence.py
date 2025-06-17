import numpy as np

class TurbulenceSimulator:
    def __init__(self, positions_init):
        """
        :param positions_init: numpy array shape (n, 3) avec colonnes [lon, lat, alt]
                               représente la position initiale (ou positions déjà connues)
        """
        self.positions = positions_init.tolist()  # liste modifiable

    def calculer_vitesse_effective(self, vitesse_vent, direction_vent, cisaillement_haut, cisaillement_bas):
        angle_rad = np.deg2rad(direction_vent)
        vx = vitesse_vent * np.sin(angle_rad)
        vy = vitesse_vent * np.cos(angle_rad)
        correction_h = 0.1 * (cisaillement_haut - cisaillement_bas)
        return np.array([vx, vy, correction_h])

    def mise_a_jour_position(self, v_eff, dt=6.0):
        lon, lat, alt = self.positions[-1]  # dernière position
        dx = v_eff[0] * dt
        dy = v_eff[1] * dt
        dz = v_eff[2] * dt

        delta_lat = dy / 111000
        delta_lon = dx / (111000 * np.cos(np.radians(lat)))

        nouvelle_pos = [lon + delta_lon, lat + delta_lat, alt + dz]
        self.positions.append(nouvelle_pos)

    def simuler(self, donnees_meteo, dt=6.0):
        """
        :param donnees_meteo: numpy array shape (m,4) colonnes [vitesse_vent, direction_vent, cisaillement_haut, cisaillement_bas]
        :param dt: durée d’un pas de temps (s)
        :return: numpy array shape (n+m, 3) positions actualisées
        """
        for ligne in donnees_meteo:
            v_vent, dir_vent, cis_haut, cis_bas = ligne
            v_eff = self.calculer_vitesse_effective(v_vent, dir_vent, cis_haut, cis_bas)
            self.mise_a_jour_position(v_eff, dt)

        return np.array(self.positions)

# test
positions_init = np.array([[2.0, 48.0, 100.0]])  # position de départ

donnees_meteo = np.array([
    [10, 270, 3, 1],
    [12, 280, 2, 1.5],
    [8,  260, 3.5, 2],
])

sim = TurbulenceSimulator(positions_init)
positions_finales = sim.simuler(donnees_meteo, dt=1.0)

print(positions_finales)