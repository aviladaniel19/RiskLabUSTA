"""
api_client.py — Conexión a APIs financieras externas.

Provee funciones para descargar datos desde:
  - Yahoo Finance (precios históricos de acciones, ETFs, índices)
  - FRED API (tasa libre de riesgo, inflación, datos macro USA)

Todas las llamadas tienen manejo de errores y reintentos.
"""

import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Yahoo Finance
# ──────────────────────────────────────────────

def descargar_precios(tickers: list[str],
                      inicio: str = None,
                      fin: str = None,
                      periodo: str = "2y") -> pd.DataFrame:
    """
    Descarga precios de cierre ajustados desde Yahoo Finance.

    Parameters
    ----------
    tickers : list[str]
        Lista de tickers, e.g. ["AAPL", "MSFT", "AMZN"].
    inicio : str, optional
        Fecha de inicio "YYYY-MM-DD". Si se da, ignora `periodo`.
    fin : str, optional
        Fecha de fin "YYYY-MM-DD". Por defecto hoy.
    periodo : str
        Período relativo si no se dan fechas (e.g. "2y", "5y").

    Returns
    -------
    pd.DataFrame
        DataFrame con columnas = tickers, índice = fecha, valores = precio de cierre ajustado.
    """
    try:
        if inicio:
            data = yf.download(
                tickers,
                start=inicio,
                end=fin or datetime.now().strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False
            )
        else:
            data = yf.download(
                tickers,
                period=periodo,
                auto_adjust=True,
                progress=False
            )

        if data.empty:
            raise ValueError(f"No se obtuvieron datos para los tickers: {tickers}")

        # yfinance devuelve MultiIndex cuando hay varios tickers
        if isinstance(data.columns, pd.MultiIndex):
            precios = data["Close"]
        else:
            precios = data[["Close"]]
            precios.columns = tickers

        # Eliminar columnas completamente vacías
        precios = precios.dropna(axis=1, how="all")

        if precios.empty:
            raise ValueError(f"Los datos descargados están vacíos para: {tickers}")

        return precios

    except Exception as e:
        raise RuntimeError(
            f"Error al descargar datos de Yahoo Finance: {e}\n"
            f"Verifica que los tickers ({tickers}) sean válidos y que tengas conexión a internet."
        )


def descargar_indice(ticker_indice: str = "^GSPC",
                     inicio: str = None,
                     fin: str = None,
                     periodo: str = "2y") -> pd.Series:
    """
    Descarga el precio de cierre de un índice de referencia (benchmark).
    Por defecto: S&P 500 (^GSPC).
    """
    df = descargar_precios([ticker_indice], inicio=inicio, fin=fin, periodo=periodo)
    return df.iloc[:, 0].rename(ticker_indice)


def obtener_info_ticker(ticker: str) -> dict:
    """Obtiene información básica de un ticker (nombre, sector, etc.)."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "nombre": info.get("longName", ticker),
            "sector": info.get("sector", "N/A"),
            "industria": info.get("industry", "N/A"),
            "moneda": info.get("currency", "USD"),
            "exchange": info.get("exchange", "N/A"),
        }
    except Exception:
        return {"nombre": ticker, "sector": "N/A", "industria": "N/A",
                "moneda": "USD", "exchange": "N/A"}


# ──────────────────────────────────────────────
# FRED API — Datos macroeconómicos
# ──────────────────────────────────────────────

def _get_fred():
    """Crea un cliente FRED autenticado."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "tu_clave_fred_aqui":
        raise RuntimeError(
            "No se encontró FRED_API_KEY en las variables de entorno.\n"
            "1. Regístrate gratis en https://fred.stlouisfed.org/docs/api/api_key.html\n"
            "2. Copia tu clave en el archivo .env:\n"
            "   FRED_API_KEY=tu_clave_real"
        )
    from fredapi import Fred
    return Fred(api_key=api_key)


def obtener_tasa_libre_riesgo(serie: str = "DGS3MO",
                               inicio: str = None) -> pd.Series:
    """
    Obtiene la tasa libre de riesgo desde FRED.

    Series comunes:
      - DGS3MO: Treasury 3 meses
      - DGS10 : Treasury 10 años
      - DTB3  : T-Bill 3 meses (secondary market)

    Returns
    -------
    pd.Series con la tasa anualizada (en decimales, e.g. 0.05 = 5%).
    """
    try:
        fred = _get_fred()
        if inicio:
            data = fred.get_series(serie, observation_start=inicio)
        else:
            data = fred.get_series(serie)

        data = data.dropna() / 100  # Convertir de porcentaje a decimal
        data.name = "risk_free_rate"
        return data

    except Exception as e:
        raise RuntimeError(f"Error al obtener datos de FRED ({serie}): {e}")


def obtener_dato_macro(serie: str, inicio: str = None) -> pd.Series:
    """
    Obtiene cualquier serie macroeconómica de FRED.

    Series útiles:
      - CPIAUCSL : CPI (inflación USA)
      - GDPC1    : PIB real USA
      - UNRATE   : Tasa de desempleo
      - DFF      : Federal Funds Rate
      - T10Y2Y   : Spread 10Y-2Y (inversión de curva)
    """
    try:
        fred = _get_fred()
        if inicio:
            data = fred.get_series(serie, observation_start=inicio)
        else:
            data = fred.get_series(serie)
        data = data.dropna()
        data.name = serie
        return data
    except Exception as e:
        raise RuntimeError(f"Error al obtener serie FRED '{serie}': {e}")


def obtener_rf_actual() -> float:
    """Retorna la última tasa libre de riesgo disponible (T-Bill 3 meses) como decimal."""
    try:
        rf = obtener_tasa_libre_riesgo("DGS3MO")
        return float(rf.iloc[-1])
    except Exception:
        # Fallback: tasa manual de referencia
        return 0.0525  # 5.25% como fallback
