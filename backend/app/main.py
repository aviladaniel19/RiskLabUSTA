"""
main.py — Punto de entrada de la API RiskLab.

FastAPI con 9 endpoints async que cumplen todos los requerimientos
de la rúbrica del Proyecto Integrador de Teoría del Riesgo.

Ejecución local:
    uvicorn app.main:app --reload --port 8000

Con Docker:
    docker-compose up
"""

import functools
import logging
import time
from typing import Annotated, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi import Request

from app.config import get_settings, Settings
from app.dependencies import get_data_service, DataService
from app.services import RiskService
from app.models import (
    ActivosResponse,
    PreciosResponse,
    RendimientosResponse,
    IndicadoresResponse,
    PortafolioRequest,
    VaRResponse,
    CAPMResponse,
    FronteraResponse,
    AlertasResponse,
    MacroResponse,
    GARCHResponse,
)

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE LOGGING
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
logger = logging.getLogger("risklab.api")


# ──────────────────────────────────────────────
# DECORADOR PERSONALIZADO: log_request
# ──────────────────────────────────────────────
# Requerimiento de la rúbrica (Buenas prácticas — Semana 1):
# Al menos un decorador personalizado implementado.

def log_request(func):
    """
    Decorador de comportamiento que registra entrada y salida de cada endpoint.

    Diferencia con @app.get/@app.post:
      - @app.get es un decorador de REGISTRO (le dice a FastAPI qué ruta maneja).
      - @log_request es un decorador de COMPORTAMIENTO (agrega logging sin tocar la lógica).
    Ambos usan el mismo mecanismo Python: functools.wraps + closures.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        inicio = time.perf_counter()
        logger.info(f"→ {func.__name__}() llamado")
        try:
            resultado = await func(*args, **kwargs)
            ms = (time.perf_counter() - inicio) * 1000
            logger.info(f"✓ {func.__name__}() OK en {ms:.1f}ms")
            return resultado
        except HTTPException:
            raise
        except Exception as exc:
            ms = (time.perf_counter() - inicio) * 1000
            logger.error(f"✗ {func.__name__}() ERROR en {ms:.1f}ms → {exc}")
            raise
    return wrapper


# ──────────────────────────────────────────────
# INSTANCIA FASTAPI
# ──────────────────────────────────────────────

app = FastAPI(
    title="RiskLab API — Teoría del Riesgo USTA",
    description=(
        "Backend FastAPI para el tablero interactivo de riesgo financiero. "
        "Expone 9 endpoints de análisis cuantitativo: indicadores técnicos, "
        "rendimientos, GARCH, CAPM, VaR/CVaR, Markowitz, señales y macro. "
        "Todos los inputs son validados con modelos Pydantic."
    ),
    version="2.0.0",
    contact={
        "name": "Proyecto Integrador — Teoría del Riesgo",
        "email": "risklab@usta.edu.co",
    },
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "Core", "description": "Activos y precios base"},
        {"name": "Análisis Técnico", "description": "Módulo 1 — Indicadores"},
        {"name": "Rendimientos", "description": "Módulo 2 — Propiedades empíricas"},
        {"name": "GARCH", "description": "Módulo 3 — Volatilidad condicional"},
        {"name": "CAPM", "description": "Módulo 4 — Riesgo sistemático"},
        {"name": "VaR", "description": "Módulo 5 — Valor en Riesgo"},
        {"name": "Markowitz", "description": "Módulo 6 — Frontera eficiente"},
        {"name": "Señales", "description": "Módulo 7 — Alertas automáticas"},
        {"name": "Macro", "description": "Módulo 8 — Contexto macroeconómico"},
    ],
)

# ── CORS — permite que Streamlit (otro puerto) consuma la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# MANEJADOR DE ERRORES 422
# ──────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Transforma los errores de validación Pydantic en JSON descriptivo.
    Requerimiento de la rúbrica: manejo HTTP 422 personalizado.
    """
    errores = []
    for error in exc.errors():
        campo = " → ".join(str(loc) for loc in error["loc"])
        errores.append({
            "campo": campo,
            "mensaje": error["msg"],
            "tipo_error": error["type"],
            "valor_recibido": error.get("input"),
        })

    logger.warning(
        f"[422] {request.method} {request.url.path} → "
        f"{len(errores)} error(es) de validación"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "estado": "error_validacion",
            "codigo": 422,
            "mensaje": "Los datos enviados contienen errores. Revise cada campo.",
            "errores": errores,
        },
    )


# ──────────────────────────────────────────────
# DEPENDENCIA: RiskService (inyección de dependencias)
# ──────────────────────────────────────────────

def get_risk_service(
    settings: Settings = Depends(get_settings),
) -> RiskService:
    """
    Dependencia que crea e inyecta el servicio de riesgo.
    Las rutas reciben RiskService pre-configurado — no instancian nada.
    """
    return RiskService(settings)


# ══════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════

# ── UI y HEALTH CHECK ─────────────────────

@app.get("/", tags=["Core"], summary="Dashboard Frontend UI", include_in_schema=False)
async def serve_ui():
    """Sirve la interfaz gráfica del Dashboard (HTML principal)."""
    import os
    file_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Dashboard UI no encontrado en static/index.html"}

@app.get("/health", tags=["Core"], summary="Health check de la API")
async def health_check():
    """Verifica que la API está operativa."""
    return {
        "status": "ok",
        "app": "RiskLab API",
        "version": "2.0.0",
        "docs": "/docs",
    }


# ── ENDPOINT 1: /activos ──────────────────────

@app.get(
    "/activos",
    response_model=ActivosResponse,
    tags=["Core"],
    summary="Lista activos disponibles en el portafolio",
    description=(
        "Retorna la lista de tickers configurados con información básica "
        "(nombre, sector, moneda). El portafolio se define dinámicamente "
        "pasando el parámetro `tickers`."
    ),
)
@log_request
async def get_activos(
    tickers: Annotated[
        str,
        Query(
            description="Tickers separados por coma. Ej: AAPL,MSFT,TSLA,AMZN,GOOG",
            example="AAPL,MSFT,TSLA,AMZN,GOOG",
        ),
    ],
    svc: RiskService = Depends(get_risk_service),
    settings: Settings = Depends(get_settings),
):
    import sys, os
    _SRC = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)
    from api_client import obtener_info_ticker

    lista = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    activos = []
    for t in lista:
        try:
            info = obtener_info_ticker(t)
            activos.append({
                "ticker": t,
                "nombre": info.get("nombre", t),
                "sector": info.get("sector", "N/A"),
                "moneda": info.get("moneda", "USD"),
            })
        except Exception:
            activos.append({"ticker": t, "nombre": t, "sector": "N/A", "moneda": "USD"})

    return {
        "activos": activos,
        "total": len(activos),
        "benchmark": settings.BENCHMARK_TICKER,
    }


# ── ENDPOINT 2: /precios/{ticker} ─────────────

@app.get(
    "/precios/{ticker}",
    response_model=PreciosResponse,
    tags=["Core"],
    summary="Precios históricos de un activo",
    description="Retorna precios de cierre ajustados desde Yahoo Finance.",
)
@log_request
async def get_precios(
    ticker: str,
    periodo: str = Query(default="2y", description="Período: 1y, 2y, 5y"),
    svc: RiskService = Depends(get_risk_service),
):
    ticker = ticker.upper()
    try:
        precios_df = svc.obtener_precios(ticker, periodo=periodo)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    precios = precios_df.iloc[:, 0]
    pts = [
        {"fecha": str(f.date()), "precio": float(p)}
        for f, p in zip(precios.index[-500:], precios.values[-500:])
    ]
    return {
        "ticker": ticker,
        "periodo": periodo,
        "n_observaciones": len(precios),
        "precios": pts,
        "precio_actual": float(precios.iloc[-1]),
        "precio_inicio": float(precios.iloc[0]),
        "retorno_total": float((precios.iloc[-1] / precios.iloc[0]) - 1),
    }


# ── ENDPOINT 3: /rendimientos/{ticker} ────────

@app.get(
    "/rendimientos/{ticker}",
    response_model=RendimientosResponse,
    tags=["Rendimientos"],
    summary="Rendimientos y estadísticas del activo (Módulo 2)",
    description=(
        "Calcula rendimientos logarítmicos y simples, estadísticas descriptivas "
        "completas, pruebas de normalidad Jarque-Bera y Shapiro-Wilk, "
        "e interpretación de hechos estilizados."
    ),
)
@log_request
async def get_rendimientos(
    ticker: str,
    periodo: str = Query(default="2y", description="Período histórico"),
    svc: RiskService = Depends(get_risk_service),
):
    ticker = ticker.upper()
    try:
        resultado = svc.calcular_rendimientos_completo(ticker, periodo=periodo)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return resultado


# ── ENDPOINT 4: /indicadores/{ticker} ─────────

@app.get(
    "/indicadores/{ticker}",
    response_model=IndicadoresResponse,
    tags=["Análisis Técnico"],
    summary="Indicadores técnicos del activo (Módulo 1)",
    description=(
        "Calcula SMA(20), SMA(50), EMA(20), RSI(14), MACD, "
        "Bandas de Bollinger y Oscilador Estocástico."
    ),
)
@log_request
async def get_indicadores(
    ticker: str,
    periodo: str = Query(default="2y", description="Período histórico"),
    svc: RiskService = Depends(get_risk_service),
):
    ticker = ticker.upper()
    try:
        resultado = svc.calcular_indicadores(ticker, periodo=periodo)
    except (RuntimeError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return resultado


# ── ENDPOINT 5: /garch/{ticker} ───────────────

@app.get(
    "/garch/{ticker}",
    response_model=GARCHResponse,
    tags=["GARCH"],
    summary="Modelos GARCH de volatilidad condicional (Módulo 3)",
    description=(
        "Ajusta y compara ARCH(1), GARCH(1,1) y EGARCH(1,1). "
        "Retorna tabla AIC/BIC, diagnóstico de residuos y pronóstico de volatilidad."
    ),
)
@log_request
async def get_garch(
    ticker: str,
    periodo: str = Query(default="2y"),
    svc: RiskService = Depends(get_risk_service),
):
    ticker = ticker.upper()
    try:
        resultado = svc.calcular_garch(ticker, periodo=periodo)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error ajustando modelos GARCH: {e}",
        )
    return resultado


# ── ENDPOINT 5b: /volatilidad/{ticker} ────────

@app.get(
    "/volatilidad/{ticker}",
    tags=["GARCH"],
    summary="Análisis completo de modelación de volatilidad condicional",
    description=(
        "Endpoint completo para la sección de Volatilidad. "
        "Incluye: test ADF de estacionariedad, prueba ARCH-LM de Engle, "
        "Ljung-Box sobre residuales², comparación ARCH/GARCH/EGARCH, "
        "serie de volatilidad condicional, rendimientos², pronóstico 30d, "
        "y diagnóstico exhaustivo de residuos estandarizados."
    ),
)
@log_request
async def get_volatilidad(
    ticker: str,
    periodo: str = Query(default="2y"),
    svc: RiskService = Depends(get_risk_service),
):
    ticker = ticker.upper()
    try:
        resultado = svc.calcular_volatilidad_completo(ticker, periodo=periodo)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error en análisis de volatilidad: {e}",
        )
    return resultado


# ── ENDPOINT 6: /capm ─────────────────────────

@app.get(
    "/capm",
    response_model=CAPMResponse,
    tags=["CAPM"],
    summary="CAPM y riesgo sistemático con Rf desde FRED (Módulo 4)",
    description=(
        "Calcula Beta por regresión OLS, rendimiento esperado CAPM y "
        "clasificación (agresivo/neutro/defensivo). "
        "La tasa libre de riesgo se obtiene automáticamente desde la API FRED."
    ),
)
@log_request
async def get_capm(
    tickers: Annotated[
        str,
        Query(
            description="Tickers separados por coma",
            example="AAPL,MSFT,TSLA",
        ),
    ],
    periodo: str = Query(default="2y"),
    svc: RiskService = Depends(get_risk_service),
):
    lista = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(lista) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos 1 ticker.",
        )
    try:
        resultado = svc.calcular_capm_completo(lista, periodo=periodo)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return resultado


# ── ENDPOINT 7: /var (POST) ───────────────────

@app.post(
    "/var",
    response_model=VaRResponse,
    tags=["VaR"],
    summary="Value at Risk y CVaR del portafolio (Módulo 5)",
    description=(
        "Recibe un portafolio (tickers + pesos) y calcula VaR paramétrico, "
        "histórico y Montecarlo (10,000 simulaciones), más CVaR. "
        "Los pesos se validan con @field_validator para garantizar que sumen 1.0."
    ),
)
@log_request
async def post_var(
    portafolio: PortafolioRequest,
    svc: RiskService = Depends(get_risk_service),
):
    try:
        resultado = svc.calcular_var(
            portafolio.tickers,
            portafolio.pesos,
            portafolio.nivel_confianza,
            portafolio.periodo,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    return resultado


# ── ENDPOINT 8: /frontera-eficiente (POST) ────

@app.post(
    "/frontera-eficiente",
    response_model=FronteraResponse,
    tags=["Markowitz"],
    summary="Frontera eficiente de Markowitz (Módulo 6)",
    description=(
        "Simula 10,000 portafolios aleatorios y calcula la frontera eficiente. "
        "Identifica el portafolio de mínima varianza y el de máximo ratio de Sharpe."
    ),
)
@log_request
async def post_frontera_eficiente(
    portafolio: PortafolioRequest,
    svc: RiskService = Depends(get_risk_service),
    settings: Settings = Depends(get_settings),
):
    try:
        resultado = svc.calcular_frontera(
            portafolio.tickers,
            portafolio.periodo,
            n_simulaciones=settings.MONTECARLO_N_SIM,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error calculando frontera eficiente: {e}",
        )
    return resultado


# ── ENDPOINT 9: /alertas ──────────────────────

@app.get(
    "/alertas",
    response_model=AlertasResponse,
    tags=["Señales"],
    summary="Señales automáticas de compra/venta por activo (Módulo 7)",
    description=(
        "Evalúa para cada activo: cruce MACD, RSI en zonas extremas, "
        "Bandas de Bollinger, cruce de medias (golden/death cross) y "
        "Oscilador Estocástico. Devuelve panel semáforo con señal global."
    ),
)
@log_request
async def get_alertas(
    tickers: Annotated[
        str,
        Query(description="Tickers separados por coma", example="AAPL,MSFT,TSLA"),
    ],
    periodo: str = Query(default="1y"),
    svc: RiskService = Depends(get_risk_service),
):
    lista = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    resultado = svc.calcular_alertas(lista, periodo=periodo)
    return resultado


# ── ENDPOINT 10: /macro ───────────────────────

@app.get(
    "/macro",
    response_model=MacroResponse,
    tags=["Macro"],
    summary="Contexto macroeconómico y benchmark (Módulo 8)",
    description=(
        "Retorna indicadores macroeconómicos en tiempo real desde FRED "
        "(tasa libre de riesgo, inflación, Federal Funds Rate). "
        "Compara el rendimiento del portafolio vs benchmark con "
        "Alpha de Jensen, Tracking Error e Information Ratio."
    ),
)
@log_request
async def get_macro(
    tickers: Annotated[str, Query(description="Tickers separados por coma")],
    pesos: Annotated[str, Query(description="Pesos separados por coma. Deben sumar 1.0")],
    periodo: str = Query(default="2y"),
    svc: RiskService = Depends(get_risk_service),
):
    lista_t = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    lista_p = [float(p.strip()) for p in pesos.split(",") if p.strip()]

    if len(lista_t) != len(lista_p):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de tickers debe coincidir con el número de pesos.",
        )
    suma = sum(lista_p)
    if not (0.999 <= suma <= 1.001):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Los pesos deben sumar 1.0. Suma recibida: {suma:.4f}",
        )

    try:
        resultado = svc.calcular_macro(lista_t, lista_p, periodo=periodo)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    return resultado
