"""
07_senales.py — Módulo 7: Señales y Alertas Automáticas.
Peso en rúbrica: 7%

Consume GET /alertas?tickers=...
"""

import os
import streamlit as st
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=900, show_spinner=False)  # Cache 15min — señales cambian más seguido
def _get(endpoint, params=None):
    try:
        r = requests.get(f"{BACKEND_URL}{endpoint}", params=params or {}, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


st.set_page_config(page_title="Señales — RiskLab", layout="wide")
st.title("⚡ Módulo 7 — Señales y Alertas Automáticas")
st.markdown("Panel semáforo con señales de compra/venta automáticas basadas en 5 indicadores técnicos.")

with st.sidebar:
    tickers_raw = st.text_input("Tickers", value="AAPL,MSFT,AMZN,TSLA,GOOG", key="tickers_sen")
    tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]
    periodo = st.selectbox("Período", ["6mo", "1y", "2y"], index=1, key="periodo_sen")
    st.divider()
    st.markdown("### ⚙️ Umbrales configurables")
    rsi_sobrecompra = st.slider("RSI Sobrecompra", 60, 80, 70)
    rsi_sobreventa = st.slider("RSI Sobreventa", 20, 40, 30)
    esto_sobrecompra = st.slider("Estocástico Sobrecompra", 70, 90, 80)
    esto_sobreventa = st.slider("Estocástico Sobreventa", 10, 30, 20)

with st.spinner("Calculando señales de mercado..."):
    data = _get("/alertas", {"tickers": ",".join(tickers), "periodo": periodo})

if not data:
    st.error("Error al calcular señales.")
    st.stop()

st.caption(f"🕒 Actualizado: {data.get('timestamp', 'N/D')}")
st.divider()

# ── COLOR MAP ──────────────────────────────────────────────────────────────
SENAL_COLOR = {
    "COMPRAR": "🟢",
    "VENDER": "🔴",
    "MANTENER": "🟡",
    "NEUTRAL": "⚪",
    "ERROR": "❌",
}

# ── Panel de tarjetas semáforo ─────────────────────────────────────────────
st.markdown("### 🚦 Panel de Alertas por Activo")

alertas = data["alertas"]
cols_por_fila = min(len(alertas), 3)
for i in range(0, len(alertas), cols_por_fila):
    grupo = alertas[i:i + cols_por_fila]
    cols = st.columns(len(grupo))
    for j, alerta in enumerate(grupo):
        with cols[j]:
            senal = alerta["senal_global"]
            emoji = SENAL_COLOR.get(senal, "⚪")

            st.markdown(
                f"""
                <div style="
                    border: 2px solid {'#22c55e' if senal=='COMPRAR' else '#ef4444' if senal=='VENDER' else '#f59e0b'};
                    border-radius: 12px;
                    padding: 16px;
                    text-align: center;
                    background: rgba(255,255,255,0.03);
                    margin-bottom: 8px;
                ">
                    <h2 style="margin:0">{alerta['ticker']}</h2>
                    <h1 style="margin:4px 0;font-size:2.5rem">{emoji}</h1>
                    <h3 style="margin:0;color:{'#22c55e' if senal=='COMPRAR' else '#ef4444' if senal=='VENDER' else '#f59e0b'}">{senal}</h3>
                    <p style="font-size:0.8rem;margin:4px 0">Precio: ${alerta.get('ultimo_precio', 0):,.2f}</p>
                    <p style="font-size:0.75rem;color:#94a3b8">RSI: {alerta.get('rsi_actual', 'N/D')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Detalle por indicador ──────────────────────────────────────────────────
st.divider()
st.markdown("### 🔍 Detalle por Indicador")

for alerta in alertas:
    with st.expander(f"{SENAL_COLOR.get(alerta['senal_global'],'⚪')} {alerta['ticker']} — Detalle"):
        c1, c2, c3, c4, c5 = st.columns(5)
        indicadores = [
            ("MACD", alerta.get("macd_senal", "N/D")),
            ("RSI", alerta.get("rsi_senal", "N/D")),
            ("Bollinger", alerta.get("bollinger_senal", "N/D")),
            ("Cruce Medias", alerta.get("cruce_medias", "N/D")),
            ("Estocástico", alerta.get("estocastico_senal", "N/D")),
        ]
        for col, (nombre, val) in zip([c1, c2, c3, c4, c5], indicadores):
            emoji = SENAL_COLOR.get(val, "⚪")
            col.markdown(f"**{nombre}**\n\n{emoji} {val}")

        st.info(alerta.get("texto_interpretativo", ""))

# ── Explicación de señales ─────────────────────────────────────────────────
with st.expander("📖 ¿Cómo se calculan las señales?"):
    st.markdown(f"""
| Indicador | Señal COMPRAR | Señal VENDER |
|-----------|--------------|-------------|
| **MACD** | MACD cruza Signal hacia arriba | MACD cruza Signal hacia abajo |
| **RSI** | RSI < {rsi_sobreventa} (sobreventa) | RSI > {rsi_sobrecompra} (sobrecompra) |
| **Bollinger** | Precio toca banda inferior | Precio toca banda superior |
| **Cruce Medias** | SMA20 > SMA50 (Golden Cross) | SMA20 < SMA50 (Death Cross) |
| **Estocástico** | %K < {esto_sobreventa} y sube | %K > {esto_sobrecompra} y baja |

La **señal global** es la moda de las 5 señales individuales.
> ⚠️ Las señales son informativas. No constituyen asesoría financiera.
    """)
