# RiskLab USTA — Análisis Cuantitativo de Riesgo Financiero

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/fastapi-0.120%2B-brightgreen?logo=fastapi)
![Chart.js](https://img.shields.io/badge/chart.js-4.4%2B-ff6384?logo=chartdotjs)
![Tailwind CSS](https://img.shields.io/badge/tailwind-3.4%2B-38bdf8?logo=tailwindcss)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Autores:** Daniel Avila Otalora | **Profesor:** Javier Mauricio Sierra | **Versión:** 2.0

RiskLab USTA es una plataforma avanzada de análisis de riesgo financiero que combina un **backend robusto en FastAPI** con un **dashboard Single Page Application (SPA)** de alta fidelidad. Utiliza modelos econométricos y simulaciones de Monte Carlo para proporcionar una visión profunda de la volatilidad y optimización de portafolios.

---

## ✨ Características Principales

### 📊 Dashboard SPA (HTML5 + Chart.js)
- **Visualización Avanzada de Distribución:** Boxplots combinados con *Stripplots* (puntos de datos reales) para detectar outliers y densidad de retornos.
- **Optimización Interactiva:** Gráfico de Frontera Eficiente con mapa de calor por Ratio de Sharpe (Escala Naranja-Verde) y marcadores geométricos para Portafolios Óptimos.
- **Análisis de Volatilidad MLE:** Comparación dinámica de modelos ARCH, GARCH y EGARCH con tablas de diagnóstico centradas y profesionales.
- **Señales Técnicas:** Panel automático con indicadores RSI, MACD y Medias Móviles dinámicas.

### ⚙️ Motor Matemático (Python Core)
- **Modelos GARCH:** Estimación por máxima verosimilitud con test de Jarvis-Bera y Ljung-Box.
- **Value at Risk (VaR):** Cálculo por métodos Paramétrico, Histórico y Monte Carlo (10k sims) con Test de Kupiec.
- **Optimización de Markowitz:** Localización de la Frontera Eficiente y carteras de Mínima Varianza / Máximo Sharpe.

---

## 🏗️ Arquitectura del Proyecto

```
RiskLabUSTA/
├── backend/                    # Servidor API & Frontend SPA
│   ├── app/
│   │   ├── main.py            # Orquestación de Endpoints
│   │   ├── services.py        # Lógica de negocio (con corrección de tipos Numpy)
│   │   └── static/            # Frontend (index.html, assets)
│   └── requirements.txt        # Dependencias (FastAPI, Arch, Statsmodels)
├── src/                        # Módulos matemáticos independientes
│   ├── garch_models.py        # Modelizado de volatilidad
│   ├── var_cvar.py            # Gestión de riesgo VaR
│   ├── markowitz.py           # Optimización de carteras
│   └── api_client.py          # Conexión Yahoo Finance & FRED
├── README.md                   # Esta guía
└── TECHNICAL_GUIDE.md          # Documentación técnica detallada
```

---

## 📦 Instalación y Uso

### 1. Prerrequisitos
- **Local:** Python 3.11+ y acceso a terminal.
- **Docker (Recomendado):** Docker Desktop o Docker Engine con Docker Compose.
- **API Key:** FRED API Key (Obtenla gratis en [fred.stlouisfed.org](https://fred.stlouisfed.org/))

### 2. Configuración (.env)
1. Clona el repositorio.
2. Crea un archivo `.env` en la carpeta `backend/` con tu clave:
   ```env
   FRED_API_KEY=tu_clave_real_aqui
   ```
   *Nota: Si vas a usar Docker, el archivo .env debe estar en `backend/` para que el contenedor lo lea automáticamente.*

---

## 🚀 Opciones de Despliegue

### Opción 1: Desarrollo Local (Sin Docker)
1. Instala las dependencias:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Ejecuta el archivo automatizado:
   ```bash
   iniciar_dashboard.bat
   ```
   *O manualmente:* `cd backend && uvicorn app.main:app --reload --port 8000`

### Opción 2: Contenedores (Con Docker) ⭐
Esta opción garantiza que todas las librerías matemáticas (como `arch` y `statsmodels`) se instalen correctamente en un entorno aislado y optimizado.

1. **Construir y Arrancar:**
   ```bash
   docker-compose up -d --build
   ```
2. **Verificar Logs:**
   ```bash
   docker-compose logs -f
   ```
3. **Acceso:**
   - **Dashboard & API:** [http://localhost:8000](http://localhost:8000)
   - **Documentación:** [http://localhost:8000/docs](http://localhost:8000/docs)
4. **Detener:**
   ```bash
   docker-compose down
   ```

---

## 📡 API Endpoints (Swagger)

Accede a la documentación interactiva en `http://localhost:8000/docs` para probar los endpoints:
- `GET /volatilidad/{ticker}`: Análisis GARCH completo.
- `POST /var`: Cálculo de Riesgo Multimetodológico.
- `POST /frontera-eficiente`: Optimización de 10,000 portafolios.

---

## 📄 Licencia
Este proyecto está bajo la licencia **MIT**. Eres libre de usarlo y modificarlo con la debida atribución.

⭐ **Si este proyecto te ha sido útil, ¡considera darle una estrella!**
