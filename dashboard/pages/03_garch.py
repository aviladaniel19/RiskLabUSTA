"""
03_garch.py — Módulo 3: ARCH/GARCH (12%)
"""

import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data_loader import cargar_precios, calcular_rendimientos
from src.garch_models import (comparar_modelos, diagnostico_residuos,
                               pronostico_volatilidad, justificacion_heterocedasticidad)

st.set_page_config(page_title="ARCH/GARCH — RiskLabUSTA", page_icon="📉", layout="wide")
st.title("📉 Módulo 3: Modelos ARCH / GARCH")
st.markdown("**Peso en la rúbrica: 12%** — Volatilidad condicional, selección por AIC/BIC, diagnóstico.")

tickers = st.session_state.get("tickers", ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"])
periodo = st.session_state.get("periodo", "2y")

ticker_sel = st.selectbox("Selecciona un activo para modelar:", tickers)

try:
    precios = cargar_precios([ticker_sel], periodo=periodo)
    rendimientos = calcular_rendimientos(precios, "log").iloc[:, 0]
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.stop()

# ── 1. Justificación ──
st.subheader("🔍 Justificación de Heterocedasticidad Condicional")
with st.spinner("Ejecutando test de efectos ARCH..."):
    texto_just = justificacion_heterocedasticidad(rendimientos)
st.markdown(texto_just)

# ── 2. Comparación de modelos ──
st.subheader("📊 Comparación de Modelos: ARCH(1), GARCH(1,1), EGARCH(1,1)")

with st.spinner("Ajustando modelos (esto puede tardar unos segundos)..."):
    tabla, modelos = comparar_modelos(rendimientos)

st.dataframe(tabla, width="stretch")
st.markdown("""
> **Interpretación:** El modelo con menor **AIC** y **BIC** es preferido.
> AIC penaliza la complejidad menos que BIC, por lo que pueden diferir en la selección.
""")

# ── 3. Volatilidad condicional ──
st.subheader("📈 Volatilidad Condicional Estimada")

# Usar el mejor modelo por AIC
mejor_idx = tabla["AIC"].astype(float).idxmin() if not tabla.empty else 0
mejor_modelo = [m for m in modelos if m["nombre"] == mejor_idx][0] if mejor_idx else modelos[1]

fig_vol = go.Figure()
vol_cond = mejor_modelo["volatilidad_condicional"]
fig_vol.add_trace(go.Scatter(x=vol_cond.index, y=vol_cond.values,
                              name=f"Volatilidad ({mejor_modelo['nombre']})",
                              line=dict(color="#e94560", width=1.2)))
fig_vol.update_layout(title=f"Volatilidad condicional — {mejor_modelo['nombre']} — {ticker_sel}",
                       xaxis_title="Fecha", yaxis_title="Volatilidad",
                       template="plotly_white", height=400)
st.plotly_chart(fig_vol, width="stretch")

# ── 4. Diagnóstico de residuos ──
st.subheader("🔬 Diagnóstico de Residuos Estandarizados")

diag = diagnostico_residuos(mejor_modelo)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Media", f"{diag['media_residuos']:.4f}")
col2.metric("Desv. Estándar", f"{diag['std_residuos']:.4f}")
col3.metric("Asimetría", f"{diag['asimetria']:.4f}")
col4.metric("JB p-valor", f"{diag['JB_p_valor']:.4f}")

st.markdown(diag["interpretacion"])

# Gráfico de residuos
residuos = mejor_modelo["residuos_estandarizados"]
fig_res = go.Figure()
fig_res.add_trace(go.Scatter(x=residuos.index, y=residuos.values,
                              mode="lines", name="Residuos Estandarizados",
                              line=dict(color="#0f3460", width=0.8)))
fig_res.add_hline(y=0, line_dash="dash", line_color="gray")
fig_res.add_hline(y=2, line_dash="dot", line_color="red", opacity=0.5)
fig_res.add_hline(y=-2, line_dash="dot", line_color="red", opacity=0.5)
fig_res.update_layout(title="Residuos estandarizados del modelo",
                       template="plotly_white", height=350)
st.plotly_chart(fig_res, width="stretch")

# ── 5. Pronóstico de volatilidad ──
st.subheader("🔮 Pronóstico de Volatilidad")

horizonte = st.slider("Horizonte de pronóstico (días):", 5, 60, 30)
forecast_df = pronostico_volatilidad(mejor_modelo, horizonte)

fig_fc = go.Figure()
fig_fc.add_trace(go.Scatter(x=forecast_df["Día"], y=forecast_df["Volatilidad_Pronosticada"],
                              name="Volatilidad Pronosticada",
                              line=dict(color="#e94560", width=2),
                              fill="tozeroy", fillcolor="rgba(233,69,96,0.1)"))
fig_fc.update_layout(title=f"Pronóstico {horizonte} días — {mejor_modelo['nombre']}",
                      xaxis_title="Día", yaxis_title="Volatilidad diaria",
                      template="plotly_white", height=350)
st.plotly_chart(fig_fc, width="stretch")
