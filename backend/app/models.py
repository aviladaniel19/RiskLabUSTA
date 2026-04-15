"""
models.py — Modelos Pydantic para request y response de todos los endpoints.

Patrón del curso Python para APIs e IA (Semanas 2, 4 y 5):
  - Todos los datos de entrada son validados automáticamente por Pydantic.
  - Los modelos de respuesta definen exactamente qué devuelve cada endpoint.
  - Field() documenta cada campo → se muestra en /docs (Swagger UI).
  - @field_validator implementa reglas de negocio en la validación.
"""

from __future__ import annotations
from typing import Annotated, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ═══════════════════════════════════════════════════════
# MODELOS COMPARTIDOS
# ═══════════════════════════════════════════════════════

class ActivoInfo(BaseModel):
    """Información básica de un activo financiero."""
    ticker: str = Field(..., description="Símbolo bursátil (ej: AAPL, MSFT)")
    nombre: str = Field(..., description="Nombre completo de la empresa o activo")
    sector: str = Field(default="N/A", description="Sector económico")
    moneda: str = Field(default="USD", description="Moneda de cotización")


# ═══════════════════════════════════════════════════════
# ENDPOINT: /activos
# ═══════════════════════════════════════════════════════

class ActivosResponse(BaseModel):
    """Respuesta del endpoint GET /activos."""
    activos: list[ActivoInfo] = Field(..., description="Lista de activos configurados")
    total: int = Field(..., description="Número total de activos")
    benchmark: str = Field(..., description="Ticker del índice de referencia")


# ═══════════════════════════════════════════════════════
# ENDPOINT: /precios/{ticker}
# ═══════════════════════════════════════════════════════

class PreciosPuntoResponse(BaseModel):
    """Un punto de precio en la serie histórica."""
    fecha: str = Field(..., description="Fecha en formato YYYY-MM-DD")
    precio: float = Field(..., description="Precio de cierre ajustado")


class PreciosResponse(BaseModel):
    """Respuesta del endpoint GET /precios/{ticker}."""
    ticker: str = Field(..., description="Símbolo bursátil")
    periodo: str = Field(..., description="Período de datos descargado")
    n_observaciones: int = Field(..., description="Número de observaciones")
    precios: list[PreciosPuntoResponse] = Field(..., description="Serie de precios")
    precio_actual: float = Field(..., description="Último precio disponible")
    precio_inicio: float = Field(..., description="Primer precio del período")
    retorno_total: float = Field(..., description="Retorno total del período (decimal)")


# ═══════════════════════════════════════════════════════
# ENDPOINT: /rendimientos/{ticker}
# ═══════════════════════════════════════════════════════

class EstadisticasDescriptivas(BaseModel):
    """Estadísticas descriptivas de una serie de rendimientos."""
    media_diaria: float
    media_anualizada: float
    volatilidad_diaria: float
    volatilidad_anualizada: float
    asimetria: float = Field(..., alias="asimetría")
    curtosis_exceso: float
    minimo: float = Field(..., alias="mínimo")
    maximo: float = Field(..., alias="máximo")
    n_observaciones: int

    model_config = {"populate_by_name": True}


class PruebaEstadistica(BaseModel):
    """Resultado de una prueba estadística de normalidad."""
    estadistico: float = Field(..., alias="estadístico")
    p_valor: float
    es_normal: bool
    interpretacion: str = Field(..., alias="interpretación")

    model_config = {"populate_by_name": True}


class RendimientosPuntoResponse(BaseModel):
    """Un punto de rendimiento en la serie temporal."""
    fecha: str
    rendimiento_log: float
    rendimiento_simple: float


class RendimientosResponse(BaseModel):
    """Respuesta del endpoint GET /rendimientos/{ticker}."""
    ticker: str
    tipo: str = Field(..., description="'log' o 'simple'")
    estadisticas: EstadisticasDescriptivas
    jarque_bera: PruebaEstadistica
    shapiro_wilk: PruebaEstadistica
    rendimientos: list[RendimientosPuntoResponse]
    hechos_estilizados: str = Field(..., description="Texto interpretativo")


# ═══════════════════════════════════════════════════════
# ENDPOINT: /indicadores/{ticker}
# ═══════════════════════════════════════════════════════

class IndicadoresPuntoResponse(BaseModel):
    """Indicadores técnicos para una fecha."""
    fecha: str
    precio: float
    sma_20: float | None = None
    sma_50: float | None = None
    ema_20: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    bb_superior: float | None = None
    bb_media: float | None = None
    bb_inferior: float | None = None
    estocastico_k: float | None = None
    estocastico_d: float | None = None


class IndicadoresResponse(BaseModel):
    """Respuesta del endpoint GET /indicadores/{ticker}."""
    ticker: str
    n_observaciones: int
    ultimo_precio: float
    ultimo_rsi: float | None = None
    ultimo_macd: float | None = None
    indicadores: list[IndicadoresPuntoResponse]


# ═══════════════════════════════════════════════════════
# MODELOS COMPARTIDOS: REQUEST DE PORTAFOLIO
# ═══════════════════════════════════════════════════════

class PortafolioRequest(BaseModel):
    """
    Request compartido para endpoints que reciben un portafolio.

    Contiene dos @field_validator que demuestran validación de negocio:
      1. Los tickers deben ser strings válidos y se normalizan a mayúsculas.
      2. Los pesos deben sumar exactamente 1.0 (±0.001 de tolerancia).

    Además el @model_validator verifica que len(tickers) == len(pesos).
    """

    tickers: list[str] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Lista de tickers del portafolio. Mínimo 2, máximo 20.",
        examples=[["AAPL", "MSFT", "AMZN", "TSLA", "GOOG"]],
    )
    pesos: list[float] = Field(
        ...,
        description="Peso de cada activo en el portafolio. Deben sumar 1.0.",
        examples=[[0.25, 0.25, 0.20, 0.15, 0.15]],
    )
    nivel_confianza: Annotated[float, Field(ge=0.90, le=0.99)] = Field(
        default=0.95,
        description="Nivel de confianza para VaR (entre 0.90 y 0.99).",
    )
    periodo: str = Field(
        default="2y",
        description="Período de datos históricos (ej: '1y', '2y', '5y').",
        pattern=r"^\d+[dmy]$",
    )

    @field_validator("tickers")
    @classmethod
    def normalizar_tickers(cls, v: list[str]) -> list[str]:
        """
        Normaliza tickers a mayúsculas y elimina espacios.

        Por qué: Yahoo Finance distingue entre 'aapl' y 'AAPL'.
        Este validador garantiza consistencia sin importar cómo escriba el usuario.
        """
        normalizados = [t.strip().upper() for t in v]
        if any(len(t) == 0 for t in normalizados):
            raise ValueError("Los tickers no pueden ser strings vacíos.")
        return normalizados

    @field_validator("pesos")
    @classmethod
    def verificar_suma_pesos(cls, v: list[float]) -> list[float]:
        """
        Valida que los pesos del portafolio sumen 1.0.

        Se permite una tolerancia de ±0.001 para errores de redondeo de punto flotante.
        (e.g. [0.33, 0.33, 0.34] = 1.00, no hay problema)
        """
        suma = sum(v)
        if not (0.999 <= suma <= 1.001):
            raise ValueError(
                f"Los pesos deben sumar 1.0. "
                f"Suma recibida: {suma:.6f}. "
                f"Ajuste los valores para que sumen exactamente 1."
            )
        return v

    @model_validator(mode="after")
    def verificar_longitud_coincide(self) -> "PortafolioRequest":
        """
        Verifica que el número de tickers coincida con el número de pesos.

        Este es un @model_validator (no field_validator) porque necesita
        acceder a DOS campos al mismo tiempo.
        """
        if len(self.tickers) != len(self.pesos):
            raise ValueError(
                f"El número de tickers ({len(self.tickers)}) no coincide "
                f"con el número de pesos ({len(self.pesos)}). "
                f"Cada ticker debe tener exactamente un peso asignado."
            )
        return self


# ═══════════════════════════════════════════════════════
# ENDPOINT: /var (POST)
# ═══════════════════════════════════════════════════════

class VaRMetodo(BaseModel):
    """Resultado de un método de cálculo de VaR."""
    metodo: str
    nivel_confianza: float
    var_diario: float = Field(..., description="VaR diario como decimal (ej: 0.025 = 2.5%)")
    var_diario_pct: str = Field(..., description="VaR diario formateado como porcentaje")
    var_anual: float = Field(..., description="VaR anualizado")
    var_anual_pct: str
    interpretacion: str


class VaRResponse(BaseModel):
    """Respuesta del endpoint POST /var."""
    tickers: list[str]
    pesos: list[float]
    nivel_confianza: float
    parametrico: VaRMetodo
    historico: VaRMetodo
    montecarlo: VaRMetodo
    cvar: dict[str, Any]
    rendimiento_portafolio_anual: float
    volatilidad_portafolio_anual: float


# ═══════════════════════════════════════════════════════
# ENDPOINT: /capm (GET)
# ═══════════════════════════════════════════════════════

class CAPMActivoResponse(BaseModel):
    """CAPM calculado para un activo individual."""
    ticker: str
    beta: float = Field(..., description="Beta por regresión OLS contra el benchmark")
    alpha_jensen: float = Field(..., description="Alpha de Jensen anualizado")
    r_cuadrado: float = Field(..., description="R² de la regresión")
    clasificacion: str = Field(..., description="Agresivo / Neutro / Defensivo")
    rendimiento_esperado_capm: float
    rendimiento_esperado_capm_pct: str


class CAPMResponse(BaseModel):
    """Respuesta del endpoint GET /capm."""
    benchmark: str
    rf_actual: float = Field(..., description="Tasa libre de riesgo actual de FRED")
    rf_actual_pct: str
    rendimiento_mercado_anual: float
    activos: list[CAPMActivoResponse]
    discusion: str


# ═══════════════════════════════════════════════════════
# ENDPOINT: /frontera-eficiente (POST)
# ═══════════════════════════════════════════════════════

class PortafolioOptimo(BaseModel):
    """Un portafolio óptimo identificado en la frontera eficiente."""
    tipo: str = Field(..., description="'Mínima Varianza' o 'Máximo Sharpe'")
    tickers: list[str]
    pesos: list[float]
    rendimiento_anual: float
    volatilidad_anual: float
    sharpe_ratio: float


class PuntoFrontera(BaseModel):
    """Un punto en la nube de portafolios simulados."""
    rendimiento: float
    volatilidad: float
    sharpe: float


class FronteraResponse(BaseModel):
    """Respuesta del endpoint POST /frontera-eficiente."""
    tickers: list[str]
    n_simulaciones: int
    portafolio_min_varianza: PortafolioOptimo
    portafolio_max_sharpe: PortafolioOptimo
    puntos_simulados: list[PuntoFrontera]
    matriz_correlacion: dict[str, dict[str, float]]


# ═══════════════════════════════════════════════════════
# ENDPOINT: /alertas (GET)
# ═══════════════════════════════════════════════════════

class AlertaActivo(BaseModel):
    """Señales de trading para un activo."""
    ticker: str
    senal_global: str = Field(
        ...,
        description="COMPRAR / VENDER / MANTENER"
    )
    macd_senal: str
    rsi_senal: str
    bollinger_senal: str
    cruce_medias: str
    estocastico_senal: str
    ultimo_precio: float
    rsi_actual: float | None = None
    texto_interpretativo: str


class AlertasResponse(BaseModel):
    """Respuesta del endpoint GET /alertas."""
    tickers: list[str]
    alertas: list[AlertaActivo]
    timestamp: str


# ═══════════════════════════════════════════════════════
# ENDPOINT: /macro (GET)
# ═══════════════════════════════════════════════════════

class IndicadorMacro(BaseModel):
    """Un indicador macroeconómico."""
    nombre: str
    serie_fred: str
    valor_actual: float
    unidad: str
    fecha_actualizacion: str


class DesempenioPortafolio(BaseModel):
    """Métricas de desempeño comparativo."""
    rendimiento_acumulado: float
    rendimiento_anualizado: float
    volatilidad_anualizada: float
    sharpe_ratio: float
    maximo_drawdown: float


class MacroResponse(BaseModel):
    """Respuesta del endpoint GET /macro."""
    indicadores_macro: list[IndicadorMacro]
    desempeno_portafolio: DesempenioPortafolio
    desempeno_benchmark: DesempenioPortafolio
    alpha_jensen: float
    tracking_error: float
    information_ratio: float
    interpretacion: str


# ═══════════════════════════════════════════════════════
# ENDPOINT: /garch/{ticker}
# ═══════════════════════════════════════════════════════

class ModeloGARCH(BaseModel):
    """Resultados de un modelo GARCH ajustado."""
    nombre: str
    aic: float
    bic: float
    log_likelihood: float
    volatilidad_anualizada: float
    es_mejor: bool = False


class GARCHResponse(BaseModel):
    """Respuesta del endpoint GET /garch/{ticker}."""
    ticker: str
    modelos_comparados: list[ModeloGARCH]
    mejor_modelo: str
    pronostico_volatilidad: list[float] = Field(
        ...,
        description="Pronóstico de volatilidad para los próximos 10 días"
    )
    jarque_bera_residuos: PruebaEstadistica
    interpretacion: str
