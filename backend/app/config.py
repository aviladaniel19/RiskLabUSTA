"""
config.py — Configuración centralizada con BaseSettings.

Patrón del curso Python para APIs e IA (Semana 6):
  - BaseSettings lee variables de entorno y del archivo .env automáticamente.
  - NUNCA se hardcodean API keys en el código fuente.
  - Todas las variables están documentadas en .env.example
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configuración de la aplicación.

    Pydantic-settings carga automáticamente desde:
      1. Variables de entorno del sistema operativo
      2. Archivo .env (si existe)

    El orden de prioridad es: variable de entorno > .env > valor por defecto.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora variables extra en .env sin error
    )

    # ── APIs Financieras Externas ──────────────────────────
    FRED_API_KEY: str = "tu_clave_fred_aqui"
    ALPHA_VANTAGE_KEY: str = ""
    FINNHUB_KEY: str = ""

    # ── Parámetros de Riesgo por defecto ──────────────────
    # Nivel de confianza para VaR (el usuario puede sobreescribir por endpoint)
    VAR_CONFIDENCE_DEFAULT: float = 0.95

    # Número de simulaciones Montecarlo
    MONTECARLO_N_SIM: int = 10_000

    # Ventana histórica por defecto (en días de trading)
    GARCH_WINDOW: int = 252

    # Ticker del índice de referencia (benchmark)
    BENCHMARK_TICKER: str = "^GSPC"  # S&P 500

    # Serie FRED para tasa libre de riesgo
    FRED_RF_SERIE: str = "DGS3MO"   # T-Bill 3 meses

    # ── Servidor ──────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ── CORS ──────────────────────────────────────────────
    # En producción, restringir a la URL del frontend
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna una instancia cacheada de Settings.

    lru_cache garantiza que Settings() se instancie UNA SOLA VEZ
    durante el ciclo de vida de la aplicación. Esto es eficiente porque
    BaseSettings lee archivos de disco en cada instanciación.

    Uso con FastAPI Depends():
        @app.get("/ejemplo")
        async def endpoint(cfg: Settings = Depends(get_settings)):
            ...
    """
    return Settings()
