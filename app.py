import streamlit as st
import numpy as np
import pandas as pd
import monte_carlo_2
import importlib

importlib.reload(monte_carlo_2)
from monte_carlo_2 import MarketScenario, DecrementIndex, AutocallProduct, AthenaProduct, PhoenixProduct, SimulationEngine

st.set_page_config(page_title="Simulateur Monte Carlo : Stress Test Indice & Pricing Autocall", layout="wide")

# --- SIDEBAR ---
mode = st.sidebar.radio("Module", ["Comparaison Trajectoires", "Pricing"])
st.sidebar.divider()

st.sidebar.header("Paramètres")

with st.sidebar.expander("1. Durée", expanded=True):
    annees = st.number_input("Années totales", value=10, min_value=1, step=1)

with st.sidebar.expander("2. Scénario Macro", expanded=True):
    nb_periodes = st.number_input("Nombre de Périodes", value=1, min_value=1, step=1)
    
    mes_regimes_input = []
    somme_annees = 0
    for i in range(int(nb_periodes)):
        st.markdown(f"**Période {i+1}**")
        def_d = 10 if i == 0 else (2 if i == 1 else 5)
        def_rp = 0.0 if i == 0 else (-15.0 if i == 1 else 5.0)
        
        d = st.number_input(f"Durée (ans) P{i+1}", value=def_d, min_value=1, key=f"d_pct_{i}")
        rp = st.number_input(f"Drift Price Return P{i+1} (%)", value=def_rp, format="%.1f", key=f"rp_pct_{i}")
        st.divider()
        
        somme_annees += d
        mes_regimes_input.append({
            "duree_annees": int(d),
            "r_perf": rp / 100.0
        })

with st.sidebar.expander("3. Caractéristiques des Indices", expanded=True):
    nb_indices = st.number_input("Nombre d'indices à comparer", min_value=1, max_value=4, value=2, step=1)
    
    liste_indices = []
    tabs_indices = st.tabs([f"Indice {i+1}" for i in range(int(nb_indices))])
    
    for i, tab in enumerate(tabs_indices):
        with tab:
            def_s0 = 1000.0
            def_dec = 50.0 if i == 0 else (40.0 if i == 1 else (35.0 if i == 2 else 60.0))
            def_vol = 18.0 if i == 0 else (20.0 if i == 1 else (22.0 if i == 2 else 25.0))
            def_yi = 3.0 if i == 0 else (3.5 if i == 1 else (3.0 if i == 2 else 4.0))
            
            s0 = st.number_input("Niveau Initial S0 (pts)", value=def_s0, step=100.0, key=f"s0_idx_{i}")
            dec = st.number_input("Décrément Fixe Annuel D (pts)", value=def_dec, step=5.0, key=f"dec_idx_{i}")
            vol = st.number_input("Volatilité de l'Indice (%)", value=def_vol, step=1.0, format="%.1f", key=f"vol_idx_{i}")
            yi = st.number_input("Yield Div Naturel Réinvesti (%)", value=def_yi, step=0.25, format="%.2f", key=f"yi_idx_{i}")
            
            nom_idx = "Indice Décrément" if int(nb_indices) == 1 else f"Indice {i+1}"
            idx_temp = DecrementIndex(
                niveau_initial=s0,
                decrement_annuel=dec,
                vol=vol / 100.0,
                dividend_yield=yi / 100.0,
                nom=nom_idx
            )
            liste_indices.append(idx_temp)

if mode == "Pricing":
    with st.sidebar.expander("4. Produit Structuré", expanded=True):
        type_produit = st.selectbox("Type de Produit", ["Athéna", "Phoenix"])
        st.caption("Les barrières sont exprimées en pourcentage du niveau initial.")
        barriere_rappel_pct = st.number_input("Barrière Rappel (%)", value=100.0, step=10.0) / 100.0
        
        if type_produit == "Phoenix":
            barriere_coupon_pct = st.number_input("Barrière Coupon (%)", value=70.0, step=5.0) / 100.0
            avec_memoire = st.checkbox("Effet Mémoire des Coupons", value=True)
        else:
            barriere_coupon_pct = None
            avec_memoire = True
            
        niveau_pdi_pct = st.number_input("Niveau PDI (%)", value=50.0, step=10.0) / 100.0
        degressivite = st.number_input("Dégressivité de Rappel (%/obs)", value=0.0, step=1.0, 
                                        help="Baisse de la barrière en points à chaque constatation après la période de non-call.")
        coupon_periode = st.number_input("Coupon par observation (%)", value=2.0, step=0.1)
        non_call_period_mois = st.number_input("Période de Non-Call (mois)", value=11, step=1)
        frequence_obs_mois = st.number_input("Fréquence d'observation (mois)", value=3, step=1)

with st.sidebar.expander("5. Moteur de Simulation", expanded=False):
    nb_trajectoires = st.number_input("Nombre de Trajectoires", value=10000, step=1000)
    seed = st.number_input("Seed aléatoire", value=42, step=1)
    if mode == "Pricing":
        taux_actualisation_pct = st.number_input("Taux d'actualisation (%)", value=3.0, step=0.1)
        taux_actualisation = taux_actualisation_pct / 100.0
    else:
        taux_actualisation = 0.0

btn_text = "Lancer la Simulation d'Indices" if mode == "Comparaison Trajectoires" else "Lancer le Pricing"
lancer = st.sidebar.button(btn_text, type="primary", use_container_width=True)

# --- MAIN AREA ---
st.title(f"Simulateur Monte Carlo : {mode}")

if lancer:
    if somme_annees != annees:
        st.error(f"Incohérence : la somme des durées des régimes ({somme_annees} ans) doit être égale au total d'années ({annees} ans).")
    else:
        moteur = SimulationEngine(nb_trajectoires=int(nb_trajectoires), seed=int(seed))
        scenario_krach = MarketScenario(config_regimes=mes_regimes_input, annees=int(annees))

        if mode == "Comparaison Trajectoires":
            with st.spinner(f"Génération de {int(nb_trajectoires)} trajectoires pour {len(liste_indices)} indice(s)..."):
                results_multi = moteur.simulate_multi_indices(liste_indices, scenario_krach)
                
                st.subheader(f"Vue d'Ensemble & Indicateurs Clés à Maturité (Année {scenario_krach.annees})")
                
                data_macro = []
                for nom_idx, d in results_multi.items():
                    data_macro.append({
                        "Indice": nom_idx,
                        "Spot Initial S0": f"{d['index'].niveau_initial:.0f} pts",
                        "Décrément Fixe": f"{d['index'].decrement_annuel:.0f} pts/an",
                        "Volatilité": f"{d['index'].vol*100:.1f}%",
                        "Yield Div Naturel": f"{d['index'].dividend_yield*100:.1f}%",
                        "Niveau Final Décrément": f"{d['moy_dec']:.1f} pts ({d['moy_dec_pct']:+.1f}%)",
                        "Niveau Final PR": f"{d['moy_pr']:.1f} pts ({d['moy_pr_pct']:+.1f}%)",
                        "Écart Moyen (Dec - PR)": f"{d['ecart_moy_pct']:+.2f}% ({d['ecart_moy_pts']:+.1f} pts)",
                        "Risque Crash < 50%": f"{d['pct_crash_50_dec']:.1f}% (vs {d['pct_crash_50_pr']:.1f}% PR)"
                    })
                st.dataframe(pd.DataFrame(data_macro), use_container_width=True)
                st.markdown("---")
                
                # 1. Trajectoires Médianes Comparées
                st.subheader("1. Trajectoires Médianes & Fuseaux Inter-centiles [P10 - P90]")
                st.caption("Évolution comparée des indices normalisés en % de S0 sur la même matrice de chocs aléatoires.")
                fig_multi_traj = moteur.plot_multi_trajectoires(results_multi, scenario_krach)
                st.plotly_chart(fig_multi_traj, use_container_width=True)
                st.markdown("---")
                
                # 2. Dispersion des Écarts à Maturité
                st.subheader("2. Dispersion Comparée de l'Écart (Décrément - Price Return) à Maturité")
                st.caption("Distribution de la surperformance / sous-performance du décrément bornée entre les centiles P1 et P99.")
                fig_multi_disp = moteur.plot_multi_dispersion_ecarts(results_multi, scenario_krach)
                st.plotly_chart(fig_multi_disp, use_container_width=True)

        elif mode == "Pricing":
            with st.spinner(f"Valorisation sur {len(liste_indices)} indice(s) ({int(nb_trajectoires)} trajectoires appariées)..."):
                ref_s0 = 1000.0
                barriere_rappel = ref_s0 * barriere_rappel_pct
                niveau_pdi = ref_s0 * niveau_pdi_pct
                
                if type_produit == "Athéna":
                    mon_produit = AthenaProduct(
                        barriere_rappel=barriere_rappel,
                        niveau_pdi=niveau_pdi,
                        non_call_period_mois=int(non_call_period_mois),
                        frequence_obs_mois=int(frequence_obs_mois),
                        degressivite=float(degressivite),
                        coupon_periode=float(coupon_periode),
                        ref_s0=ref_s0
                    )
                else:
                    barriere_coupon = ref_s0 * barriere_coupon_pct
                    mon_produit = PhoenixProduct(
                        barriere_rappel=barriere_rappel,
                        barriere_coupon=barriere_coupon,
                        niveau_pdi=niveau_pdi,
                        non_call_period_mois=int(non_call_period_mois),
                        frequence_obs_mois=int(frequence_obs_mois),
                        degressivite=float(degressivite),
                        coupon_periode=float(coupon_periode),
                        avec_memoire=avec_memoire,
                        ref_s0=ref_s0
                    )
                
                results_multi_pricing = moteur.run_multi_indices(
                    liste_indices, scenario_krach, mon_produit, taux_actualisation=taux_actualisation
                )
                
                memoire_str = " (Mémoire)" if (type_produit == "Phoenix" and avec_memoire) else (" (Sans Mémoire)" if type_produit == "Phoenix" else "")
                st.subheader(f"Indicateurs de Performance et de Risque : {type_produit}{memoire_str}")
                
                # Tableau comparatif
                data_pricing = []
                for nom_idx, d in results_multi_pricing.items():
                    lev_str = f"{d['levier_equivalent']:.2f}x" if d['levier_equivalent'] is not None else "N/A"
                    data_pricing.append({
                        "Indice": nom_idx,
                        "Taux d'Autocall": f"{d['pct_rappel_dec']:.1f}% (vs {d['pct_rappel_pr']:.1f}% PR)",
                        "Espérance de Gain": f"{d['moy_payoff_dec']:.2f}% (vs {d['moy_payoff_pr']:.2f}% PR)",
                        "Duration Espérée": f"{d['duration_dec']:.2f} ans (vs {d['duration_pr']:.2f} ans PR)",
                        "Probabilité sous PDI": f"{d['pct_pdi_dec']:.2f}% (vs {d['pct_pdi_pr']:.2f}% PR)",
                        "Levier Krach vs PR": lev_str
                    })
                st.dataframe(pd.DataFrame(data_pricing), use_container_width=True)
                st.markdown("---")
                
                # 1. Graphique Comparatif des KPIs
                st.subheader("1. Indicateurs Comparés de Performance et de Risque")
                fig_kpis = moteur.plot_multi_pricing_kpis(results_multi_pricing)
                st.plotly_chart(fig_kpis, use_container_width=True)
                st.markdown("---")
                
                # 2. Distribution comparée des dates de rappel
                st.subheader("2. Distribution Comparée des Dates de Rappel Anticipé")
                fig_rappels = moteur.plot_multi_pricing_rappels(results_multi_pricing, scenario_krach, mon_produit)
                st.plotly_chart(fig_rappels, use_container_width=True)
                st.markdown("---")
                
                # 3. Dispersion des écarts à maturité
                st.subheader("3. Dispersion Comparée de l'Écart (Décrément - Price Return) à Maturité")
                fig_disp_pricing = moteur.plot_multi_dispersion_ecarts(results_multi_pricing, scenario_krach)
                st.plotly_chart(fig_disp_pricing, use_container_width=True)

else:
    st.info("Ajustez les paramètres dans la barre latérale gauche, puis cliquez sur le bouton pour lancer le calcul.")
