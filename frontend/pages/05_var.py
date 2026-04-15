"""
05_var.py — Módulo 5: Valor en Riesgo (VaR) y CVaR.
Peso en rúbrica: 10%

Consume POST /var con PortafolioRequest (validación Pydantic con @field_validator).
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


def _post(endpoint, body):
    try:
        r = requests.post(f"{BACKEND_URL}{endpoint}", json=body, timeout=60)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 422:
            for e in r.json().get("errores", []):
                st.error(f"❌ `{e['campo']}`: {e['mensaje']}")
        else:
            st.error(f"Error {r.status_code}: {r.text[:300]}")
        return None
    except Exception as ex:
        st.error(f"Conexión fallida: {ex}")
        return None


st.set_page_config(page_title="VaR — RiskLab", layout="wide")
st.title("⚠️ Módulo 5 — Valor en Riesgo (VaR) y CVaR")
st.markdown("Cuantifica la pérdida potencial del portafolio usando 3 métodos + Expected Shortfall.")

with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_var")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    periodo = st.selectbox("Período", ["1y", "2y", "3y"], index=1, key="periodo_var")
    nivel = st.slider("Nivel de confianza", 0.90, 0.99, 0.95, 0.01, key="nivel_var")

    st.divider()
    st.markdown("**Pesos del portafolio**")
    n = len(tickers)
    pesos = []
    for i, t in enumerate(tickers):
        default = round(1.0 / n, 4) if i < n - 1 else round(1.0 - sum([round(1.0/n, 4)] * (n-1)), 4)
        p = st.number_input(t, min_value=0.0, max_value=1.0, value=default, step=0.01, key=f"peso_{t}_var")
        pesos.append(p)

    suma_pesos = sum(pesos)
    if abs(suma_pesos - 1.0) > 0.001:
        st.error(f"⚠️ Los pesos suman {suma_pesos:.4f}. Deben sumar 1.0")

calcular = st.button("⚡ Calcular VaR y CVaR", type="primary", disabled=abs(sum(pesos) - 1.0) > 0.001)

if calcular:
    body = {
        "tickers": tickers,
        "pesos": pesos,
        "nivel_confianza": nivel,
        "periodo": periodo,
    }
    with st.spinner("Ejecutando 10,000 simulaciones Montecarlo..."):
        data = _post("/var", body)
else:
    data = None

if not data:
    st.info("👆 Configura el portafolio en el sidebar y presiona **Calcular VaR y CVaR**")
    st.stop()

# ── KPIs del portafolio ────────────────────────────────────────────────────
st.markdown("### 📊 Perfil del Portafolio")
k1, k2, k3 = st.columns(3)
k1.metric("Rendimiento Anual", f"{data['rendimiento_portafolio_anual']*100:.2f}%")
k2.metric("Volatilidad Anual", f"{data['volatilidad_portafolio_anual']*100:.2f}%")
k3.metric("Nivel de Confianza", f"{data['nivel_confianza']:.0%}")

# ── Tabla comparativa ─────────────────────────────────────────────────────
st.markdown("### 📋 Comparación de Métodos VaR")
metodos = [data["parametrico"], data["historico"], data["montecarlo"]]
df_var = pd.DataFrame([{
    "Método": m["metodo"],
    "VaR Diario": m["var_diario_pct"],
    "VaR Anual": m["var_anual_pct"],
} for m in metodos])

cvar_data = data["cvar"]
df_var = pd.concat([df_var, pd.DataFrame([{
    "Método": "CVaR (Expected Shortfall)",
    "VaR Diario": cvar_data["cvar_diario_pct"],
    "VaR Anual": "—",
}])], ignore_index=True)

st.dataframe(df_var, use_container_width=True)

# ── Gráfico: Distribución con líneas VaR ──────────────────────────────────
st.markdown("### 📈 Distribución de Rendimientos y Líneas VaR")
mu = data["rendimiento_portafolio_anual"] / 252
sigma = data["volatilidad_portafolio_anual"] / np.sqrt(252)
sim = np.random.normal(mu, sigma, 50000)

fig = go.Figure()
fig.add_trace(go.Histogram(x=sim * 100, histnorm="probability density", nbinsx=100,
    marker_color="#6366f1", opacity=0.7, name="Distribución simulada"))

colores = {"Paramétrico": "#f59e0b", "Histórico": "#10b981", "Montecarlo": "#ef4444"}
for m in metodos:
    nombre = m["metodo"].split("(")[0].strip()
    fig.add_vline(x=-m["var_diario"] * 100, line_dash="dash",
        line_color=colores.get(nombre, "white"),
        annotation_text=f'{nombre[:5]}: {m["var_diario_pct"]}',
        annotation_position="top left")

fig.add_vline(x=-cvar_data["cvar_diario"] * 100, line_dash="dot",
    line_color="#a855f7", annotation_text=f'CVaR: {cvar_data["cvar_diario_pct"]}',
    annotation_position="top left")

fig.update_layout(title="Distribución de Rendimientos del Portafolio", xaxis_title="Rendimiento diario (%)",
    yaxis_title="Densidad", template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# ── Interpretaciones ──────────────────────────────────────────────────────
st.markdown("### 📚 Interpretación")
for m in metodos:
    with st.expander(m["metodo"]):
        st.info(m["interpretacion"])
with st.expander("CVaR (Expected Shortfall)"):
    st.warning(cvar_data["interpretacion"])
