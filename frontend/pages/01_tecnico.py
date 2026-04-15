"""
01_tecnico.py — Módulo 1: Análisis Técnico e Indicadores.
Peso en rúbrica: 10%

Consume el endpoint GET /indicadores/{ticker} del backend FastAPI.
Visualiza SMA, EMA, RSI, MACD, Bandas de Bollinger y Oscilador Estocástico.
"""

import os
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import requests

# ── Helpers compartidos del app principal ──────────────────────────────────
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=3600, show_spinner=False)
def _get(endpoint, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", params=params or {}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


# ── Configuración de página ────────────────────────────────────────────────
st.set_page_config(page_title="Análisis Técnico — RiskLab", layout="wide")
st.title("📈 Módulo 1 — Análisis Técnico e Indicadores")
st.markdown("Visualización interactiva de indicadores técnicos con datos en tiempo real desde Yahoo Finance.")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_tec")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    ticker_sel = st.selectbox("Activo a analizar", tickers)
    periodo = st.selectbox("Período", ["1y", "2y", "3y"], index=1, key="periodo_tec")
    st.divider()
    mostrar_sma20 = st.checkbox("SMA 20", value=True)
    mostrar_sma50 = st.checkbox("SMA 50", value=True)
    mostrar_ema20 = st.checkbox("EMA 20", value=True)
    mostrar_bb = st.checkbox("Bandas de Bollinger", value=True)
    mostrar_rsi = st.checkbox("RSI (14)", value=True)
    mostrar_macd = st.checkbox("MACD", value=True)
    mostrar_esto = st.checkbox("Oscilador Estocástico", value=False)

# ── Carga de datos ─────────────────────────────────────────────────────────
with st.spinner(f"Descargando indicadores de {ticker_sel}..."):
    data = _get(f"/indicadores/{ticker_sel}", {"periodo": periodo})

if not data:
    st.error("No se obtuvieron datos. Verifica el ticker y que el backend esté corriendo.")
    st.stop()

df = pd.DataFrame(data["indicadores"])
df["fecha"] = pd.to_datetime(df["fecha"])

# ══════════════════════════════════════════════
# GRÁFICO 1: Precio + SMA/EMA/Bollinger
# ══════════════════════════════════════════════
n_rows = 1 + mostrar_rsi + mostrar_macd + mostrar_esto
fig = make_subplots(
    rows=n_rows, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.5] + [0.2] * (n_rows - 1),
    subplot_titles=(
        [f"{ticker_sel} — Precio y Medias Móviles"]
        + (["RSI (14)"] if mostrar_rsi else [])
        + (["MACD"] if mostrar_macd else [])
        + (["Estocástico"] if mostrar_esto else [])
    ),
)

# Precio
fig.add_trace(
    go.Scatter(x=df["fecha"], y=df["precio"], name="Precio", line=dict(color="#6366f1", width=1.5)),
    row=1, col=1,
)

if mostrar_sma20:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["sma_20"], name="SMA 20", line=dict(color="#f59e0b", dash="dash")), row=1, col=1)
if mostrar_sma50:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["sma_50"], name="SMA 50", line=dict(color="#10b981", dash="dot")), row=1, col=1)
if mostrar_ema20:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["ema_20"], name="EMA 20", line=dict(color="#f43f5e", dash="dashdot")), row=1, col=1)

if mostrar_bb and "bb_superior" in df.columns:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["bb_superior"], name="BB Superior", line=dict(color="#94a3b8", dash="dash"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["bb_inferior"], name="BB Inferior", line=dict(color="#94a3b8", dash="dash"), fill="tonexty", fillcolor="rgba(148,163,184,0.1)"), row=1, col=1)

# Filas adicionales
fila_actual = 2
if mostrar_rsi:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["rsi_14"], name="RSI 14", line=dict(color="#8b5cf6")), row=fila_actual, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=fila_actual, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=fila_actual, col=1)
    fila_actual += 1

if mostrar_macd:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["macd"], name="MACD", line=dict(color="#3b82f6")), row=fila_actual, col=1)
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["macd_signal"], name="Signal", line=dict(color="#ef4444")), row=fila_actual, col=1)
    fig.add_trace(go.Bar(x=df["fecha"], y=df["macd_hist"], name="Histograma", marker_color="#94a3b8", opacity=0.5), row=fila_actual, col=1)
    fila_actual += 1

if mostrar_esto:
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["estocastico_k"], name="%K", line=dict(color="#f97316")), row=fila_actual, col=1)
    fig.add_trace(go.Scatter(x=df["fecha"], y=df["estocastico_d"], name="%D", line=dict(color="#a855f7")), row=fila_actual, col=1)
    fig.add_hline(y=80, line_dash="dash", line_color="red", row=fila_actual, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="green", row=fila_actual, col=1)

fig.update_layout(height=200 + 250 * n_rows, template="plotly_dark", legend=dict(orientation="h", y=-0.05), hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# ── Panel explicativo ──────────────────────────────────────────────────────
with st.expander("📖 Interpretación de indicadores"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**SMA / EMA:**
Medias móviles que suavizan el precio. La EMA da más peso a datos recientes.
- Precio > SMA → tendencia alcista
- Cruce SMA20 sobre SMA50 → *Golden Cross* (señal de compra)

**RSI (14):**
Mide la fuerza relativa del movimiento.
- RSI > 70 → sobrecompra (posible corrección)
- RSI < 30 → sobreventa (posible rebote)
        """)
    with col2:
        st.markdown("""
**MACD:**
Diferencia entre EMA 12 y EMA 26. La señal es una EMA 9 del MACD.
- MACD cruza Signal hacia arriba → señal de compra
- Histograma positivo → momentum alcista

**Bandas de Bollinger:**
Media ± 2 desviaciones estándar. Miden la volatilidad relativa.
- Precio toca banda superior → sobrecompra relativa
- Precio toca banda inferior → sobreventa relativa
        """)

# ── KPIs ──────────────────────────────────────────────────────────────────
st.divider()
k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Último precio", f"${data['ultimo_precio']:,.2f}")
k2.metric("📊 RSI actual", f"{data.get('ultimo_rsi', 0):.1f}" if data.get('ultimo_rsi') else "N/D")
k3.metric("📈 MACD actual", f"{data.get('ultimo_macd', 0):.4f}" if data.get('ultimo_macd') else "N/D")
k4.metric("🔢 Observaciones", f"{data['n_observaciones']:,}")
