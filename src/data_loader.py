"""
data_loader.py — Orquestación de carga y limpieza de datos.

Usa Streamlit caching para evitar descargas repetidas
y respetar rate limits de las APIs.
"""

import streamlit as st
import pandas as pd
import numpy as np
from src.api_client import descargar_precios, descargar_indice, obtener_info_ticker


@st.cache_data(ttl=3600, show_spinner="Descargando datos de Yahoo Finance...")
def cargar_precios(tickers: list, inicio: str = None, fin: str = None,
                   periodo: str = "2y") -> pd.DataFrame:
    """
    Carga precios con caché de 1 hora.
    Aplica limpieza de valores faltantes (forward fill).
    """
    precios = descargar_precios(tickers, inicio=inicio, fin=fin, periodo=periodo)
    precios = limpiar_datos(precios)
    return precios


@st.cache_data(ttl=3600, show_spinner="Descargando índice de referencia...")
def cargar_indice(ticker_indice: str = "^GSPC", inicio: str = None,
                  fin: str = None, periodo: str = "2y") -> pd.Series:
    """Carga índice de referencia con caché."""
    indice = descargar_indice(ticker_indice, inicio=inicio, fin=fin, periodo=periodo)
    indice = indice.ffill().dropna()
    return indice


@st.cache_data(ttl=86400, show_spinner=False)
def cargar_info_tickers(tickers: list) -> dict:
    """Carga información de tickers con caché de 24 horas."""
    return {t: obtener_info_ticker(t) for t in tickers}


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia un DataFrame de precios:
      1. Forward fill para llenar huecos de fines de semana / festivos
      2. Eliminar filas iniciales con NaN (si un activo cotiza después que otro)
      3. Documentar cantidad de datos faltantes
    """
    n_faltantes = df.isna().sum().sum()
    if n_faltantes > 0:
        st.info(
            f"ℹ️ Se encontraron {n_faltantes} valores faltantes. "
            f"Se aplicó forward fill para completarlos."
        )

    df = df.ffill()       # Rellenar hacia adelante
    df = df.dropna()      # Eliminar filas restantes con NaN
    return df


def calcular_rendimientos(precios: pd.DataFrame,
                          tipo: str = "log") -> pd.DataFrame:
    """
    Calcula rendimientos a partir de precios.

    Parameters
    ----------
    precios : pd.DataFrame
        Precios de cierre.
    tipo : str
        "log" para rendimientos logarítmicos (default),
        "simple" para rendimientos simples.

    Returns
    -------
    pd.DataFrame con rendimientos (sin la primera fila NaN).
    """
    if tipo == "log":
        returns = np.log(precios / precios.shift(1))
    else:
        returns = precios.pct_change()

    return returns.dropna()
