"""
app.py — Aplicación principal del tablero RiskLabUSTA.

Ejecutar con:
    streamlit run dashboard/app.py
"""

import streamlit as st
import sys
import os

# Agregar la raíz del proyecto al path para importar src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Configuración de la página ──
st.set_page_config(
    page_title="RiskLabUSTA — Tablero de Riesgo Financiero",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos CSS personalizados ──
st.markdown("""
<style>
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(90deg, #e94560, #f5a623);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .main-header p {
        color: rgba(255,255,255,0.6);
        margin-top: 0.3rem;
        font-size: 0.95rem;
    }
    /* Métricas */
    .stMetric {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: rgba(255,255,255,0.85);
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar con configuración global ──
with st.sidebar:
    st.markdown("## 📊 RiskLabUSTA")
    st.markdown("---")

    # Selector de tickers
    tickers_default = "AAPL, MSFT, GOOGL, AMZN, TSLA"
    tickers_input = st.text_input(
        "🏷️ Tickers (separados por coma)",
        value=tickers_default,
        help="Ingresa los tickers de Yahoo Finance separados por coma"
    )
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    st.markdown("---")

    # Selector de benchmark
    benchmark = st.selectbox(
        "📈 Benchmark (índice de referencia)",
        options=["^GSPC", "^DJI", "^IXIC", "^RUT", "SPY"],
        index=0,
        format_func=lambda x: {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^RUT": "Russell 2000",
            "SPY": "SPY ETF"
        }.get(x, x)
    )

    # Período de datos
    periodo = st.selectbox(
        "📅 Período histórico",
        options=["1y", "2y", "3y", "5y", "10y"],
        index=1,
        format_func=lambda x: {
            "1y": "1 año", "2y": "2 años", "3y": "3 años",
            "5y": "5 años", "10y": "10 años"
        }.get(x, x)
    )

    st.markdown("---")
    st.markdown(
        "**Proyecto Integrador**  \n"
        "Teoría del Riesgo — USTA  \n"
        "Prof. Javier Mauricio Sierra"
    )

# Guardar configuración en session_state
st.session_state["tickers"] = tickers
st.session_state["benchmark"] = benchmark
st.session_state["periodo"] = periodo

# ── Página principal ──
st.markdown("""
<div class="main-header">
    <h1>RiskLabUSTA</h1>
    <p>Tablero Interactivo de Análisis de Riesgo Financiero</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
### 👋 Bienvenido al Tablero de Riesgo Financiero

Este tablero integra **8 módulos analíticos** conectados a APIs financieras en tiempo real.
Navega por las páginas del menú lateral para explorar cada módulo.

| Módulo | Descripción | Peso |
|--------|-------------|------|
| 📈 **Análisis Técnico** | SMA, EMA, RSI, MACD, Bollinger, Estocástico | 12% |
| 📊 **Rendimientos** | Log-rendimientos, pruebas de normalidad, hechos estilizados | 8% |
| 📉 **ARCH/GARCH** | Modelos de volatilidad condicional, pronóstico | 12% |
| 🛡️ **CAPM y Beta** | Riesgo sistemático, rendimiento esperado | 8% |
| ⚠️ **VaR y CVaR** | 3 métodos + Expected Shortfall | 12% |
| 🎯 **Markowitz** | Frontera eficiente, portafolios óptimos | 12% |
| ⚡ **Señales** | Alertas automáticas de trading | 10% |
| 🌐 **Macro** | Contexto macroeconómico, benchmark | 8% |
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Activos", len(tickers))
with col2:
    st.metric("Benchmark", benchmark)
with col3:
    st.metric("Período", periodo)

if len(tickers) < 5:
    st.warning("⚠️ Se requieren al menos 5 activos. Agrega más tickers en la barra lateral.")

# ── Carga inicial de datos ──
try:
    from src.data_loader import cargar_precios, cargar_indice

    with st.spinner("Cargando datos de mercado..."):
        precios = cargar_precios(tickers, periodo=periodo)
        indice = cargar_indice(benchmark, periodo=periodo)

    st.session_state["precios"] = precios
    st.session_state["indice"] = indice

    st.success(f"✅ Datos cargados: {len(precios)} observaciones × {len(precios.columns)} activos")

except Exception as e:
    st.error(f"❌ Error al cargar datos: {e}")
    st.info("Verifica tu conexión a internet y que los tickers sean válidos.")
