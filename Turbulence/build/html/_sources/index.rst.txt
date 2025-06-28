.. ETS_en_Turbulence documentation master file, created by
   sphinx-quickstart on Fri Jun 27 15:20:42 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ETS_en_Turbulence documentation
===============================

Projet de session – MGA802 (ÉTS Montréal)
-----------------------------------------

**ETS_en_Turbulence** est une application Python qui :

* **suit en temps réel** la position des avions via l’API **OpenSky** ;
* **détecte automatiquement** les épisodes de turbulence grâce à un algorithme fondé sur
  les variations verticales d’altitude, la vitesse air, et la charge g ;
* **interroge l’API Open-Meteo** pour récupérer les champs météo (vents, cisaillement, CAPE)
  au point de turbulence ;
* **propage la cellule turbulente** (advection) selon le vent prévu afin d’anticiper
  son déplacement dans les minutes suivantes.

Architecture du dépôt
~~~~~~~~~~~~~~~~~~~~~

- ``requetes_opensky.py`` : wrapper minimal autour de l’API OpenSky
  (bbox, filtrage avion, parsing JSON)
- ``turbulence.py``     : logique de détection + seuils adaptatifs
- ``requetes_meteo.py``  : accès météo + interpolation spatiale
- ``modele_deplacement_turbulence.py`` : modèle d’advection/dispersion
- ``affichage_streamlit.py`` : dashboard temps réel (carte + log)
- ``main.py``       : orchestrateur multithread + boucle 3 s

Déploiement rapide
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # création d’un venv
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   # lancement du dashboard
   streamlit run affichage_streamlit.py

Contributeurs
~~~~~~~~~~~~~

- Arthur Aussedat-Pretet
- Victor Laloi
- Vladislav Liksutin

Licence
~~~~~~~

MIT — voir ``LICENSE``.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
