"""
02_rendimientos.py — Módulo 2: Rendimientos y Propiedades Empíricas (8%)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios, calcular_rendimientos
from src.returns import (rendimientos_log, rendimientos_simples,
                          estadisticas_descriptivas, tabla_pruebas_normalidad,
                          interpretar_hechos_estilizados)

st.set_page_config(page_title="Rendimientos — RiskLabUSTA", page_icon="📊", layout="wide")
st.title("📊 Módulo 2: Rendimientos y Propiedades Empíricas")
st.markdown("**Peso en la rúbrica: 8%** — Caracterización estadística de los rendimientos.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
periodo = st.session_state.get("periodo", "2y")

# ── Cargar datos ──
try:
    precios = cargar_precios(tickers, periodo=periodo)
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

# Calcular rendimientos
ret_log = rendimientos_log(precios)
ret_simple = rendimientos_simples(precios)

ticker_sel = st.selectbox("Selecciona un activo:", tickers)

# ── 1. Estadísticas descriptivas ──
st.subheader("📋 Estadísticas Descriptivas")
stats_df = estadisticas_descriptivas(ret_log)
st.dataframe(stats_df.style.format("{:.6f}"), width="stretch")

# ── 2. Histograma con curva normal ──
st.subheader("📊 Histograma con Curva Normal Superpuesta")

datos = ret_log[ticker_sel].dropna()
fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(x=datos, nbinsx=80, name="Rendimientos",
                                 marker_color="#0f3460", opacity=0.7, histnorm="probability density"))

# Curva normal superpuesta
x_norm = np.linspace(datos.min(), datos.max(), 200)
y_norm = (1 / (datos.std() * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - datos.mean()) / datos.std())**2)
fig_hist.add_trace(go.Scatter(x=x_norm, y=y_norm, name="Normal teórica",
                               line=dict(color="#e94560", width=2)))
fig_hist.update_layout(title=f"Distribución de rendimientos log de {ticker_sel}",
                        xaxis_title="Rendimiento", yaxis_title="Densidad",
                        template="plotly_white", height=400)
st.plotly_chart(fig_hist, width="stretch")

# ── 3. Gráfico Q-Q ──
st.subheader("📊 Gráfico Q-Q contra la Distribución Normal")

from scipy import stats as sp_stats
sorted_data = np.sort(datos)
theoretical = sp_stats.norm.ppf(np.linspace(0.01, 0.99, len(sorted_data)))

fig_qq = go.Figure()
fig_qq.add_trace(go.Scatter(x=theoretical, y=sorted_data, mode="markers",
                             name="Datos", marker=dict(color="#0f3460", size=3, opacity=0.5)))
# Línea de referencia
min_val = min(theoretical.min(), sorted_data.min())
max_val = max(theoretical.max(), sorted_data.max())
fig_qq.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val * datos.std() + datos.mean(),
                                                       max_val * datos.std() + datos.mean()],
                             mode="lines", name="Referencia Normal",
                             line=dict(color="#e94560", dash="dash")))
fig_qq.update_layout(title=f"Q-Q Plot de {ticker_sel}",
                      xaxis_title="Cuantiles teóricos (Normal)",
                      yaxis_title="Cuantiles observados",
                      template="plotly_white", height=400)
st.plotly_chart(fig_qq, width="stretch")

# ── 4. Boxplot ──
st.subheader("📊 Boxplot de Rendimientos")

fig_box = go.Figure()
for col in ret_log.columns:
    fig_box.add_trace(go.Box(y=ret_log[col].values, name=col))
fig_box.update_layout(title="Boxplot de rendimientos logarítmicos",
                       yaxis_title="Rendimiento", template="plotly_white", height=400)
st.plotly_chart(fig_box, width="stretch")

# ── 5. Pruebas de normalidad ──
st.subheader("🧪 Pruebas de Normalidad")
tabla_norm = tabla_pruebas_normalidad(ret_log)
st.dataframe(tabla_norm, width="stretch")

st.markdown("""
> **Interpretación:** Si el p-valor < 0.05, se rechaza H₀ de normalidad.
> En mercados financieros, los rendimientos casi siempre rechazan normalidad
> debido a **colas pesadas** y **asimetría**.
""")

# ── 6. Discusión de hechos estilizados ──
st.subheader("📝 Hechos Estilizados")
texto_he = interpretar_hechos_estilizados(ret_log[ticker_sel], ticker_sel)
st.markdown(texto_he)

# Serie temporal de rendimientos y rendimientos²
st.subheader("📊 Serie Temporal de Rendimientos y Volatilidad")
fig_ts = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=["Rendimientos", "Rendimientos² (proxy de volatilidad)"],
                        vertical_spacing=0.08)
fig_ts.add_trace(go.Scatter(x=ret_log.index, y=ret_log[ticker_sel].values,
                             name="Rendimientos", line=dict(color="#0f3460", width=0.8)), row=1, col=1)
fig_ts.add_trace(go.Scatter(x=ret_log.index, y=(ret_log[ticker_sel]**2).values,
                             name="Rendimientos²", line=dict(color="#e94560", width=0.8)), row=2, col=1)
fig_ts.update_layout(template="plotly_white", height=500, showlegend=False)
st.plotly_chart(fig_ts, width="stretch")

st.markdown("""
> El gráfico de rendimientos² evidencia el **agrupamiento de volatilidad**
> (volatility clustering): períodos de alta volatilidad tienden a seguirse entre sí.
> Este fenómeno es la base para los modelos ARCH/GARCH (Módulo 3).
""")
