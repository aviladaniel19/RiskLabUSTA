"""
04_capm.py — Módulo 4: CAPM y Beta (8%)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios, cargar_indice, calcular_rendimientos
from src.capm import tabla_capm, calcular_beta, discusion_riesgo_sistematico
from src.api_client import obtener_rf_actual

st.set_page_config(page_title="CAPM y Beta — RiskLabUSTA", page_icon="🛡️", layout="wide")
st.title("🛡️ Módulo 4: CAPM y Riesgo Sistemático")
st.markdown("**Peso en la rúbrica: 8%** — Beta, CAPM con Rf desde API, clasificación de activos.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
benchmark = st.session_state.get("benchmark", "^GSPC")
periodo = st.session_state.get("periodo", "2y")

try:
    precios = cargar_precios(tickers, periodo=periodo)
    indice = cargar_indice(benchmark, periodo=periodo)
    ret_activos = calcular_rendimientos(precios, "log")
    ret_indice = calcular_rendimientos(indice.to_frame(), "log").iloc[:, 0]
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

# ── 1. Tasa libre de riesgo desde API ──
st.subheader("🏦 Tasa Libre de Riesgo (FRED API)")
try:
    rf = obtener_rf_actual()
    st.success(f"✅ Tasa libre de riesgo obtenida de FRED (T-Bill 3M): **{rf*100:.2f}%** anual")
except Exception as e:
    rf = 0.0525
    st.warning(f"⚠️ No se pudo obtener Rf de FRED. Usando valor manual: {rf*100:.2f}%. Error: {e}")

# ── 2. Tabla CAPM ──
st.subheader("📋 Tabla de Beta y CAPM por Activo")
capm_df = tabla_capm(ret_activos, ret_indice, rf)
st.dataframe(capm_df, width="stretch")

# ── 3. Gráficos de dispersión ──
st.subheader("📊 Dispersión: Rendimientos del Activo vs. Índice")

ticker_sel = st.selectbox("Selecciona un activo:", tickers)

datos_comunes = ret_activos[[ticker_sel]].join(ret_indice.rename("Índice"), how="inner").dropna()
beta_info = calcular_beta(datos_comunes[ticker_sel], datos_comunes["Índice"])

fig_disp = go.Figure()
fig_disp.add_trace(go.Scatter(
    x=datos_comunes["Índice"], y=datos_comunes[ticker_sel],
    mode="markers", name="Rendimientos",
    marker=dict(color="#0f3460", size=3, opacity=0.4)
))

# Línea de regresión
x_range = np.linspace(datos_comunes["Índice"].min(), datos_comunes["Índice"].max(), 100)
y_reg = beta_info["alpha"] + beta_info["beta"] * x_range
fig_disp.add_trace(go.Scatter(
    x=x_range, y=y_reg, mode="lines", name=f"β = {beta_info['beta']:.4f}",
    line=dict(color="#e94560", width=2)
))
fig_disp.update_layout(
    title=f"{ticker_sel} vs {benchmark} — Beta = {beta_info['beta']:.4f} (R² = {beta_info['r_cuadrado']:.4f})",
    xaxis_title=f"Rendimiento {benchmark}",
    yaxis_title=f"Rendimiento {ticker_sel}",
    template="plotly_white", height=450
)
st.plotly_chart(fig_disp, width="stretch")

col1, col2, col3 = st.columns(3)
col1.metric("Beta", f"{beta_info['beta']:.4f}")
col2.metric("R²", f"{beta_info['r_cuadrado']:.4f}")
col3.metric("P-valor", f"{beta_info['p_valor']:.6f}")

# ── 4. Gráfico de Betas ──
st.subheader("📊 Comparación de Betas")
betas = []
for t in tickers:
    if t in ret_activos.columns:
        b = calcular_beta(ret_activos[t], ret_indice)
        betas.append({"Ticker": t, "Beta": b["beta"]})

import pandas as pd
betas_df = pd.DataFrame(betas)
colors = ["#e94560" if b > 1.2 else "#f5a623" if b > 0.8 else "#2ecc71" for b in betas_df["Beta"]]

fig_betas = go.Figure(go.Bar(x=betas_df["Ticker"], y=betas_df["Beta"],
                              marker_color=colors))
fig_betas.add_hline(y=1, line_dash="dash", line_color="gray", annotation_text="β = 1 (Mercado)")
fig_betas.update_layout(title="Beta de cada activo", yaxis_title="Beta",
                         template="plotly_white", height=350)
st.plotly_chart(fig_betas, width="stretch")

# ── 5. Discusión ──
st.subheader("📝 Riesgo Sistemático vs. No Sistemático")
st.markdown(discusion_riesgo_sistematico())
