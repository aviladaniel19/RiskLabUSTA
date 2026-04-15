"""
02_rendimientos.py — Módulo 2: Rendimientos y Propiedades Empíricas.
Peso en rúbrica: 6%

Consume GET /rendimientos/{ticker}.
"""

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import streamlit as st
import requests
from scipy import stats as scipy_stats

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=3600, show_spinner=False)
def _get(endpoint, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", params=params or {}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


st.set_page_config(page_title="Rendimientos — RiskLab", layout="wide")
st.title("📉 Módulo 2 — Rendimientos y Propiedades Empíricas")

with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_ret")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    ticker_sel = st.selectbox("Activo a analizar", tickers, key="ticker_ret")
    periodo = st.selectbox("Período", ["1y", "2y", "3y"], index=1, key="periodo_ret")

with st.spinner(f"Calculando rendimientos de {ticker_sel}..."):
    data = _get(f"/rendimientos/{ticker_sel}", {"periodo": periodo})

if not data:
    st.error("No se obtuvieron datos. Verifica el ticker y que el backend esté corriendo.")
    st.stop()

df = pd.DataFrame(data["rendimientos"])
ret = df["rendimiento_log"].values
est = data["estadisticas"]

# ── Estadísticas descriptivas ──────────────────────────────────────────────
st.markdown("### 📊 Estadísticas Descriptivas")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Media diaria", f"{est['media_diaria']*100:.4f}%")
c2.metric("Vol. anualizada", f"{est['volatilidad_anualizada']*100:.2f}%")
c3.metric("Media anualizada", f"{est['media_anualizada']*100:.2f}%")
c4.metric("Asimetría", f"{est['asimetría']:.4f}")
c5.metric("Curtosis exceso", f"{est['curtosis_exceso']:.4f}")
c6.metric("Observaciones", f"{est['n_observaciones']:,}")

# ── Visualizaciones ────────────────────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("Serie de Rendimientos", "Histograma + Curva Normal", "Q-Q Plot", "Boxplot"),
)

# Serie temporal
fig.add_trace(go.Scatter(x=df["fecha"], y=ret, mode="lines", name="Rend. log", line=dict(color="#6366f1", width=0.8)), row=1, col=1)
fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)

# Histograma + Normal
mu, sigma = est["media_diaria"], est["volatilidad_diaria"]
x_norm = np.linspace(min(ret), max(ret), 200)
y_norm = scipy_stats.norm.pdf(x_norm, mu, sigma)
fig.add_trace(go.Histogram(x=ret, histnorm="probability density", name="Histograma", marker_color="#8b5cf6", opacity=0.7, nbinsx=60), row=1, col=2)
fig.add_trace(go.Scatter(x=x_norm, y=y_norm, name="Normal teórica", line=dict(color="#f43f5e", width=2)), row=1, col=2)

# Q-Q Plot
(osm, osr) = scipy_stats.probplot(ret, dist="norm")[:2]
qq_df = pd.DataFrame({"teoricos": osm[0], "observados": osm[1]})
fig.add_trace(go.Scatter(x=qq_df["teoricos"], y=qq_df["observados"], mode="markers", name="Q-Q", marker=dict(color="#10b981", size=3)), row=2, col=1)
lim = max(abs(qq_df["teoricos"].min()), abs(qq_df["teoricos"].max()))
fig.add_trace(go.Scatter(x=[-lim, lim], y=[-lim, lim], name="Normal ref", line=dict(color="red", dash="dash")), row=2, col=1)

# Boxplot
fig.add_trace(go.Box(y=ret, name=ticker_sel, marker_color="#f59e0b"), row=2, col=2)

fig.update_layout(height=700, template="plotly_dark", showlegend=False, title_text=f"Análisis de Rendimientos — {ticker_sel}")
st.plotly_chart(fig, use_container_width=True)

# ── Pruebas de normalidad ──────────────────────────────────────────────────
st.markdown("### 🧪 Pruebas de Normalidad")
col_jb, col_sw = st.columns(2)

jb = data["jarque_bera"]
sw = data["shapiro_wilk"]

with col_jb:
    st.markdown("**Jarque-Bera**")
    st.metric("Estadístico", f"{jb['estadístico']:.4f}")
    st.metric("p-valor", f"{jb['p_valor']:.6f}")
    if jb["es_normal"]:
        st.success("✅ No se rechaza H₀ — posible normalidad")
    else:
        st.error("❌ Se rechaza H₀ — distribución NO normal")
    st.caption(jb["interpretación"])

with col_sw:
    st.markdown("**Shapiro-Wilk**")
    st.metric("Estadístico", f"{sw['estadístico']:.6f}")
    st.metric("p-valor", f"{sw['p_valor']:.6f}")
    if sw["es_normal"]:
        st.success("✅ No se rechaza H₀ — posible normalidad")
    else:
        st.error("❌ Se rechaza H₀ — distribución NO normal")
    st.caption(sw["interpretación"])

# ── Hechos estilizados ─────────────────────────────────────────────────────
st.divider()
st.markdown("### 📚 Hechos Estilizados")
st.markdown(data["hechos_estilizados"])
