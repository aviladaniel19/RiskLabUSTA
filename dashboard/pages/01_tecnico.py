"""
01_tecnico.py — Módulo 1: Análisis Técnico (12%)

Indicadores: SMA, EMA, RSI, MACD, Bandas de Bollinger, Oscilador Estocástico.
Gráficos interactivos con Plotly. Selector dinámico de activos.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios
from src.indicators import sma, ema, rsi, macd, bollinger_bands, estocastico_desde_close

st.set_page_config(page_title="Análisis Técnico — RiskLabUSTA", page_icon="📈", layout="wide")
st.title("📈 Módulo 1: Análisis Técnico")
st.markdown("**Peso en la rúbrica: 12%** — Indicadores técnicos interactivos con datos en tiempo real.")

# ── Sidebar controls ──
tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
periodo = st.session_state.get("periodo", "2y")

# Selector dinámico de ticker individual
ticker_sel = st.selectbox("Selecciona un activo para analizar:", tickers)

# Nuevo ticker dinámico
nuevo_ticker = st.text_input("🔍 O ingresa un nuevo ticker:", placeholder="Ej: META, NVDA, JPM")
if nuevo_ticker:
    ticker_sel = nuevo_ticker.strip().upper()

# Parámetros ajustables
col1, col2, col3 = st.columns(3)
with col1:
    sma_periodo = st.slider("Período SMA", 5, 200, 20)
with col2:
    ema_periodo = st.slider("Período EMA", 5, 200, 20)
with col3:
    rsi_periodo = st.slider("Período RSI", 5, 30, 14)

# ── Cargar datos ──
try:
    precios_df = cargar_precios([ticker_sel], periodo=periodo)
    precios = precios_df.iloc[:, 0]
except Exception as e:
    st.error(f"❌ Error al descargar datos de {ticker_sel}: {e}")
    st.stop()

# ── 1. Gráfico de precios con SMA y EMA ──
st.subheader("📊 Precios con Medias Móviles")

fig_precios = go.Figure()
fig_precios.add_trace(go.Scatter(x=precios.index, y=precios.values,
                                  name="Precio", line=dict(color="#1a1a2e", width=1.5)))
fig_precios.add_trace(go.Scatter(x=precios.index, y=sma(precios, sma_periodo).values,
                                  name=f"SMA({sma_periodo})", line=dict(color="#e94560", width=1.2, dash="dot")))
fig_precios.add_trace(go.Scatter(x=precios.index, y=ema(precios, ema_periodo).values,
                                  name=f"EMA({ema_periodo})", line=dict(color="#0f3460", width=1.2, dash="dash")))
fig_precios.update_layout(
    title=f"Precio de {ticker_sel} con Medias Móviles",
    xaxis_title="Fecha", yaxis_title="Precio (USD)",
    template="plotly_white", height=450,
    xaxis=dict(rangeslider=dict(visible=True)),
)
st.plotly_chart(fig_precios, width="stretch")

with st.expander("ℹ️ ¿Qué son las Medias Móviles?"):
    st.markdown("""
    - **SMA (Simple Moving Average):** Promedio aritmético de los últimos N precios. Suaviza la serie para identificar tendencias.
    - **EMA (Exponential Moving Average):** Promedio ponderado exponencialmente. Da más peso a los datos recientes, reacciona más rápido a cambios.
    - **Uso:** Cuando la EMA cruza la SMA de abajo hacia arriba → señal alcista (Golden Cross). De arriba hacia abajo → señal bajista (Death Cross).
    """)

# ── 2. RSI ──
st.subheader("📊 RSI (Relative Strength Index)")

rsi_vals = rsi(precios, rsi_periodo)
fig_rsi = go.Figure()
fig_rsi.add_trace(go.Scatter(x=rsi_vals.index, y=rsi_vals.values,
                              name="RSI", line=dict(color="#e94560")))
fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecompra (70)")
fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobreventa (30)")
fig_rsi.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.05)
fig_rsi.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.05)
fig_rsi.update_layout(
    title=f"RSI({rsi_periodo}) de {ticker_sel}",
    yaxis=dict(range=[0, 100]), template="plotly_white", height=300,
)
st.plotly_chart(fig_rsi, width="stretch")

with st.expander("ℹ️ ¿Qué es el RSI?"):
    st.markdown("""
    - **RSI** mide la velocidad y magnitud de los cambios de precio recientes.
    - RSI > 70 → El activo está **sobrecomprado** (posible corrección a la baja).
    - RSI < 30 → El activo está **sobrevendido** (posible rebote al alza).
    - Rango: 0 a 100.
    """)

# ── 3. MACD ──
st.subheader("📊 MACD (Moving Average Convergence Divergence)")

macd_df = macd(precios)
fig_macd = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.6, 0.4],
                         vertical_spacing=0.05)
fig_macd.add_trace(go.Scatter(x=precios.index, y=precios.values,
                               name="Precio", line=dict(color="#1a1a2e")), row=1, col=1)
fig_macd.add_trace(go.Scatter(x=macd_df.index, y=macd_df["MACD"].values,
                               name="MACD", line=dict(color="#e94560")), row=2, col=1)
fig_macd.add_trace(go.Scatter(x=macd_df.index, y=macd_df["Signal"].values,
                               name="Signal", line=dict(color="#0f3460", dash="dash")), row=2, col=1)
colors = ["green" if v >= 0 else "red" for v in macd_df["Histograma"].values]
fig_macd.add_trace(go.Bar(x=macd_df.index, y=macd_df["Histograma"].values,
                           name="Histograma", marker_color=colors), row=2, col=1)
fig_macd.update_layout(title=f"MACD de {ticker_sel}", template="plotly_white", height=500)
st.plotly_chart(fig_macd, width="stretch")

with st.expander("ℹ️ ¿Qué es el MACD?"):
    st.markdown("""
    - **MACD** = EMA(12) - EMA(26). Mide la diferencia entre dos medias exponenciales.
    - **Línea de señal** = EMA(9) del MACD.
    - **Histograma** = MACD - Signal. Positivo → momentum alcista.
    - **Señal de compra:** MACD cruza Signal de abajo hacia arriba.
    - **Señal de venta:** MACD cruza Signal de arriba hacia abajo.
    """)

# ── 4. Bandas de Bollinger ──
st.subheader("📊 Bandas de Bollinger")

bb = bollinger_bands(precios)
fig_bb = go.Figure()
fig_bb.add_trace(go.Scatter(x=precios.index, y=bb["Superior"].values,
                              name="Banda Superior", line=dict(color="rgba(233,69,96,0.3)")))
fig_bb.add_trace(go.Scatter(x=precios.index, y=bb["Inferior"].values,
                              name="Banda Inferior", line=dict(color="rgba(233,69,96,0.3)"),
                              fill="tonexty", fillcolor="rgba(233,69,96,0.05)"))
fig_bb.add_trace(go.Scatter(x=precios.index, y=bb["Media"].values,
                              name="Media (SMA 20)", line=dict(color="#e94560", dash="dot")))
fig_bb.add_trace(go.Scatter(x=precios.index, y=precios.values,
                              name="Precio", line=dict(color="#1a1a2e", width=1.5)))
fig_bb.update_layout(title=f"Bandas de Bollinger de {ticker_sel}",
                      template="plotly_white", height=450)
st.plotly_chart(fig_bb, width="stretch")

with st.expander("ℹ️ ¿Qué son las Bandas de Bollinger?"):
    st.markdown("""
    - **Banda Media:** SMA de 20 períodos.
    - **Banda Superior:** Media + 2σ.
    - **Banda Inferior:** Media - 2σ.
    - Precio tocando la banda superior → posible sobrecompra.
    - Precio tocando la banda inferior → posible sobreventa.
    - Bandas estrechas → baja volatilidad, posible movimiento fuerte próximo.
    """)

# ── 5. Oscilador Estocástico ──
st.subheader("📊 Oscilador Estocástico")

est = estocastico_desde_close(precios)
fig_est = go.Figure()
fig_est.add_trace(go.Scatter(x=est.index, y=est["%K"].values,
                              name="%K", line=dict(color="#e94560")))
fig_est.add_trace(go.Scatter(x=est.index, y=est["%D"].values,
                              name="%D", line=dict(color="#0f3460", dash="dash")))
fig_est.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Sobrecompra (80)")
fig_est.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Sobreventa (20)")
fig_est.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.05)
fig_est.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.05)
fig_est.update_layout(title=f"Oscilador Estocástico de {ticker_sel}",
                       yaxis=dict(range=[0, 100]), template="plotly_white", height=300)
st.plotly_chart(fig_est, width="stretch")

with st.expander("ℹ️ ¿Qué es el Oscilador Estocástico?"):
    st.markdown("""
    - **%K** mide la posición del cierre actual respecto al rango de precios de N períodos.
    - **%D** es la media móvil de %K (suavizado).
    - %K > 80 → zona de sobrecompra.
    - %K < 20 → zona de sobreventa.
    - **Señal de compra:** %K cruza %D hacia arriba en zona de sobreventa.
    - **Señal de venta:** %K cruza %D hacia abajo en zona de sobrecompra.
    """)
