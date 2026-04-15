"""
07_senales.py — ⭐ Módulo 7: Señales y Alertas Automáticas (10%)
"""

import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios
from src.signals import generar_todas_las_senales, resumen_senales

st.set_page_config(page_title="Señales — RiskLabUSTA", page_icon="⚡", layout="wide")
st.title("⚡ Módulo 7: Señales y Alertas Automáticas")
st.markdown("**⭐ Peso en la rúbrica: 10%** — Señales de compra/venta basadas en indicadores técnicos.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
periodo = st.session_state.get("periodo", "2y")

# ── Umbrales configurables ──
st.sidebar.markdown("### ⚙️ Configuración de umbrales")
rsi_sobrecompra = st.sidebar.slider("RSI Sobrecompra", 60, 90, 70)
rsi_sobreventa = st.sidebar.slider("RSI Sobreventa", 10, 40, 30)

try:
    precios = cargar_precios(tickers, periodo=periodo)
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

# ── Panel de señales para todos los activos ──
st.subheader("🚦 Panel de Alertas por Activo")

for ticker in tickers:
    if ticker not in precios.columns:
        continue

    serie = precios[ticker].dropna()
    if len(serie) < 200:
        st.warning(f"⚠️ {ticker}: datos insuficientes para todos los indicadores.")
        continue

    resumen = resumen_senales(serie, ticker)

    # Tarjeta del activo
    with st.container():
        col_header, col_veredicto = st.columns([3, 1])
        with col_header:
            st.markdown(f"### {ticker}")
        with col_veredicto:
            st.markdown(f"## {resumen['veredicto']}")

        # Tarjetas de señales tipo semáforo
        cols = st.columns(5)
        for i, senal in enumerate(resumen["senales"]):
            with cols[i]:
                bg_color = {
                    "green": "#d4edda",
                    "red": "#f8d7da",
                    "gray": "#e9ecef"
                }.get(senal["color"], "#e9ecef")

                text_color = {
                    "green": "#155724",
                    "red": "#721c24",
                    "gray": "#495057"
                }.get(senal["color"], "#495057")

                st.markdown(f"""
                <div style="background:{bg_color}; padding:12px; border-radius:10px;
                            text-align:center; border: 1px solid {text_color}20;">
                    <div style="font-size:24px;">{senal['icono']}</div>
                    <div style="font-size:11px; font-weight:700; color:{text_color};
                                margin-top:4px;">{senal['indicador']}</div>
                    <div style="font-size:13px; font-weight:800; color:{text_color};">
                        {senal['señal']}</div>
                    <div style="font-size:10px; color:{text_color}80; margin-top:2px;">
                        {senal['valor']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Texto interpretativo expandible
        with st.expander(f"📝 Detalle de señales de {ticker}"):
            for senal in resumen["senales"]:
                st.markdown(senal["texto"])
                st.markdown("---")

        st.markdown("---")

# ── Resumen global ──
st.subheader("📊 Resumen Global de Señales")

import pandas as pd
tabla_global = []
for ticker in tickers:
    if ticker not in precios.columns:
        continue
    serie = precios[ticker].dropna()
    if len(serie) < 200:
        continue
    res = resumen_senales(serie, ticker)
    fila = {"Activo": ticker, "Veredicto": res["veredicto"],
            "Compra": res["compra"], "Venta": res["venta"]}
    for s in res["senales"]:
        fila[s["indicador"]] = f"{s['icono']} {s['señal']}"
    tabla_global.append(fila)

if tabla_global:
    st.dataframe(pd.DataFrame(tabla_global).set_index("Activo"), width="stretch")
