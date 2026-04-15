"""
05_var.py — Módulo 5: VaR y CVaR (12%)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios, calcular_rendimientos
from src.var_cvar import (var_parametrico, var_historico, var_montecarlo,
                           cvar, tabla_comparativa_var)

st.set_page_config(page_title="VaR y CVaR — RiskLabUSTA", page_icon="⚠️", layout="wide")
st.title("⚠️ Módulo 5: Valor en Riesgo (VaR) y CVaR")
st.markdown("**Peso en la rúbrica: 12%** — 3 métodos de VaR + Expected Shortfall.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
periodo = st.session_state.get("periodo", "2y")
ticker_sel = st.selectbox("Selecciona un activo:", tickers)

try:
    precios = cargar_precios([ticker_sel], periodo=periodo)
    rendimientos = calcular_rendimientos(precios, "log").iloc[:, 0]
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

nivel = st.select_slider("Nivel de confianza:", options=[0.90, 0.95, 0.99], value=0.95)

# ── 1. Cálculos ──
vp = var_parametrico(rendimientos, nivel)
vh = var_historico(rendimientos, nivel)
vm = var_montecarlo(rendimientos, nivel, n_simulaciones=10000)
cv = cvar(rendimientos, nivel)

# ── 2. Métricas resumen ──
st.subheader("📊 Resumen de VaR y CVaR")

col1, col2, col3, col4 = st.columns(4)
col1.metric("VaR Paramétrico", f"{vp['var_diario']*100:.2f}%",
            delta=f"Anual: {vp['var_anual']*100:.2f}%")
col2.metric("VaR Histórico", f"{vh['var_diario']*100:.2f}%",
            delta=f"Anual: {vh['var_anual']*100:.2f}%")
col3.metric("VaR Montecarlo", f"{vm['var_diario']*100:.2f}%",
            delta=f"Anual: {vm['var_anual']*100:.2f}%")
col4.metric("CVaR (ES)", f"{cv['cvar_diario']*100:.2f}%",
            delta=f"Anual: {cv['cvar_anual']*100:.2f}%", delta_color="inverse")

# ── 3. Tabla comparativa ──
st.subheader("📋 Tabla Comparativa de Métodos")
tabla = tabla_comparativa_var(rendimientos, [0.95, 0.99])
st.dataframe(tabla, width="stretch")

# ── 4. Visualización: distribución con líneas VaR y CVaR ──
st.subheader("📊 Distribución de Rendimientos con VaR y CVaR")

fig = go.Figure()
fig.add_trace(go.Histogram(x=rendimientos.values, nbinsx=100, name="Rendimientos",
                            marker_color="#0f3460", opacity=0.7,
                            histnorm="probability density"))

# Líneas de VaR
fig.add_vline(x=-vp["var_diario"], line_dash="solid", line_color="red",
              annotation_text=f"VaR Param. ({nivel*100:.0f}%)")
fig.add_vline(x=-vh["var_diario"], line_dash="dash", line_color="orange",
              annotation_text=f"VaR Hist.")
fig.add_vline(x=-cv["cvar_diario"], line_dash="dot", line_color="darkred",
              annotation_text=f"CVaR")

fig.update_layout(
    title=f"Distribución de rendimientos de {ticker_sel} con VaR al {nivel*100:.0f}%",
    xaxis_title="Rendimiento diario",
    yaxis_title="Densidad",
    template="plotly_white", height=450,
)
st.plotly_chart(fig, width="stretch")

# ── 5. Simulación Montecarlo ──
st.subheader("📊 Distribución Montecarlo (10,000 simulaciones)")

fig_mc = go.Figure()
fig_mc.add_trace(go.Histogram(x=vm["simulaciones"], nbinsx=100,
                               name="Simulaciones MC",
                               marker_color="#16213e", opacity=0.7,
                               histnorm="probability density"))
fig_mc.add_vline(x=-vm["var_diario"], line_dash="solid", line_color="red",
                  annotation_text=f"VaR MC ({nivel*100:.0f}%)")
fig_mc.update_layout(title="Distribución de simulaciones Montecarlo",
                      xaxis_title="Rendimiento simulado",
                      template="plotly_white", height=350)
st.plotly_chart(fig_mc, width="stretch")

# ── 6. Interpretaciones ──
st.subheader("📝 Interpretación")
st.markdown(vp["interpretacion"])
st.markdown(vh["interpretacion"])
st.markdown(vm["interpretacion"])
st.markdown(cv["interpretacion"])

st.info("""
💡 **¿Cuál método usar?**
- **Paramétrico:** Rápido, pero asume normalidad (no siempre realista).
- **Histórico:** No asume distribución, pero depende de que el pasado se repita.
- **Montecarlo:** Flexible, permite distribuciones no normales. Costoso computacionalmente.
- **CVaR:** Complementa el VaR midiendo la pérdida *promedio* en el peor escenario.
""")
