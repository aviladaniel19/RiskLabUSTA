"""
06_markowitz.py — Módulo 6: Optimización de Portafolio (Markowitz).
Peso en rúbrica: 10%

Consume POST /frontera-eficiente.
"""

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


def _post(endpoint, body):
    try:
        r = requests.post(f"{BACKEND_URL}{endpoint}", json=body, timeout=120)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 422:
            for e in r.json().get("errores", []):
                st.error(f"❌ `{e['campo']}`: {e['mensaje']}")
        else:
            st.error(f"Error {r.status_code}")
        return None
    except Exception as ex:
        st.error(f"Conexión fallida: {ex}")
        return None


st.set_page_config(page_title="Markowitz — RiskLab", layout="wide")
st.title("🎯 Módulo 6 — Optimización de Portafolio (Markowitz)")
st.markdown("Frontera eficiente construida con **10,000 portafolios simulados**. Identifica mínima varianza y máximo Sharpe.")

with st.sidebar:
    tickers_raw = st.text_input("Tickers (mín. 2)", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_mkw")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    periodo = st.selectbox("Período", ["1y", "2y", "3y"], index=1, key="periodo_mkw")

    n = len(tickers)
    pesos = [round(1.0 / n, 4)] * (n - 1)
    pesos.append(round(1.0 - sum(pesos), 4))

calcular = st.button("🚀 Calcular Frontera Eficiente (10,000 sim.)", type="primary")

if calcular:
    body = {"tickers": tickers, "pesos": pesos, "periodo": periodo}
    with st.spinner("Simulando 10,000 portafolios... puede tomar 30-60 segundos."):
        data = _post("/frontera-eficiente", body)
else:
    data = None

if not data:
    if not calcular:
        st.info("👆 Configura los tickers en el sidebar y presiona **Calcular Frontera Eficiente**")
    st.stop()

# ── Heatmap de correlación ─────────────────────────────────────────────────
st.markdown("### 🗓️ Matriz de Correlación")
corr = data["matriz_correlacion"]
tickers_corr = list(corr.keys())
matriz = [[corr[t1].get(t2, 0) for t2 in tickers_corr] for t1 in tickers_corr]
fig_corr = go.Figure(go.Heatmap(
    z=matriz, x=tickers_corr, y=tickers_corr,
    colorscale="RdBu_r", zmin=-1, zmax=1,
    text=[[f"{v:.2f}" for v in row] for row in matriz],
    texttemplate="%{text}",
))
fig_corr.update_layout(template="plotly_dark", height=350, title="Correlación de Rendimientos Logarítmicos")
st.plotly_chart(fig_corr, use_container_width=True)

# ── Gráfico Frontera Eficiente ─────────────────────────────────────────────
st.markdown("### 🌈 Frontera Eficiente — 10,000 portafolios simulados")
puntos = data["puntos_simulados"]
mv = data["portafolio_min_varianza"]
ms = data["portafolio_max_sharpe"]

fig = go.Figure()

# Nube de portafolios
fig.add_trace(go.Scatter(
    x=[p["volatilidad"] * 100 for p in puntos],
    y=[p["rendimiento"] * 100 for p in puntos],
    mode="markers",
    marker=dict(
        color=[p["sharpe"] for p in puntos],
        colorscale="Viridis",
        size=3,
        opacity=0.6,
        colorbar=dict(title="Sharpe Ratio"),
    ),
    name="Portafolios simulados",
))

# Portafolio mínima varianza
fig.add_trace(go.Scatter(
    x=[mv["volatilidad_anual"] * 100],
    y=[mv["rendimiento_anual"] * 100],
    mode="markers+text",
    marker=dict(size=18, color="#22c55e", symbol="star"),
    text=["Min. Varianza"],
    textposition="top right",
    name="Mínima Varianza",
))

# Portafolio máximo Sharpe
fig.add_trace(go.Scatter(
    x=[ms["volatilidad_anual"] * 100],
    y=[ms["rendimiento_anual"] * 100],
    mode="markers+text",
    marker=dict(size=18, color="#f59e0b", symbol="star"),
    text=["Máx. Sharpe"],
    textposition="top right",
    name="Máximo Sharpe",
))

fig.update_layout(
    title=f"Frontera Eficiente — {data['n_simulaciones']:,} portafolios",
    xaxis_title="Volatilidad Anual (%)",
    yaxis_title="Rendimiento Anual (%)",
    template="plotly_dark",
    height=550,
)
st.plotly_chart(fig, use_container_width=True)

# ── Composición portafolios óptimos ──────────────────────────────────────
st.markdown("### 📊 Composición de Portafolios Óptimos")
col_mv, col_ms = st.columns(2)

with col_mv:
    st.markdown("**🟢 Portafolio de Mínima Varianza**")
    st.metric("Rendimiento anual", f"{mv['rendimiento_anual']*100:.2f}%")
    st.metric("Volatilidad anual", f"{mv['volatilidad_anual']*100:.2f}%")
    st.metric("Sharpe Ratio", f"{mv['sharpe_ratio']:.4f}")
    df_comp = pd.DataFrame({"Ticker": mv["tickers"], "Peso": [f"{p*100:.2f}%" for p in mv["pesos"]]})
    st.dataframe(df_comp, use_container_width=True)

with col_ms:
    st.markdown("**🟡 Portafolio de Máximo Sharpe**")
    st.metric("Rendimiento anual", f"{ms['rendimiento_anual']*100:.2f}%")
    st.metric("Volatilidad anual", f"{ms['volatilidad_anual']*100:.2f}%")
    st.metric("Sharpe Ratio", f"{ms['sharpe_ratio']:.4f}")
    df_comp2 = pd.DataFrame({"Ticker": ms["tickers"], "Peso": [f"{p*100:.2f}%" for p in ms["pesos"]]})
    st.dataframe(df_comp2, use_container_width=True)
