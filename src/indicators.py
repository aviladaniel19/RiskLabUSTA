"""
indicators.py — Indicadores técnicos de análisis financiero.

Módulo 1: SMA, EMA, RSI, MACD, Bandas de Bollinger, Oscilador Estocástico.
"""

import pandas as pd
import numpy as np


def sma(precios: pd.Series, ventana: int = 20) -> pd.Series:
    """Media Móvil Simple (Simple Moving Average)."""
    return precios.rolling(window=ventana).mean()


def ema(precios: pd.Series, ventana: int = 20) -> pd.Series:
    """Media Móvil Exponencial (Exponential Moving Average)."""
    return precios.ewm(span=ventana, adjust=False).mean()


def rsi(precios: pd.Series, periodo: int = 14) -> pd.Series:
    """
    Índice de Fuerza Relativa (Relative Strength Index).
    RSI > 70 → sobrecompra, RSI < 30 → sobreventa.
    """
    delta = precios.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(com=periodo - 1, min_periods=periodo).mean()
    avg_loss = loss.ewm(com=periodo - 1, min_periods=periodo).mean()

    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    return rsi_values


def macd(precios: pd.Series,
         rapida: int = 12,
         lenta: int = 26,
         signal_period: int = 9) -> pd.DataFrame:
    """
    MACD (Moving Average Convergence Divergence).

    Returns
    -------
    DataFrame con columnas: MACD, Signal, Histograma.
    """
    ema_rapida = precios.ewm(span=rapida, adjust=False).mean()
    ema_lenta = precios.ewm(span=lenta, adjust=False).mean()

    macd_line = ema_rapida - ema_lenta
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histograma = macd_line - signal_line

    return pd.DataFrame({
        "MACD": macd_line,
        "Signal": signal_line,
        "Histograma": histograma
    })


def bollinger_bands(precios: pd.Series,
                    ventana: int = 20,
                    num_std: float = 2.0) -> pd.DataFrame:
    """
    Bandas de Bollinger.

    Returns
    -------
    DataFrame con columnas: Media, Superior, Inferior.
    """
    media = precios.rolling(window=ventana).mean()
    std = precios.rolling(window=ventana).std()

    return pd.DataFrame({
        "Media": media,
        "Superior": media + (num_std * std),
        "Inferior": media - (num_std * std)
    })


def estocastico(precios_high: pd.Series,
                precios_low: pd.Series,
                precios_close: pd.Series,
                k_periodo: int = 14,
                d_periodo: int = 3) -> pd.DataFrame:
    """
    Oscilador Estocástico (%K y %D).
    %K > 80 → sobrecompra, %K < 20 → sobreventa.

    Si solo se tienen precios de cierre, se puede usar Close para high y low
    con una aproximación basada en rolling max/min.
    """
    lowest_low = precios_low.rolling(window=k_periodo).min()
    highest_high = precios_high.rolling(window=k_periodo).max()

    k = 100 * (precios_close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_periodo).mean()

    return pd.DataFrame({
        "%K": k,
        "%D": d
    })


def estocastico_desde_close(precios_close: pd.Series,
                             k_periodo: int = 14,
                             d_periodo: int = 3) -> pd.DataFrame:
    """
    Oscilador Estocástico aproximado usando solo precios de cierre.
    Usa rolling max/min como proxy de High/Low.
    """
    return estocastico(
        precios_high=precios_close,
        precios_low=precios_close,
        precios_close=precios_close,
        k_periodo=k_periodo,
        d_periodo=d_periodo
    )


def resumen_indicadores(precios: pd.Series, nombre: str = "") -> dict:
    """
    Calcula todos los indicadores para un activo y retorna un diccionario resumen.
    """
    ultimo_precio = precios.iloc[-1]
    sma_20 = sma(precios, 20).iloc[-1]
    ema_20 = ema(precios, 20).iloc[-1]
    rsi_14 = rsi(precios, 14).iloc[-1]
    macd_df = macd(precios)
    bb = bollinger_bands(precios)

    return {
        "ticker": nombre,
        "precio": ultimo_precio,
        "SMA_20": sma_20,
        "EMA_20": ema_20,
        "RSI_14": rsi_14,
        "MACD": macd_df["MACD"].iloc[-1],
        "MACD_Signal": macd_df["Signal"].iloc[-1],
        "BB_Superior": bb["Superior"].iloc[-1],
        "BB_Inferior": bb["Inferior"].iloc[-1],
        "BB_Media": bb["Media"].iloc[-1],
    }
