"""
macro_benchmark.py — Contexto macroeconómico y comparación con benchmark.

⭐ Módulo 8: Datos macro vía API, rendimiento acumulado vs benchmark,
Alpha de Jensen, Tracking Error, Information Ratio, Máximo Drawdown.
"""

import pandas as pd
import numpy as np
from src.api_client import obtener_dato_macro, obtener_tasa_libre_riesgo, obtener_rf_actual


def obtener_panel_macro() -> dict:
    """
    Descarga indicadores macroeconómicos clave desde FRED.

    Returns
    -------
    dict con los valores más recientes de cada indicador.
    """
    indicadores = {}

    # Tasa libre de riesgo (T-Bill 3 meses)
    try:
        rf = obtener_tasa_libre_riesgo("DGS3MO")
        indicadores["Tasa libre de riesgo (T-Bill 3M)"] = {
            "valor": f"{rf.iloc[-1]*100:.2f}%",
            "fecha": str(rf.index[-1].date()),
            "serie": rf
        }
    except Exception as e:
        indicadores["Tasa libre de riesgo"] = {"valor": "Error", "fecha": "-", "error": str(e)}

    # Federal Funds Rate
    try:
        ffr = obtener_dato_macro("DFF")
        indicadores["Federal Funds Rate"] = {
            "valor": f"{ffr.iloc[-1]:.2f}%",
            "fecha": str(ffr.index[-1].date()),
            "serie": ffr
        }
    except Exception:
        indicadores["Federal Funds Rate"] = {"valor": "N/A", "fecha": "-"}

    # Treasury 10Y
    try:
        t10 = obtener_dato_macro("DGS10")
        indicadores["Treasury 10 años"] = {
            "valor": f"{t10.iloc[-1]:.2f}%",
            "fecha": str(t10.index[-1].date()),
            "serie": t10
        }
    except Exception:
        indicadores["Treasury 10 años"] = {"valor": "N/A", "fecha": "-"}

    # Spread 10Y-2Y (inversión de curva)
    try:
        spread = obtener_dato_macro("T10Y2Y")
        indicadores["Spread 10Y-2Y"] = {
            "valor": f"{spread.iloc[-1]:.2f}%",
            "fecha": str(spread.index[-1].date()),
            "serie": spread
        }
    except Exception:
        indicadores["Spread 10Y-2Y"] = {"valor": "N/A", "fecha": "-"}

    return indicadores


def rendimiento_acumulado_base100(rendimientos: pd.Series) -> pd.Series:
    """
    Calcula el rendimiento acumulado normalizado a base 100.
    """
    return (1 + rendimientos).cumprod() * 100


def comparar_vs_benchmark(rendimientos_portafolio: pd.Series,
                           rendimientos_benchmark: pd.Series) -> pd.DataFrame:
    """
    Compara rendimiento acumulado del portafolio vs benchmark, ambos base 100.
    """
    # Alinear índices
    idx_comun = rendimientos_portafolio.index.intersection(rendimientos_benchmark.index)
    rp = rendimientos_portafolio.loc[idx_comun]
    rb = rendimientos_benchmark.loc[idx_comun]

    return pd.DataFrame({
        "Portafolio": rendimiento_acumulado_base100(rp),
        "Benchmark": rendimiento_acumulado_base100(rb),
    })


def alpha_jensen(rendimientos_portafolio: pd.Series,
                 rendimientos_benchmark: pd.Series,
                 rf: float = None) -> float:
    """
    Alpha de Jensen: exceso de rendimiento ajustado por riesgo.
    α = R_p - [R_f + β × (R_m - R_f)]
    """
    if rf is None:
        rf = obtener_rf_actual()

    rf_diario = rf / 252

    rp = rendimientos_portafolio.mean() * 252
    rm = rendimientos_benchmark.mean() * 252

    # Beta del portafolio
    idx = rendimientos_portafolio.index.intersection(rendimientos_benchmark.index)
    cov = np.cov(rendimientos_portafolio.loc[idx], rendimientos_benchmark.loc[idx])
    beta = cov[0, 1] / cov[1, 1]

    alpha = rp - (rf + beta * (rm - rf))
    return alpha


def tracking_error(rendimientos_portafolio: pd.Series,
                   rendimientos_benchmark: pd.Series) -> float:
    """
    Tracking Error: volatilidad de la diferencia de rendimientos (anualizado).
    TE = σ(R_p - R_m) × √252
    """
    idx = rendimientos_portafolio.index.intersection(rendimientos_benchmark.index)
    diff = rendimientos_portafolio.loc[idx] - rendimientos_benchmark.loc[idx]
    return diff.std() * np.sqrt(252)


def information_ratio(rendimientos_portafolio: pd.Series,
                      rendimientos_benchmark: pd.Series) -> float:
    """
    Information Ratio: exceso de rendimiento / tracking error.
    IR = (R_p - R_m) / TE
    """
    idx = rendimientos_portafolio.index.intersection(rendimientos_benchmark.index)
    rp = rendimientos_portafolio.loc[idx].mean() * 252
    rm = rendimientos_benchmark.loc[idx].mean() * 252
    te = tracking_error(rendimientos_portafolio, rendimientos_benchmark)

    if te == 0:
        return 0

    return (rp - rm) / te


def max_drawdown(rendimientos: pd.Series) -> float:
    """
    Máximo Drawdown: mayor caída desde un pico hasta un valle.
    """
    acumulado = (1 + rendimientos).cumprod()
    pico = acumulado.cummax()
    drawdown = (acumulado - pico) / pico
    return drawdown.min()


def tabla_desempeno(rendimientos_portafolio: pd.Series,
                    rendimientos_benchmark: pd.Series,
                    rf: float = None) -> pd.DataFrame:
    """
    Tabla completa de desempeño: rendimiento, volatilidad, Sharpe, etc.
    """
    if rf is None:
        rf = obtener_rf_actual()

    idx = rendimientos_portafolio.index.intersection(rendimientos_benchmark.index)
    rp = rendimientos_portafolio.loc[idx]
    rb = rendimientos_benchmark.loc[idx]

    def metricas(r, nombre):
        ret_anual = r.mean() * 252
        vol_anual = r.std() * np.sqrt(252)
        sharpe = (ret_anual - rf) / vol_anual if vol_anual > 0 else 0
        mdd = max_drawdown(r)
        ret_acum = (1 + r).prod() - 1

        return {
            "": nombre,
            "Rend. Acumulado": f"{ret_acum*100:.2f}%",
            "Rend. Anualizado": f"{ret_anual*100:.2f}%",
            "Volatilidad Anual": f"{vol_anual*100:.2f}%",
            "Sharpe Ratio": f"{sharpe:.3f}",
            "Máx. Drawdown": f"{mdd*100:.2f}%",
        }

    tabla = pd.DataFrame([
        metricas(rp, "Portafolio"),
        metricas(rb, "Benchmark"),
    ]).set_index("")

    return tabla


def interpretacion_benchmark(rendimientos_portafolio: pd.Series,
                              rendimientos_benchmark: pd.Series,
                              rf: float = None) -> str:
    """Genera texto interpretativo de la comparación."""
    alpha = alpha_jensen(rendimientos_portafolio, rendimientos_benchmark, rf)
    te = tracking_error(rendimientos_portafolio, rendimientos_benchmark)
    ir = information_ratio(rendimientos_portafolio, rendimientos_benchmark)

    texto = f"### Análisis comparativo vs Benchmark\n\n"
    texto += f"- **Alpha de Jensen:** {alpha*100:.2f}%\n"

    if alpha > 0:
        texto += "  → El portafolio generó rendimiento **por encima** de lo esperado según su riesgo (CAPM).\n\n"
    else:
        texto += "  → El portafolio generó rendimiento **por debajo** de lo esperado según su riesgo.\n\n"

    texto += f"- **Tracking Error:** {te*100:.2f}%\n"
    texto += "  → Mide la desviación del portafolio respecto al benchmark.\n\n"

    texto += f"- **Information Ratio:** {ir:.3f}\n"
    if abs(ir) > 0.5:
        texto += "  → IR > 0.5 sugiere una gestión activa exitosa.\n"
    else:
        texto += "  → IR bajo, cercano a gestión pasiva.\n"

    return texto
