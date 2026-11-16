
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Dashboard DMAIC - Stellantis", layout="wide")
st.title("🏭 Pilotage & Équilibrage Ligne d'Usinage (Démarche DMAIC)")
st.markdown("**Site PSA Valenciennes** — Ligne automatisée de couronnes de pont")

# --- BARRE LATÉRALE : SIMULATION WHAT-IF (AMÉLIORER) ---
st.sidebar.header("🎛️ Simulation des Améliorations")
gain_lavage = st.sidebar.slider("Gain cycle Lavage (min)", 0.0, 4.0, 0.0, 0.5)
gain_pannes = st.sidebar.slider("Réduction pannes imprévues (min)", 0, 45, 0, 5)
gain_micro = st.sidebar.slider("Réduction micro-arrêts (min)", 0, 30, 0, 5)
rebuts_simules = st.sidebar.slider("Pièces non conformes / jour", 0, 3, 3, 1)

# --- CALCULS DYNAMIQUES ---
temps_net = 1290 + gain_pannes + gain_micro
takt_time = temps_net / 100

df_postes = pd.DataFrame({
    "Ordre": [1, 2, 3, 4, 5],
    "Poste": ["Rectifieuse", "Ébauche", "Finition", "Machine à laver", "Contrôle"],
    "Cycle_min": [13.0, 11.0, 12.0, 14.0 - gain_lavage, 9.0]
})

cycle_goulot = df_postes["Cycle_min"].max()
capacite_max = temps_net / cycle_goulot
# Si aucune simulation n'est activée, on affiche les 88 pièces réelles observées
pieces_produites = 88.0 if (gain_lavage == 0 and gain_pannes == 0 and gain_micro == 0) else capacite_max
pieces_conformes = max(0.0, pieces_produites - rebuts_simules)

dispo = temps_net / 1380
perf = min(1.0, pieces_produites / capacite_max)
qualite = pieces_conformes / pieces_produites if pieces_produites > 0 else 0
trs = dispo * perf * qualite

# --- BANDEAU DES KPI ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Pièces Conformes / j", f"{pieces_conformes:.1f} pcs", f"{pieces_conformes - 100:.1f} vs Objectif")
col2.metric("TRS Global", f"{trs*100:.1f} %")
col3.metric("Disponibilité", f"{dispo*100:.1f} %")
col4.metric("Takt Time Cible", f"{takt_time:.2f} min")
col5.metric("Cycle Goulot", f"{cycle_goulot:.1f} min", f"{cycle_goulot - takt_time:+.2f} min vs Takt", delta_color="inverse")

st.divider()

# --- GRAPHIQUES LIGNE 1 : YAMAZUMI & CASCADE DES TEMPS ---
g1, g2 = st.columns(2)

with g1:
    st.subheader("📊 Équilibrage des Postes (Yamazumi vs Takt Time)")
    couleurs = ["#EF553B" if c > takt_time else "#00CC96" for c in df_postes["Cycle_min"]]
    fig_yamazumi = go.Figure(data=[
        go.Bar(x=df_postes["Poste"], y=df_postes["Cycle_min"], marker_color=couleurs, text=df_postes["Cycle_min"], textposition="auto")
    ])
    fig_yamazumi.add_hline(y=takt_time, line_dash="dash", line_color="black", annotation_text=f"Takt Time ({takt_time:.2f} min)")
    fig_yamazumi.update_layout(yaxis_title="Temps de cycle (min/pièce)", showlegend=False, height=380)
    st.plotly_chart(fig_yamazumi, use_container_width=True)

with g2:
    st.subheader("⏱️ Décomposition des Temps Journaliers (1 440 min)")
    fig_waterfall = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "total"],
        x=["Théorique (24h)", "Préventif", "Pannes", "Micro-arrêts", "Réglages", "Temps Net"],
        y=[1440, -60, -(45 - gain_pannes), -(30 - gain_micro), -15, 0],
        text=[1440, -60, -(45 - gain_pannes), -(30 - gain_micro), -15, temps_net],
        textposition="outside"
    ))
    fig_waterfall.update_layout(yaxis_title="Minutes / jour", height=380)
    st.plotly_chart(fig_waterfall, use_container_width=True)

# --- GRAPHIQUES LIGNE 2 : MÉTHODE DES CHAÎNONS (FLUX) ---
st.subheader("📐 Implantation & Méthode des Chaînons (Plan A vs Plan B optimisé)")
df_flux = pd.DataFrame({
    "Trajet": [
        "1. Magasin → Rectifieuse",
        "2. Rectifieuse → Ébauche",
        "3. Ébauche → Finition",
        "4. Finition → Lavage",
        "5. Lavage → Contrôle"
    ],
    "Plan A (Actuel : 150 m)": [25, 45, 38, 22, 20],
    "Plan B (Cible : 48 m)": [10, 10, 10, 10, 8]
})
df_flux_melt = df_flux.melt(id_vars="Trajet", var_name="Scénario", value_name="Distance (m)")
fig_flux = px.bar(df_flux_melt, x="Distance (m)", y="Trajet", color="Scénario", barmode="group", orientation="h",
                  color_discrete_sequence=["#636EFA", "#00CC96"], height=320)
st.plotly_chart(fig_flux, use_container_width=True)
