"""
08_macro.py — ⭐ Módulo 8: Contexto Macroeconómico y Benchmark (8%)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios, cargar_indice, calcular_rendimientos
from src.macro_benchmark import (obtener_panel_macro, comparar_vs_benchmark,
                                  alpha_jensen, tracking_error, information_ratio,
                                  max_drawdown, tabla_desempeno, interpretacion_benchmark)
from src.markowitz import portafolio_max_sharpe
from src.api_client import obtener_rf_actual

st.set_page_config(page_title="Macro y Benchmark — RiskLabUSTA", page_icon="🌐", layout="wide")
st.title("🌐 Módulo 8: Contexto Macroeconómico y Benchmark")
st.markdown("**⭐ Peso en la rúbrica: 8%** — Datos macro vía API + comparación vs benchmark.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
benchmark_ticker = st.session_state.get("benchmark", "^GSPC")
periodo = st.session_state.get("periodo", "2y")

try:
    precios = cargar_precios(tickers, periodo=periodo)
    indice = cargar_indice(benchmark_ticker, periodo=periodo)
    rendimientos = calcular_rendimientos(precios, "log")
    ret_indice = calcular_rendimientos(indice.to_frame(), "log").iloc[:, 0]
    rf = obtener_rf_actual()
except Exception as e:
    st.error(f"❌ Error: {e}")
    rf = 0.05
    st.stop()

# ── 1. Panel Macroeconómico ──
st.subheader("🏦 Panel de Indicadores Macroeconómicos (FRED API)")

try:
    macro = obtener_panel_macro()
    cols = st.columns(len(macro))
    for i, (nombre, info) in enumerate(macro.items()):
        with cols[i]:
            st.metric(nombre, info.get("valor", "N/A"),
                     delta=f"Fecha: {info.get('fecha', '-')}")
except Exception as e:
    st.warning(f"⚠️ No se pudieron cargar datos macro: {e}")
    st.info("Configura FRED_API_KEY en tu archivo .env para habilitar este módulo.")

# ── 2. Portafolio óptimo vs Benchmark ──
st.subheader("📈 Rendimiento Acumulado: Portafolio Óptimo vs Benchmark")

# Obtener portafolio de máximo Sharpe
try:
    max_sh = portafolio_max_sharpe(rendimientos, rf)
    pesos = np.array([max_sh["pesos"].get(t, 0) for t in rendimientos.columns])

    # Rendimiento del portafolio ponderado
    ret_portafolio = (rendimientos * pesos).sum(axis=1)

    # Comparación base 100
    comparacion = comparar_vs_benchmark(ret_portafolio, ret_indice)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(x=comparacion.index, y=comparacion["Portafolio"],
                                   name="Portafolio Óptimo", line=dict(color="#e94560", width=2)))
    fig_comp.add_trace(go.Scatter(x=comparacion.index, y=comparacion["Benchmark"],
                                   name=f"Benchmark ({benchmark_ticker})",
                                   line=dict(color="#0f3460", width=2, dash="dash")))
    fig_comp.add_hline(y=100, line_dash="dot", line_color="gray", opacity=0.5)
    fig_comp.update_layout(title="Rendimiento acumulado Base 100",
                            xaxis_title="Fecha", yaxis_title="Valor (base 100)",
                            template="plotly_white", height=450)
    st.plotly_chart(fig_comp, width="stretch")
except Exception as e:
    st.error(f"Error al calcular portafolio: {e}")
    st.stop()

# ── 3. Métricas comparativas ──
st.subheader("📊 Métricas de Desempeño")

col1, col2, col3, col4 = st.columns(4)

alpha = alpha_jensen(ret_portafolio, ret_indice, rf)
te = tracking_error(ret_portafolio, ret_indice)
ir = information_ratio(ret_portafolio, ret_indice)
mdd_port = max_drawdown(ret_portafolio)

col1.metric("Alpha de Jensen", f"{alpha*100:.2f}%",
            delta="Superó al mercado" if alpha > 0 else "Subperformance")
col2.metric("Tracking Error", f"{te*100:.2f}%")
col3.metric("Information Ratio", f"{ir:.3f}")
col4.metric("Máx. Drawdown", f"{mdd_port*100:.2f}%")

# ── 4. Tabla de desempeño ──
st.subheader("📋 Tabla de Desempeño Comparativo")
desempeno = tabla_desempeno(ret_portafolio, ret_indice, rf)
st.dataframe(desempeno, width="stretch")

# ── 5. Interpretación ──
st.subheader("📝 Interpretación")
texto = interpretacion_benchmark(ret_portafolio, ret_indice, rf)
st.markdown(texto)

# ── 6. Drawdown chart ──
st.subheader("📉 Drawdown del Portafolio")

acumulado = (1 + ret_portafolio).cumprod()
pico = acumulado.cummax()
drawdown_serie = (acumulado - pico) / pico

fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(x=drawdown_serie.index, y=drawdown_serie.values,
                              fill="tozeroy", fillcolor="rgba(233,69,96,0.15)",
                              line=dict(color="#e94560", width=1),
                              name="Drawdown"))
fig_dd.update_layout(title="Máximo Drawdown del portafolio óptimo",
                      xaxis_title="Fecha", yaxis_title="Drawdown (%)",
                      template="plotly_white", height=350)
st.plotly_chart(fig_dd, width="stretch")
