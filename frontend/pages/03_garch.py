"""
03_garch.py — Módulo 3: Modelos ARCH/GARCH de Volatilidad Condicional.
Peso en rúbrica: 10%

Consume GET /garch/{ticker}.
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


st.set_page_config(page_title="GARCH — RiskLab", layout="wide")
st.title("🌊 Módulo 3 — Modelos ARCH/GARCH de Volatilidad Condicional")
st.markdown(
    "Modela la heterocedasticidad condicional de los rendimientos. "
    "Compara ARCH(1), GARCH(1,1) y EGARCH(1,1) por AIC/BIC."
)

with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_garch")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    ticker_sel = st.selectbox("Activo a modelar", tickers, key="ticker_garch")
    periodo = st.selectbox("Período", ["2y", "3y", "5y"], index=0, key="periodo_garch")

with st.spinner(f"Ajustando modelos GARCH para {ticker_sel}... (puede tomar 30-60 seg.)"):
    data = _get(f"/garch/{ticker_sel}", {"periodo": periodo})

if not data:
    st.error("Error al ajustar modelos GARCH. Verifica el ticker.")
    st.stop()

# ── Justificación ─────────────────────────────────────────────────────────
with st.expander("📖 ¿Por qué modelar volatilidad condicional?"):
    st.markdown("""
Los rendimientos financieros presentan **agrupamiento de volatilidad** (*volatility clustering*):
períodos de alta volatilidad tienden a seguirse. Esto viola el supuesto de varianza constante (homocedasticidad).

Los modelos ARCH/GARCH capturan este fenómeno modelando la varianza condicional:
- **ARCH(1):** σ²_t = ω + α·ε²_{t-1}
- **GARCH(1,1):** σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}  ← más parsimonioso
- **EGARCH(1,1):** captura el **efecto apalancamiento** (caídas → mayor volatilidad que subidas)
    """)

# ── Tabla comparativa AIC/BIC ──────────────────────────────────────────────
st.markdown("### 📊 Comparación de Modelos (AIC/BIC)")
modelos = data["modelos_comparados"]
df_modelos = pd.DataFrame(modelos)

mejor = df_modelos.loc[df_modelos["aic"].idxmin(), "nombre"] if not df_modelos.empty else "N/D"

# Destacar el mejor modelo
def highlight_mejor(row):
    if row["es_mejor"]:
        return ["background-color: #14532d; color: white"] * len(row)
    return [""] * len(row)

if not df_modelos.empty:
    cols_mostrar = ["nombre", "log_likelihood", "aic", "bic", "volatilidad_anualizada"]
    st.dataframe(
        df_modelos[cols_mostrar].rename(columns={
            "nombre": "Modelo",
            "log_likelihood": "Log-Likelihood",
            "aic": "AIC",
            "bic": "BIC",
            "volatilidad_anualizada": "Vol. Anualizada",
        }).style.apply(highlight_mejor, axis=1),
        use_container_width=True,
    )
    st.success(f"✅ **Mejor modelo por AIC:** {mejor}")

# ── Pronóstico de volatilidad ──────────────────────────────────────────────
st.markdown("### 🔮 Pronóstico de Volatilidad (próximos 10 días)")
pronostico = data.get("pronostico_volatilidad", [])
if pronostico:
    dias = list(range(1, len(pronostico) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dias, y=[v * 100 for v in pronostico],
        mode="lines+markers",
        name="Volatilidad pronosticada (%)",
        line=dict(color="#f59e0b", width=2),
        marker=dict(size=8),
    ))
    fig.update_layout(
        title=f"Pronóstico de Volatilidad — {mejor}",
        xaxis_title="Días hacia adelante",
        yaxis_title="Volatilidad diaria (%)",
        template="plotly_dark",
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Diagnóstico de residuos ────────────────────────────────────────────────
st.markdown("### 🔬 Diagnóstico de Residuos Estandarizados")
jb = data.get("jarque_bera_residuos", {})
col1, col2, col3 = st.columns(3)
col1.metric("JB Estadístico", f"{jb.get('estadístico', 0):.4f}")
col2.metric("p-valor", f"{jb.get('p_valor', 0):.6f}")
with col3:
    if jb.get("es_normal"):
        st.success("Residuos aproximadamente normales ✅")
    else:
        st.warning("Residuos con colas pesadas (esperado en finanzas) ⚠️")

st.caption(jb.get("interpretación", ""))
