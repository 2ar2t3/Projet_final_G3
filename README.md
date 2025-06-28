# ETS_en_Turbulence

> Suivi et prévision **temps réel** de la turbulence aérienne  
> Projet de session – **MGA802** (Maîtrise en génie aérospatial, ÉTS Montréal)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](#prérequis)  
[![Streamlit](https://img.shields.io/badge/streamlit-tableau-FF4B4B?logo=streamlit)](#🚀-démarrage-rapide)  
[![Licence](https://img.shields.io/badge/licence-MIT-green.svg)](#licence)

---

## ✈️ Concept

**ETS_en_Turbulence** :

Ce projet, réalisé dans le cadre du cours MGA802 de l'École de Technologie Supérieure de Montréal, à pour objectif de détecter la position des turbulences mondiales en temps réel. 


1. Interroge en continu l’API **OpenSky** pour récupérer les états ADS-B des avions mondiaux ;
2. Détecte leurs potentielles instabilités, indiquant la présence d'une turbulence ;
3. Récupère les vents locaux via **Open-Meteo** pour chaque position de turbulences ;
4. Applique un algorithme de déplacement de turbulence en temps réel
5. Diffuse les résultats dans un tableau de bord **Streamlit** (rafraîchi toutes les 3 s).

<img src="docs/exemple_carte_streamlit.png" alt="Capture d’écran Streamlit" width="800">

---

## Fonctionnalités principales

| Module | Rôle | Classe / fonction clé |
|--------|------|-----------------------|
| `main.py` | Boucle orchestratrise  | `Main` |
| `turbulence.py` | Détecteur de turbulences | `TurbulenceDetector` |
| `requetes_opensky.py` | Recupération données avions | `OpenSky` |
| `requetes_meteo.py` | Vents & cisaillement | `OpenMeteo` |
| `modele_deplacement_turbulence.py` | Modèle d’advection de turbulenes | `deplacement_turbulence` |
| `affiche_carte.py` | Module d'affichage 1 | `Data`, `Carte` |
| `app_dashboard.py` | Module d'affichage 2 | – |

---

## Prérequis

| Outil / service | Détail | Clé API |
|-----------------|--------|---------|
| **Python ≥ 3.10** | Virtualenv recommandé | – |
| **OpenSky** | 100 req/jour (anonyme) · 6 req/min (auth) | Facultatif : `OPENSKY_USER`, `OPENSKY_PASS` |
| **Open-Meteo** | Gratuit, illimité | Aucune |

L'API gratuite OpenSky offre un nombre de crédits d'appels limité pour les utilisateurs anonmyes (10 minutes d'utilisation, par IP, par jour). Afin d'augmenter cette limite et de passer à plus d'une heure par jour, il suffit de se créer un compte sur *https://opensky-network.org/data/api* et d'entrer son 'identifiant' et son "mot de passe' dans le module `requete_opensky.py`
```bash
    #Définition de variable de classes
    identifiant = "2ar2t-api-client"
    mdp = "46k6mXbu7YekAdU7uI7UcKfXQfcrOWre"
```
Un compte initial peut être utilisé, mais le nombre de crédit disponibles est incertain et dépend de l'utilisation générale du compte. 
Il est donc recommandé de se créer un compte pour une utilisation journalière. 
---

## Installation

```bash
git clone https://github.com/<utilisateur>/ETS_en_Turbulence.git
cd ETS_en_Turbulence

python -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate

pip install -r requirements.txt
