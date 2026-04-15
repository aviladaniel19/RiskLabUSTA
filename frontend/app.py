"""
app.py — Punto de entrada del Frontend Streamlit.

Este archivo configura la página, define el helper de llamadas HTTP al backend
y muestra la página de bienvenida / portafolio activo.

ARQUITECTURA:
  - El frontend NUNCA importa src/ directamente.
  - Toda la lógica de cálculo vive en el backend FastAPI.
  - Streamlit solo hace: UI + llamadas HTTP + visualizaciones Plotly.

VARIABLE DE ENTORNO:
  BACKEND_URL — URL del backend FastAPI.
    - Local:  http://localhost:8000
    - Docker: http://backend:8000  (resuelto por la red interna de Docker)
"""

import os
import requests
import streamlit as st

# ── Configuración de página ────────────────────────────────────────────────
st.set_page_config(
    page_title="RiskLab USTA — Tablero de Riesgo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── URL del backend (inyectada como variable de entorno en Docker) ──────────
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS HTTP — Todas las páginas usan estas funciones
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def api_get(endpoint: str, params: dict = None) -> dict | None:
    """
    Llamada GET al backend FastAPI con manejo de errores.

    Parámetros
    ----------
    endpoint : str
        Ruta del endpoint, ej: "/precios/AAPL"
    params : dict, optional
        Query parameters, ej: {"periodo": "2y"}

    Retorna
    -------
    dict con la respuesta JSON, o None si hubo error.

    El decorador @st.cache_data cachea la respuesta durante 1 hora,
    evitando llamadas repetidas a las APIs externas.
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params or {}, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            st.error(f"❌ Ticker no encontrado. Verifica que sea un símbolo válido de Yahoo Finance.")
        elif resp.status_code == 422:
            errores = resp.json().get("errores", [])
            for e in errores:
                st.error(f"❌ Campo `{e['campo']}`: {e['mensaje']}")
        elif resp.status_code == 503:
            st.warning("⚠️ El servicio externo (Yahoo Finance / FRED) no respondió. Intenta nuevamente.")
        else:
            st.error(f"Error {resp.status_code}: {resp.text[:200]}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"🔌 No se pudo conectar al backend en `{BACKEND_URL}`. "
            "Verifica que el servidor FastAPI esté corriendo con:\n"
            "`uvicorn app.main:app --reload`"
        )
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ El backend tardó demasiado en responder. Intenta de nuevo.")
        return None


def api_post(endpoint: str, body: dict) -> dict | None:
    """
    Llamada POST al backend FastAPI.
    No se cachea porque los parámetros del body pueden variar.
    """
    url = f"{BACKEND_URL}{endpoint}"
    try:
        resp = requests.post(url, json=body, timeout=60)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 422:
            errores = resp.json().get("errores", [])
            for e in errores:
                st.error(f"❌ Campo `{e['campo']}`: {e['mensaje']}")
        else:
            st.error(f"Error {resp.status_code}: {resp.text[:300]}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"🔌 No se pudo conectar al backend en `{BACKEND_URL}`.")
        return None


def verificar_backend() -> bool:
    """Verifica que el backend FastAPI esté operativo."""
    try:
        resp = requests.get(f"{BACKEND_URL}/", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Configuración global del portafolio
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://www.usta.edu.co/images/logo-usta.png", width=120)
    st.markdown("## 📊 RiskLab USTA")
    st.caption("Tablero Interactivo de Riesgo Financiero")
    st.divider()

    # Estado del backend
    backend_ok = verificar_backend()
    if backend_ok:
        st.success("🟢 Backend conectado")
    else:
        st.error("🔴 Backend desconectado")
        st.code("uvicorn app.main:app --reload")

    st.divider()

    # ── Configuración global del portafolio ───────────────────────────────
    st.markdown("### ⚙️ Configuración")

    tickers_input = st.text_input(
        "Tickers del portafolio",
        value="AAPL,MSFT,AMZN,TSLA,GOOG",
        help="Ingresa los tickers separados por coma. Se normalizan a mayúsculas.",
        key="tickers_global",
    )

    periodo = st.selectbox(
        "Período histórico",
        options=["1y", "2y", "3y", "5y"],
        index=1,
        key="periodo_global",
    )

    nivel_confianza = st.slider(
        "Nivel de confianza (VaR)",
        min_value=0.90,
        max_value=0.99,
        value=0.95,
        step=0.01,
        format="%.2f",
        key="confianza_global",
    )

    st.divider()
    st.caption(f"🔗 Backend: `{BACKEND_URL}`")
    st.caption("📖 [Ver documentación API](/docs)")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA PRINCIPAL — Bienvenida y resumen del portafolio
# ══════════════════════════════════════════════════════════════════════════════

st.title("📊 RiskLab USTA — Tablero de Riesgo Financiero")
st.markdown(
    "Sistema de análisis cuantitativo de riesgo de portafolios de renta variable. "
    "Usa el menú lateral para navegar entre los 8 módulos analíticos."
)

if not backend_ok:
    st.warning(
        "⚠️ El backend FastAPI no está disponible. "
        "Inicia el servidor antes de usar el tablero."
    )
    st.stop()

# Parsear tickers del sidebar
tickers_lista = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if len(tickers_lista) < 2:
    st.info("ℹ️ Ingresa al menos 2 tickers en el sidebar para comenzar el análisis.")
    st.stop()

# Mostrar resumen de activos
with st.spinner("Cargando información de activos..."):
    data = api_get("/activos", {"tickers": ",".join(tickers_lista)})

if data:
    st.markdown(f"### 🗂️ Portafolio configurado — {data['total']} activos")
    cols = st.columns(min(len(data["activos"]), 5))
    for i, activo in enumerate(data["activos"]):
        with cols[i % 5]:
            st.metric(
                label=activo["ticker"],
                value=activo["nombre"][:20] + ("…" if len(activo["nombre"]) > 20 else ""),
                delta=activo["sector"],
            )

    st.divider()
    st.info(
        f"**Benchmark:** {data['benchmark']} (S&P 500) | "
        f"**Período:** {periodo} | "
        f"**Nivel confianza VaR:** {nivel_confianza:.0%}"
    )

    st.markdown("### 📌 Navegación")
    st.markdown(
        """
        | Módulo | Descripción | Peso Rúbrica |
        |--------|-------------|-------------|
        | 📈 **01 Análisis Técnico** | SMA, EMA, RSI, MACD, Bollinger, Estocástico | 10% |
        | 📉 **02 Rendimientos** | Estadísticas, Jarque-Bera, Shapiro-Wilk, hechos estilizados | 6% |
        | 🌊 **03 ARCH/GARCH** | Volatilidad condicional, AIC/BIC, pronóstico | 10% |
        | 🛡️ **04 CAPM y Beta** | Riesgo sistemático, Rf desde FRED API | 6% |
        | ⚠️ **05 VaR y CVaR** | Paramétrico, Histórico, Montecarlo (10k sim.) | 10% |
        | 🎯 **06 Markowitz** | Frontera eficiente, mínima varianza, máx. Sharpe | 10% |
        | ⚡ **07 Señales** | Panel semáforo automático por indicador | 7% |
        | 🌍 **08 Macro y Benchmark** | FRED API + Alpha Jensen + Tracking Error | 6% |
        """
    )
