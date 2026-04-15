"""
06_markowitz.py — Módulo 6: Optimización de Portafolio — Markowitz (12%)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios, calcular_rendimientos
from src.markowitz import (simular_portafolios, portafolio_minima_varianza,
                            portafolio_max_sharpe, frontera_eficiente, tabla_composicion)
from src.api_client import obtener_rf_actual

st.set_page_config(page_title="Markowitz — RiskLabUSTA", page_icon="🎯", layout="wide")
st.title("🎯 Módulo 6: Optimización de Portafolio — Markowitz")
st.markdown("**Peso en la rúbrica: 12%** — Frontera eficiente, portafolios óptimos.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
periodo = st.session_state.get("periodo", "2y")

try:
    precios = cargar_precios(tickers, periodo=periodo)
    rendimientos = calcular_rendimientos(precios, "log")
    rf = obtener_rf_actual()
except Exception as e:
    st.error(f"❌ Error: {e}")
    rf = 0.05
    st.stop()

# ── 1. Heatmap de correlaciones ──
st.subheader("🗺️ Matriz de Correlación")

corr = rendimientos.corr()
fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                      zmin=-1, zmax=1, aspect="auto")
fig_corr.update_layout(title="Correlación entre activos", height=400, template="plotly_white")
st.plotly_chart(fig_corr, width="stretch")

# ── 2. Simulación de portafolios ──
st.subheader("📊 Simulación de 10,000 Portafolios Aleatorios")

with st.spinner("Simulando portafolios..."):
    sim = simular_portafolios(rendimientos, n_portafolios=10000, rf=rf)

# ── 3. Portafolios óptimos ──
with st.spinner("Optimizando..."):
    min_var = portafolio_minima_varianza(rendimientos, rf)
    max_sh = portafolio_max_sharpe(rendimientos, rf)
    frontera = frontera_eficiente(rendimientos, n_puntos=100, rf=rf)

# ── 4. Gráfico de frontera eficiente ──
fig_front = go.Figure()

# Nube de portafolios
fig_front.add_trace(go.Scatter(
    x=sim["Volatilidad"], y=sim["Rendimiento"],
    mode="markers", name="Portafolios simulados",
    marker=dict(color=sim["Sharpe"], colorscale="Viridis",
                size=3, opacity=0.4, colorbar=dict(title="Sharpe"))
))

# Frontera eficiente
if not frontera.empty:
    fig_front.add_trace(go.Scatter(
        x=frontera["Volatilidad"], y=frontera["Rendimiento"],
        mode="lines", name="Frontera Eficiente",
        line=dict(color="#e94560", width=3)
    ))

# Portafolio de mínima varianza
fig_front.add_trace(go.Scatter(
    x=[min_var["volatilidad"]], y=[min_var["rendimiento"]],
    mode="markers", name=f"Mínima Varianza (Sharpe: {min_var['sharpe']:.3f})",
    marker=dict(color="blue", size=15, symbol="star")
))

# Portafolio de máximo Sharpe
fig_front.add_trace(go.Scatter(
    x=[max_sh["volatilidad"]], y=[max_sh["rendimiento"]],
    mode="markers", name=f"Máximo Sharpe ({max_sh['sharpe']:.3f})",
    marker=dict(color="gold", size=15, symbol="star")
))

fig_front.update_layout(
    title="Frontera Eficiente de Markowitz",
    xaxis_title="Volatilidad (riesgo) anualizada",
    yaxis_title="Rendimiento anualizado",
    template="plotly_white", height=550,
)
st.plotly_chart(fig_front, width="stretch")

# ── 5. Composición de portafolios óptimos ──
st.subheader("📋 Composición de Portafolios Óptimos")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔵 Mínima Varianza")
    st.metric("Rendimiento", f"{min_var['rendimiento']*100:.2f}%")
    st.metric("Volatilidad", f"{min_var['volatilidad']*100:.2f}%")
    st.metric("Sharpe Ratio", f"{min_var['sharpe']:.3f}")
    st.dataframe(tabla_composicion(min_var), width="stretch")

with col2:
    st.markdown("### ⭐ Máximo Sharpe")
    st.metric("Rendimiento", f"{max_sh['rendimiento']*100:.2f}%")
    st.metric("Volatilidad", f"{max_sh['volatilidad']*100:.2f}%")
    st.metric("Sharpe Ratio", f"{max_sh['sharpe']:.3f}")
    st.dataframe(tabla_composicion(max_sh), width="stretch")

# ── 6. Gráficos circulares ──
st.subheader("📊 Distribución de Pesos")

col1, col2 = st.columns(2)
with col1:
    pesos_mv = {k: v for k, v in min_var["pesos"].items() if v > 0.001}
    fig_pie1 = go.Figure(go.Pie(labels=list(pesos_mv.keys()),
                                 values=list(pesos_mv.values()),
                                 textinfo="label+percent"))
    fig_pie1.update_layout(title="Mínima Varianza", height=350)
    st.plotly_chart(fig_pie1, width="stretch")

with col2:
    pesos_ms = {k: v for k, v in max_sh["pesos"].items() if v > 0.001}
    fig_pie2 = go.Figure(go.Pie(labels=list(pesos_ms.keys()),
                                 values=list(pesos_ms.values()),
                                 textinfo="label+percent"))
    fig_pie2.update_layout(title="Máximo Sharpe", height=350)
    st.plotly_chart(fig_pie2, width="stretch")
