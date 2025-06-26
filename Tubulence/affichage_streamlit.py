import streamlit as st
from streamlit_autorefresh import st_autorefresh
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
else:
    st.info("Aucune turbulence pour l’instant.")

# ────────────────────────────────────────────────
# 3. Auto-rafraîchissement toutes les 3 s
# ────────────────────────────────────────────────
st_autorefresh(interval=3000, key="refresh")