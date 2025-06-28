"""
main.py ― Orchestrateur temps réel
==================================

Boucle de suivi et de prévision des turbulences pour le projet
**ETS_en_Turbulence** (cours MGA802, ÉTS Montréal).

1. **Collecte** les états ADS-B via l’API OpenSky.
2. **Détecte** les turbulences avec :class:`turbulence.TurbulenceDetector`.
3. **Interroge** Open-Meteo pour connaître les vents locaux.
4. **Fait dériver** chaque cellule turbulente selon le vent (advection).
5. **Publie** un tableau NumPy thread-safe ``self.to_display`` consommé par
   l’interface Streamlit.
"""

import threading
import time

import numpy as np

from requetes_opensky import OpenSky
from turbulence import TurbulenceDetector
from requetes_meteo import OpenMeteo
from modele_deplacement_turbulence import deplacement_turbulence


class Main:
    """
    Orchestrateur temps réel du pipeline ADS-B → Turbulence → Météo.

    Paramètres
    ----------
    bbox : tuple[float, float, float, float] | None, optional
        *(min_lon, max_lon, min_lat, max_lat)*.
        ``None`` ⇒ requête monde entier (⚠︎ volumineux).

    Attributs
    ---------
    bbox : tuple | None
        Zone interrogeable passée au constructeur.
    detector : TurbulenceDetector
        Fenêtre glissante de 5 ticks pour la détection.
    turbulences_actives : numpy.ndarray
        Tableau *(N, 5)* `[lon, lat, alt, diam, timestamp]`.
    to_display : numpy.ndarray
        Copie protégée de ``turbulences_actives`` destinée au front-end.
    lock : threading.Lock
        Verrou garantissant l’accès thread-safe à ``to_display``.
    """

    def __init__(self, bbox = None):
        # Zone d'intéret
        self.bbox = bbox

        self.detector = TurbulenceDetector(window_size=5)

        # Colonnes : lon, lat, alt, diamètre, timestamp
        self.turbulences_actives: np.ndarray = np.empty((0, 5), dtype=float)

        self.to_display: np.ndarray = np.empty((0, 5), dtype=float)

        # Verrou pour accès thread-safe à ``to_display``
        self.lock = threading.Lock()

        # Démarrage de la boucle en tâche de fond
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        """
        Boucle principale exécutée en arrière-plan.

        Cette méthode tourne indéfiniment dans un thread *daemon* et enchaîne
        périodiquement les opérations suivantes :

        1. **Acquisition ADS-B** – interroge l’API *OpenSky* pour obtenir
           l’état instantané des aéronefs dans la *bounding box* ``self.bbox``.
        2. **Détection de turbulences** – transmet les nouveaux états
           au :class:`turbulence.TurbulenceDetector` qui renvoie les cellules
           turbulentes fraîchement identifiées.
        3. **Mise à jour des cellules existantes** – récupère la météo locale
           via :class:`requetes_meteo.OpenMeteo` puis fait dériver chacune des
           cellules déjà actives selon le vent
           (:func:`modele_deplacement_turbulence.deplacement_turbulence`).
        4. **Fusion** – empile les turbulences déplacées et les nouvelles pour
           obtenir l’état global ``self.turbulences_actives``.
        5. **Publication thread-safe** – copie atomiquement cet état dans
           ``self.to_display`` afin que l’interface Streamlit puisse l’afficher
           sans risque de condition de course.
        6. **Temporisation** – attend 3 s avant de reprendre le cycle.

        Les cellules turbulentes sont stockées dans des tableaux NumPy
        de forme *(N, 5)* avec les colonnes ::

            [longitude, latitude, altitude, diametre, timestamp]

        Parameters
        ----------
        None

        Returns
        -------
        None
            La fonction est bloquante : elle ne renvoie jamais de valeur et ne
            se termine qu’à l’arrêt du programme.

        Notes
        -----
        - **Cadence effective** ≈ 6 s : ~3 s de traitement + 3 s de pause.
        - L’accès au tableau publié (`self.to_display`) est protégé par
          un :class:`threading.Lock` (``self.lock``).
        - Les données météo et ADS-B sont externes ; prévois une gestion
          d’exception si l’une des API devient indisponible.

        See Also
        --------
        :class:`requetes_opensky.OpenSky`
        :class:`turbulence.TurbulenceDetector`
        :class:`requetes_meteo.OpenMeteo`
        :func:`modele_deplacement_turbulence.deplacement_turbulence`
        """
        while True:
            # 1) Acquisition ADS-B
            states = OpenSky().get_json(self.bbox)

            # 2) Détection de turbulences sur la fenêtre courante
            turbulences_recentes = self.detector.update(states)

            # 3) Fusion / initialisation
            if turbulences_recentes.size:
                if self.turbulences_actives.size:
                    meteo_old = OpenMeteo(self.turbulences_actives).resultats
                    turbulences_deplacees = deplacement_turbulence(
                        self.turbulences_actives, meteo_old
                    )

                    self.turbulences_actives = np.vstack(
                        (turbulences_deplacees, turbulences_recentes)
                    )
                else:
                    # Première détection du run
                    self.turbulences_actives = turbulences_recentes.copy()

                with self.lock:
                    self.to_display = self.turbulences_actives.copy()

            # 4) Pas de nouvelles turbulences mais des anciennes encore actives
            elif self.turbulences_actives.size:
                meteo_old = OpenMeteo(self.turbulences_actives).resultats
                turbulences_deplacees = deplacement_turbulence(
                    self.turbulences_actives, meteo_old
                )

                with self.lock:
                    self.to_display = turbulences_deplacees.copy()

            # 5) Pause puis advection globale avant la prochaine itération
            time.sleep(3)

            if self.turbulences_actives.size:
                meteo_new = OpenMeteo(self.turbulences_actives).resultats
                turbulences_deplacees = deplacement_turbulence(
                    self.turbulences_actives, meteo_new
                )

                with self.lock:
                    self.to_display = turbulences_deplacees.copy()

            # Deuxième pause pour conserver la cadence ~3 s par demi-cycle
            time.sleep(3)


