"""
08_macro.py — Módulo 8: Contexto Macroeconómico y Benchmark.
Peso en rúbrica: 6%

Consume GET /macro?tickers=...&pesos=...
"""

import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=3600, show_spinner=False)
def _get(endpoint, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", params=params or {}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


st.set_page_config(page_title="Macro — RiskLab", layout="wide")
st.title("🌍 Módulo 8 — Contexto Macroeconómico y Benchmark")
st.markdown("Indicadores macro en tiempo real desde **FRED API** + comparativa de desempeño vs S&P 500.")

with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_mac")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    periodo = st.selectbox("Período", ["1y", "2y", "3y"], index=1, key="periodo_mac")

    st.divider()
    st.markdown("**Pesos del Portafolio**")
    n = len(tickers)
    pesos = []
    for t in tickers:
        p = st.number_input(t, value=round(1.0/n, 4), min_value=0.0, max_value=1.0, step=0.01, key=f"peso_{t}_mac")
        pesos.append(p)

    suma = sum(pesos)
    if abs(suma - 1.0) > 0.001:
        st.error(f"Los pesos suman {suma:.4f}. Deben sumar 1.0")

calcular = st.button("🌐 Obtener datos macro y calcular métricas", type="primary", disabled=abs(sum(pesos)-1.0) > 0.001)

if calcular:
    with st.spinner("Descargando datos desde FRED API y calculando métricas..."):
        data = _get("/macro", {
            "tickers": ",".join(tickers),
            "pesos": ",".join(str(p) for p in pesos),
            "periodo": periodo,
        })
else:
    data = None

if not data:
    if not calcular:
        st.info("👆 Configura pesos en el sidebar y presiona el botón para obtener datos macro.")
    st.stop()

# ── Panel de Indicadores Macro ────────────────────────────────────────────
st.markdown("### 📡 Indicadores Macroeconómicos (FRED API)")
macro_items = data["indicadores_macro"]
cols = st.columns(len(macro_items))
for i, ind in enumerate(macro_items):
    with cols[i]:
        st.metric(
            label=ind["nombre"],
            value=f"{ind['valor_actual']:.4f} {ind['unidad']}",
            help=f"Serie FRED: {ind['serie_fred']} | Actualizado: {ind['fecha_actualizacion']}",
        )

# ── Métricas comparativas ──────────────────────────────────────────────────
st.divider()
st.markdown("### 📊 Desempeño: Portafolio vs Benchmark (S&P 500)")
port = data["desempeno_portafolio"]
bench = data["desempeno_benchmark"]

col_p, col_b = st.columns(2)
with col_p:
    st.markdown("**🎯 Portafolio Óptimo**")
    st.metric("Rendimiento acumulado", f"{port['rendimiento_acumulado']*100:.2f}%")
    st.metric("Rendimiento anualizado", f"{port['rendimiento_anualizado']*100:.2f}%")
    st.metric("Volatilidad anualizada", f"{port['volatilidad_anualizada']*100:.2f}%")
    st.metric("Sharpe Ratio", f"{port['sharpe_ratio']:.4f}")
    st.metric("Máx. Drawdown", f"{port['maximo_drawdown']*100:.2f}%")

with col_b:
    st.markdown("**📈 Benchmark (S&P 500)**")
    st.metric("Rendimiento acumulado", f"{bench['rendimiento_acumulado']*100:.2f}%")
    st.metric("Rendimiento anualizado", f"{bench['rendimiento_anualizado']*100:.2f}%")
    st.metric("Volatilidad anualizada", f"{bench['volatilidad_anualizada']*100:.2f}%")
    st.metric("Sharpe Ratio", f"{bench['sharpe_ratio']:.4f}")
    st.metric("Máx. Drawdown", f"{bench['maximo_drawdown']*100:.2f}%")

# ── Alpha, Tracking Error, IR ──────────────────────────────────────────────
st.divider()
st.markdown("### 📐 Métricas de Gestión Activa")
k1, k2, k3 = st.columns(3)
k1.metric("Alpha de Jensen", f"{data['alpha_jensen']*100:.4f}%",
    help="Exceso de rendimiento sobre lo esperado por el CAPM. Alpha > 0 → el gestor agrega valor.")
k2.metric("Tracking Error", f"{data['tracking_error']*100:.2f}%",
    help="Desviación estándar de la diferencia de rendimientos portafolio - benchmark.")
k3.metric("Information Ratio", f"{data['information_ratio']:.4f}",
    help="Alpha / Tracking Error. IR > 0.5 → gestión activa eficiente.")

# ── Interpretación ─────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📚 Interpretación")
st.markdown(data.get("interpretacion", ""))
