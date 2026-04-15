# RiskLab USTA — Análisis Cuantitativo de Riesgo Financiero

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/fastapi-0.111%2B-brightgreen?logo=fastapi)
![Streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red?logo=streamlit)
![Docker](https://img.shields.io/badge/docker-compose-blue?logo=docker)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-coming%20soon-lightgrey)

**Autores:** Equipo RiskLab | **Profesor:** Javier Mauricio Sierra | **Versión:** 2.0

Tablero interactivo de análisis cuantitativo de riesgo financiero con arquitectura **backend FastAPI + frontend Streamlit**, conectado a APIs financieras (Yahoo Finance y FRED).

---

## 📑 Tabla de Contenidos

- [✨ Características](#-características)
- [🏗️ Arquitectura](#-arquitectura)
- [📦 Instalación](#-instalación)
- [🚀 Uso Rápido](#-uso-rápido)
- [📡 API Endpoints](#-api-endpoints)
- [🔐 Variables de Entorno](#-variables-de-entorno)
- [🤝 Contribuciones](#-contribuciones)
- [📄 Licencia](#-licencia)

---

## ✨ Características

### Dashboard Interactivo (Streamlit)
- 📊 **8 Módulos de Análisis** — Técnico, Rendimientos, GARCH, CAPM, VaR, Markowitz, Señales, Macro
- 📈 **Indicadores Técnicos** — SMA, EMA, RSI, MACD, Bollinger Bands, Estocástico
- 🎯 **Backtesting** — Validación de estrategias históricas
- 🔮 **Optimización de Portafolio** — Frontera eficiente de Markowitz
- 🚨 **Alertas Automáticas** — Señales semáforo en tiempo real

### API REST (FastAPI)
- ✅ **9 Endpoints RESTful Async** — Diseño escalable
- 📚 **Documentación Interactiva** — Swagger/OpenAPI en `/docs`
- 🔌 **Modular y Reutilizable** — Módulos de cálculo independientes
- 🛡️ **Type-safe** — Validación con Pydantic v2
- ⚡ **High Performance** — Async/await con uvicorn

### Análisis Financiero
- 📉 **Volatilidad Dinámica** — Modelos ARCH/GARCH
- 💰 **Value at Risk (VaR)** — Métodos paramétrico, histórico y Montecarlo
- 📊 **CAPM & Benchmark** — Cálculo de beta y exceso de rendimiento
- 🎲 **Simulaciones** — 10,000 simulaciones Montecarlo para portafolios
- 🌍 **Indicadores Macro** — Integración FRED (Federal Reserve)

---

## 🏗️ Arquitectura

```
RiskLabUSTA/
├── backend/                    # ⚙️ API FastAPI — motor de cálculo
│   ├── app/
│   │   ├── main.py            # 9 endpoints async
│   │   ├── models.py          # Pydantic schemas (request/response)
│   │   ├── services.py        # Orquestador de módulos
│   │   ├── dependencies.py    # Inyección de dependencias
│   │   └── config.py          # BaseSettings + .env
│   ├── src/                    # Módulos de cálculo reutilizados
│   │   ├── capm.py            # Capital Asset Pricing Model
│   │   ├── garch_models.py    # ARCH/GARCH
│   │   ├── markowitz.py       # Optimización portafolio
│   │   ├── var_cvar.py        # Value at Risk
│   │   ├── indicators.py      # Análisis técnico
│   │   └── ...
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # 🎨 Dashboard Streamlit — visualización
│   ├── app.py                 # Punto de entrada + helpers
│   ├── pages/                 # 8 módulos como páginas
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example               # Variables de configuración
├── .github/
│   ├── workflows/             # CI/CD Automation
│   │   ├── tests.yml
│   │   └── docker-build.yml
│   └── PULL_REQUEST_TEMPLATE.md
└── README.md
```

---

## 📦 Instalación

### Opción 1: Sin Docker (Desarrollo Local)

#### Prerrequisitos
- Python 3.11+
- Git
- FRED API Key (gratis en https://fred.stlouisfed.org/)

#### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/RiskLabUSTA.git
cd RiskLabUSTA

# 2. Backend — entorno virtual e instalación
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar tu FRED_API_KEY

# 4. Iniciar backend
uvicorn app.main:app --reload --port 8000
```

En **otra terminal**:

```bash
# 5. Frontend
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

**Se abrirá automáticamente** en http://localhost:8501

### Opción 2: Con Docker (Recomendado)

```bash
# 1. Configurar .env
cp backend/.env.example backend/.env
# Editar backend/.env con tu FRED_API_KEY

# 2. Construir y arrancar TODO
docker-compose up -d

# 3. Ver logs en tiempo real
docker-compose logs -f

# 4. Acceso
# API Swagger: http://localhost:8000/docs
# Dashboard:   http://localhost:8501

# 5. Detener
docker-compose down
```

---

## 🚀 Uso Rápido

### 1. Obtener API Key (FRED)

1. Ve a https://fred.stlouisfed.org/docs/api/api_key.html
2. Regístrate (gratis)
3. Copia tu API key en `.env`

### 2. Usar el Dashboard

1. Navega por los 8 módulos en el sidebar izquierdo
2. Ingresa tickers recomendados: `AAPL`, `MSFT`, `AMZN`, `TSLA`, `GOOG`
3. Explora gráficos e indicadores interactivos

### 3. Usar la API Directamente

```bash
# Obtener rendimientos de un activo
curl http://localhost:8000/rendimientos/AAPL?dias=252

# Calcular VaR (POST)
curl -X POST http://localhost:8000/var \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MSFT",
    "dias": 252,
    "metodo": "montecarlo",
    "confidence": 0.95
  }'

# Ver documentación completa
open http://localhost:8000/docs
```

---

## 📡 API Endpoints

| Endpoint | Método | Módulo | Descripción |
|----------|--------|--------|-------------|
| `/health` | GET | — | Health check del servidor |
| `/rendimientos/{ticker}` | GET | 2️⃣ | Rendimientos + pruebas normalidad (Shapiro-Wilk) |
| `/indicadores/{ticker}` | GET | 1️⃣ | Análisis técnico (SMA, EMA, RSI, MACD, Bollinger, Estocástico) |
| `/garch/{ticker}` | GET | 3️⃣ | Comparación ARCH vs GARCH (AIC, BIC) |
| `/capm` | GET | 4️⃣ | Beta + CAPM (Rf desde FRED) |
| `/var` | POST | 5️⃣ | VaR (paramétrico, histórico, MC) + CVaR |
| `/frontera-eficiente` | POST | 6️⃣ | Portafolio óptimo (10k simulaciones) |
| `/alertas/{ticker}` | GET | 7️⃣ | Señales automáticas (semáforo) |
| `/macro` | GET | 8️⃣ | Indicadores FRED + Alpha de Jensen |

**Ver documentación interactiva:** http://localhost:8000/docs (Swagger UI)

---

## 🔐 Variables de Entorno

Copia `.env.example` a `.env` y completa:

```env
# ✅ OBLIGATORIO
FRED_API_KEY=your_key_here

# Opcional (para features adicionales)
ALPHA_VANTAGE_KEY=
FINNHUB_KEY=

# Configuración (defaults si no especifica)
VAR_CONFIDENCE_DEFAULT=0.95
MONTECARLO_N_SIM=10000
GARCH_WINDOW=252
BENCHMARK_TICKER=^GSPC
FRED_RF_SERIE=DGS3MO
```

Ver `.env.example` para descripción detallada.

---

## 🤝 Contribuciones

¡Somos bienvenidos a contribuciones! Lee nuestra [**Guía de Contribución**](CONTRIBUTING.md) para:

- Reportar bugs 🐛
- Proponer features 💡
- Hacer Pull Requests 🚀

**Proceso rápido:**

1. Fork el repo
2. Crea una rama: `git checkout -b feat/tu-feature`
3. Commit con mensajes claros: `git commit -m "feat: descripción"`
4. Push: `git push origin feat/tu-feature`
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT** — ver [LICENSE](LICENSE) para detalles.

Eres libre de usar, modificar y distribuir este código con atribución.

---

## 📚 Bibliografía

1. Moscote Flórez, O. *Elementos de estadística en riesgo financiero*. USTA, 2013.
2. Hull, J. C. (2018). *Risk Management and Financial Institutions*. 5th ed., Wiley.
3. Markowitz, H. (1952). Portfolio Selection. *The Journal of Finance*, 7(1), 77–91.
4. Tsay, R. S. (2010). *Analysis of Financial Time Series*. 3rd ed., Wiley.

### Tecnologías

- 🚀 [FastAPI](https://fastapi.tiangolo.com/) — API web moderna
- 🎨 [Streamlit](https://streamlit.io/) — Dashboard en Python
- 📊 [Pandas & NumPy](https://pandas.pydata.org/) — Data Science
- 📈 [Plotly](https://plotly.com/) — Gráficos interactivos
- 📦 [Docker](https://www.docker.com/) — Containerización
- 🔗 [yfinance](https://github.com/ranaroussi/yfinance) — Yahoo Finance
- 🏦 [FRED API](https://fred.stlouisfed.org/) — Datos macroeconómicos
- 📊 [statsmodels & scikit-learn](https://scikit-learn.org/) — Modelos estadísticos

---

## 👥 Autores

- **Equipo RiskLab USTA**
- **Profesor:** Javier Mauricio Sierra
- **Asistencia de IA:** Antigravity (Google DeepMind)

---

**¿Preguntas?** Abre un [Issue](../../issues) o [Discussion](../../discussions).

⭐ **Si te gusta el proyecto, dale una estrella!**
