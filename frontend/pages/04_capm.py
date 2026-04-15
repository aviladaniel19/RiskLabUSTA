"""
04_capm.py — Módulo 4: CAPM y Riesgo Sistemático.
Peso en rúbrica: 6%

Consume GET /capm?tickers=...
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=3600, show_spinner=False)
def _get(endpoint, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", params=params or {}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


st.set_page_config(page_title="CAPM — RiskLab", layout="wide")
st.title("🛡️ Módulo 4 — CAPM y Riesgo Sistemático")
st.markdown("Beta calculado por regresión OLS. Tasa libre de riesgo obtenida automáticamente desde **FRED API** (T-Bill 3 meses).")

with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_capm")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    periodo = st.selectbox("Período", ["1y", "2y", "3y"], index=1, key="periodo_capm")

with st.spinner("Calculando CAPM con Rf desde FRED..."):
    data = _get("/capm", {"tickers": ",".join(tickers), "periodo": periodo})

if not data:
    st.error("Error al calcular CAPM. Verifica la FRED_API_KEY en el archivo .env")
    st.stop()

# ── KPIs: Rf y mercado ────────────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("📡 Tasa Libre de Riesgo (FRED)", data["rf_actual_pct"], help="T-Bill 3 meses, obtenida en tiempo real desde FRED API")
k2.metric("📈 Benchmark", data["benchmark"])
k3.metric("📊 Rend. Mercado Anual", f"{data['rendimiento_mercado_anual']*100:.2f}%")

# ── Tabla CAPM ─────────────────────────────────────────────────────────────
st.markdown("### 📋 Tabla Resumen CAPM")
activos = data["activos"]
df = pd.DataFrame(activos)

# Color de fondo según clasificación
def color_beta(val):
    if "Agresivo" in str(val):
        return "color: #ef4444; font-weight: bold"
    elif "Defensivo" in str(val):
        return "color: #22c55e; font-weight: bold"
    return "color: #f59e0b; font-weight: bold"

cols_mostrar = ["ticker", "beta", "alpha_jensen", "r_cuadrado", "clasificacion", "rendimiento_esperado_capm_pct"]
df_display = df[cols_mostrar].rename(columns={
    "ticker": "Activo",
    "beta": "Beta (β)",
    "alpha_jensen": "Alpha Jensen (anual)",
    "r_cuadrado": "R²",
    "clasificacion": "Clasificación",
    "rendimiento_esperado_capm_pct": "E(Ri) CAPM",
})

st.dataframe(
    df_display.style.applymap(color_beta, subset=["Clasificación"]),
    use_container_width=True,
)

# ── Gráfico: Scatter Beta vs Rendimiento Esperado ─────────────────────────
st.markdown("### 📉 Security Market Line (SML)")
fig = go.Figure()

betas_rango = [0, max([a["beta"] for a in activos]) + 0.3]
rf = data["rf_actual"]
rm = data["rendimiento_mercado_anual"]
sml_y = [rf + b * (rm - rf) for b in betas_rango]

fig.add_trace(go.Scatter(x=betas_rango, y=[y*100 for y in sml_y], mode="lines", name="SML", line=dict(color="#6366f1", width=2, dash="dash")))

for a in activos:
    fig.add_trace(go.Scatter(
        x=[a["beta"]], y=[a["rendimiento_esperado_capm"] * 100],
        mode="markers+text",
        name=a["ticker"],
        text=[a["ticker"]],
        textposition="top center",
        marker=dict(size=12),
    ))

fig.update_layout(
    title="Security Market Line — CAPM",
    xaxis_title="Beta (β)",
    yaxis_title="Rendimiento Esperado CAPM (%)",
    template="plotly_dark",
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# ── Discusión ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📚 Riesgo Sistemático vs. No Sistemático")
st.markdown(data["discusion"])
