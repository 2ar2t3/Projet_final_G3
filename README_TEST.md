# ✅ Cas de test — Turbulence Map

## Objectif

Lors de ce test, nous avons simulé pendant environ 5 minutes, avec les positions géographiques des avions en temps réel et de meme pour la conditions météo.
Il verifie que le code complet fonctionne correctement.

## Contenu

- `affichage_streamlit.py` : script pour afficher la carte
- `affiche_carte.py` : script pour creer la carte
- `main.py` : script qui gere la collecte, le traitement et la mise a jour des données
- `modele_deplacement_turbulence.py` : script qui deplace les turbulence en fonction des conditions météo
- `requete_meteo.py` : script qui gere les données météo
- `requetes_OpenSky.py` : script qui gere  la récupération des données ADS-B en interagissant avec l’API OpenSky.
- `turbulence.py` : script qui contient la logique de détection, modélisation et traitement des zones de turbulences.

## Exécution

Lancer le test depuis le terminal :
 cd Tubulence
Et ensuite :
 streamlit run affichage_streamlit.py

 ## Résultat

Une page Streamlit s'ouvre et affiche les zones de turbulences comme on peux le voir sur l'image :
![image](https://github.com/user-attachments/assets/2483eb34-b677-427e-8153-19ee1f579804)

 
