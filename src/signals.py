"""
signals.py — Señales automáticas de trading y alertas.

⭐ Módulo 7: Señales basadas en indicadores técnicos.
Cruce MACD, RSI extremo, Bollinger, cruces de medias, estocástico.
"""

import pandas as pd
import numpy as np
from src.indicators import rsi, macd, bollinger_bands, sma, ema, estocastico_desde_close


def senal_macd(precios: pd.Series) -> dict:
    """
    Señal por cruce del MACD con la línea de señal.
    - Compra: MACD cruza por encima de Signal.
    - Venta: MACD cruza por debajo de Signal.
    """
    m = macd(precios)
    macd_actual = m["MACD"].iloc[-1]
    signal_actual = m["Signal"].iloc[-1]
    macd_prev = m["MACD"].iloc[-2]
    signal_prev = m["Signal"].iloc[-2]

    if macd_prev <= signal_prev and macd_actual > signal_actual:
        tipo = "COMPRA"
        color = "green"
        icono = "🟢"
    elif macd_prev >= signal_prev and macd_actual < signal_actual:
        tipo = "VENTA"
        color = "red"
        icono = "🔴"
    else:
        tipo = "NEUTRAL"
        color = "gray"
        icono = "⚪"

    return {
        "indicador": "MACD",
        "señal": tipo,
        "color": color,
        "icono": icono,
        "valor": round(macd_actual, 4),
        "detalle": f"MACD: {macd_actual:.4f} | Signal: {signal_actual:.4f}",
        "texto": (
            f"**MACD ({tipo}):** La línea MACD ({macd_actual:.4f}) "
            f"{'cruzó por encima' if tipo == 'COMPRA' else 'cruzó por debajo' if tipo == 'VENTA' else 'se mantiene cerca'} "
            f"de la línea de señal ({signal_actual:.4f})."
        )
    }


def senal_rsi(precios: pd.Series, sobrecompra: float = 70,
              sobreventa: float = 30) -> dict:
    """
    Señal por RSI en zonas extremas.
    - RSI > sobrecompra → Venta (sobrecomprado).
    - RSI < sobreventa → Compra (sobrevendido).
    """
    rsi_val = rsi(precios).iloc[-1]

    if rsi_val > sobrecompra:
        tipo = "VENTA"
        color = "red"
        icono = "🔴"
        zona = "SOBRECOMPRA"
    elif rsi_val < sobreventa:
        tipo = "COMPRA"
        color = "green"
        icono = "🟢"
        zona = "SOBREVENTA"
    else:
        tipo = "NEUTRAL"
        color = "gray"
        icono = "⚪"
        zona = "NEUTRAL"

    return {
        "indicador": "RSI",
        "señal": tipo,
        "color": color,
        "icono": icono,
        "valor": round(rsi_val, 2),
        "detalle": f"RSI: {rsi_val:.2f} | Zona: {zona}",
        "texto": (
            f"**RSI ({tipo}):** RSI = {rsi_val:.2f}. "
            f"{'Zona de sobrecompra (> ' + str(sobrecompra) + '). Posible corrección a la baja.' if tipo == 'VENTA' else ''}"
            f"{'Zona de sobreventa (< ' + str(sobreventa) + '). Posible rebote al alza.' if tipo == 'COMPRA' else ''}"
            f"{'Zona neutral. Sin señal clara.' if tipo == 'NEUTRAL' else ''}"
        )
    }


def senal_bollinger(precios: pd.Series, ventana: int = 20,
                    num_std: float = 2.0) -> dict:
    """
    Señal por Bandas de Bollinger.
    - Precio toca banda inferior → posible Compra.
    - Precio toca banda superior → posible Venta.
    """
    bb = bollinger_bands(precios, ventana, num_std)
    precio_actual = precios.iloc[-1]
    superior = bb["Superior"].iloc[-1]
    inferior = bb["Inferior"].iloc[-1]

    if precio_actual >= superior:
        tipo = "VENTA"
        color = "red"
        icono = "🔴"
    elif precio_actual <= inferior:
        tipo = "COMPRA"
        color = "green"
        icono = "🟢"
    else:
        tipo = "NEUTRAL"
        color = "gray"
        icono = "⚪"

    return {
        "indicador": "Bollinger",
        "señal": tipo,
        "color": color,
        "icono": icono,
        "valor": round(precio_actual, 2),
        "detalle": f"Precio: {precio_actual:.2f} | Superior: {superior:.2f} | Inferior: {inferior:.2f}",
        "texto": (
            f"**Bollinger ({tipo}):** Precio ({precio_actual:.2f}) "
            f"{'toca la banda superior ({0:.2f}). Posible sobrecompra.'.format(superior) if tipo == 'VENTA' else ''}"
            f"{'toca la banda inferior ({0:.2f}). Posible sobreventa.'.format(inferior) if tipo == 'COMPRA' else ''}"
            f"{'dentro de las bandas. Sin señal.'.format() if tipo == 'NEUTRAL' else ''}"
        )
    }


def senal_cruce_medias(precios: pd.Series, corta: int = 50,
                       larga: int = 200) -> dict:
    """
    Señal por cruce de medias móviles (Golden Cross / Death Cross).
    - Golden Cross: SMA corta cruza por encima de SMA larga → Compra.
    - Death Cross: SMA corta cruza por debajo de SMA larga → Venta.
    """
    sma_corta = sma(precios, corta)
    sma_larga = sma(precios, larga)

    if sma_corta.iloc[-1] is np.nan or sma_larga.iloc[-1] is np.nan:
        return {
            "indicador": "Cruce de Medias",
            "señal": "INSUF. DATOS",
            "color": "gray",
            "icono": "⚪",
            "valor": 0,
            "detalle": "Datos insuficientes para calcular medias móviles",
            "texto": "Datos insuficientes."
        }

    corta_actual = sma_corta.iloc[-1]
    larga_actual = sma_larga.iloc[-1]
    corta_prev = sma_corta.iloc[-2]
    larga_prev = sma_larga.iloc[-2]

    if corta_prev <= larga_prev and corta_actual > larga_actual:
        tipo = "COMPRA"
        color = "green"
        icono = "🟢"
        nombre = "Golden Cross"
    elif corta_prev >= larga_prev and corta_actual < larga_actual:
        tipo = "VENTA"
        color = "red"
        icono = "🔴"
        nombre = "Death Cross"
    elif corta_actual > larga_actual:
        tipo = "ALCISTA"
        color = "green"
        icono = "🟡"
        nombre = "Tendencia alcista"
    else:
        tipo = "BAJISTA"
        color = "red"
        icono = "🟡"
        nombre = "Tendencia bajista"

    return {
        "indicador": "Cruce de Medias",
        "señal": tipo,
        "color": color,
        "icono": icono,
        "valor": round(corta_actual - larga_actual, 2),
        "detalle": f"SMA{corta}: {corta_actual:.2f} | SMA{larga}: {larga_actual:.2f} | {nombre}",
        "texto": (
            f"**Cruce de Medias ({tipo}):** SMA({corta}) = {corta_actual:.2f}, "
            f"SMA({larga}) = {larga_actual:.2f}. {nombre}."
        )
    }


def senal_estocastico(precios: pd.Series, k_periodo: int = 14,
                      d_periodo: int = 3,
                      sobrecompra: float = 80,
                      sobreventa: float = 20) -> dict:
    """
    Señal por Oscilador Estocástico.
    - %K cruza %D en zona de sobreventa → Compra.
    - %K cruza %D en zona de sobrecompra → Venta.
    """
    est = estocastico_desde_close(precios, k_periodo, d_periodo)
    k_actual = est["%K"].iloc[-1]
    d_actual = est["%D"].iloc[-1]

    if k_actual < sobreventa and k_actual > d_actual:
        tipo = "COMPRA"
        color = "green"
        icono = "🟢"
    elif k_actual > sobrecompra and k_actual < d_actual:
        tipo = "VENTA"
        color = "red"
        icono = "🔴"
    else:
        tipo = "NEUTRAL"
        color = "gray"
        icono = "⚪"

    return {
        "indicador": "Estocástico",
        "señal": tipo,
        "color": color,
        "icono": icono,
        "valor": round(k_actual, 2),
        "detalle": f"%K: {k_actual:.2f} | %D: {d_actual:.2f}",
        "texto": (
            f"**Estocástico ({tipo}):** %K = {k_actual:.2f}, %D = {d_actual:.2f}. "
            f"{'Cruce alcista en zona de sobreventa. Posible entrada.' if tipo == 'COMPRA' else ''}"
            f"{'Cruce bajista en zona de sobrecompra. Posible salida.' if tipo == 'VENTA' else ''}"
            f"{'Sin señal significativa.' if tipo == 'NEUTRAL' else ''}"
        )
    }


def generar_todas_las_senales(precios: pd.Series,
                               rsi_sobrecompra: float = 70,
                               rsi_sobreventa: float = 30) -> list[dict]:
    """
    Genera todas las señales para un activo.

    Returns
    -------
    list[dict] con una señal por cada indicador.
    """
    return [
        senal_macd(precios),
        senal_rsi(precios, rsi_sobrecompra, rsi_sobreventa),
        senal_bollinger(precios),
        senal_cruce_medias(precios),
        senal_estocastico(precios),
    ]


def resumen_senales(precios: pd.Series, nombre: str = "") -> dict:
    """Resume todas las señales para un activo con veredicto general."""
    senales = generar_todas_las_senales(precios)

    n_compra = sum(1 for s in senales if s["señal"] == "COMPRA")
    n_venta = sum(1 for s in senales if s["señal"] == "VENTA")

    if n_compra > n_venta and n_compra >= 2:
        veredicto = "🟢 COMPRA"
    elif n_venta > n_compra and n_venta >= 2:
        veredicto = "🔴 VENTA"
    else:
        veredicto = "⚪ NEUTRAL"

    return {
        "ticker": nombre,
        "senales": senales,
        "compra": n_compra,
        "venta": n_venta,
        "veredicto": veredicto,
    }
