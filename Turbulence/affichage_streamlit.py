import streamlit as st
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt
import numpy as np

from main            import Main           # ta classe avec le thread
from affiche_carte   import Data, Carte    # tes classes d’affichage

st.set_page_config(layout="wide")

# ────────────────────────────────────────────────
# 1. Instance unique du collecteur
# ────────────────────────────────────────────────
if "app" not in st.session_state:
    st.session_state.app = Main()          # lance le thread daemon

app = st.session_state.app                 # raccourci

# ────────────────────────────────────────────────
# 2. Récupère les points à afficher
# ────────────────────────────────────────────────
with app.lock:
    points = app.to_display.copy()                    # ndarray (N,4) lon, lat, alt, diam

st.header("🌪️  Carte des turbulences (auto-refresh 3 s)")

if points.size:
    # points est déjà au bon format pour Data :
    #   colonne 0 : lon   | colonne 1 : lat | 2 : alt | 3 : diam
    Carte(Data(points)).affichage()
    st.markdown("### 🧭 Légende de la carte")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("**Couleurs**")
        st.markdown("- 🟥 **Rouge** : turbulence originale (confiance 100%)")
        st.markdown("- 🟦 **Bleu** : turbulence prédite (confiance < 100%)")

        st.markdown("**Taille**")
        st.markdown("- Proportionnelle au **diamètre estimé** de la turbulence")

        st.markdown("**Opacité**")
        st.markdown("- Dépend du **niveau de confiance** (de 0% à 100%)")

    with col2:
        fig, ax = plt.subplots(figsize=(7, 1.5))
        ax.set_xlim(0, 8)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # Exemples de turbulences bleues à différents niveaux de confiance
        niveaux = [0 ,10, 30, 50, 70, 90, 100]
        couleurs = [[0, 0, 1, conf / 100] for conf in niveaux]
        tailles = [300 + conf * 2 for conf in niveaux]

        for i, (taille, color, conf) in enumerate(zip(tailles, couleurs, niveaux)):
            ax.scatter(i + 1, 0.5, s=taille, color=color)
            ax.text(i + 1, 0.1, f"{conf}%", ha='center', fontsize=8)

        st.pyplot(fig)

else:
    st.info("Aucune turbulence pour l’instant.")

# ────────────────────────────────────────────────
# 3. Auto-rafraîchissement toutes les 3 s
# ────────────────────────────────────────────────
st_autorefresh(interval=3000, key="refresh")