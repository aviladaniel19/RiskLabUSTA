"""
var_cvar.py — Valor en Riesgo y Expected Shortfall.

Módulo 5: VaR paramétrico, histórico, Montecarlo (10,000+), CVaR.
"""

import pandas as pd
import numpy as np
from scipy import stats


def var_parametrico(rendimientos: pd.Series,
                    nivel_confianza: float = 0.95) -> dict:
    """
    VaR Paramétrico (método de varianza-covarianza, asumiendo normalidad).

    VaR = μ - z × σ

    Parameters
    ----------
    rendimientos : pd.Series
        Serie de rendimientos logarítmicos.
    nivel_confianza : float
        Nivel de confianza (0.95 o 0.99).

    Returns
    -------
    dict con VaR diario, anualizado, e interpretación.
    """
    mu = rendimientos.mean()
    sigma = rendimientos.std()
    z = stats.norm.ppf(1 - nivel_confianza)

    var_diario = -(mu + z * sigma)
    var_anual = var_diario * np.sqrt(252)

    return {
        "metodo": "Paramétrico (Normal)",
        "nivel_confianza": nivel_confianza,
        "var_diario": var_diario,
        "var_anual": var_anual,
        "interpretacion": (
            f"Con un {nivel_confianza*100:.0f}% de confianza, la pérdida máxima "
            f"esperada en un día es de {var_diario*100:.2f}% del valor del portafolio."
        )
    }


def var_historico(rendimientos: pd.Series,
                  nivel_confianza: float = 0.95) -> dict:
    """
    VaR por Simulación Histórica.
    Usa el percentil empírico de la distribución de rendimientos.
    """
    alpha = 1 - nivel_confianza
    var_diario = -rendimientos.quantile(alpha)
    var_anual = var_diario * np.sqrt(252)

    return {
        "metodo": "Histórico",
        "nivel_confianza": nivel_confianza,
        "var_diario": var_diario,
        "var_anual": var_anual,
        "interpretacion": (
            f"Basado en datos históricos, con {nivel_confianza*100:.0f}% de confianza, "
            f"la pérdida máxima diaria es de {var_diario*100:.2f}%."
        )
    }


def var_montecarlo(rendimientos: pd.Series,
                   nivel_confianza: float = 0.95,
                   n_simulaciones: int = 10000,
                   seed: int = 42) -> dict:
    """
    VaR por Simulación de Montecarlo.
    Genera n_simulaciones rendimientos aleatorios asumiendo distribución normal
    con la media y desviación estándar histórica.
    """
    np.random.seed(seed)
    mu = rendimientos.mean()
    sigma = rendimientos.std()

    simulados = np.random.normal(mu, sigma, n_simulaciones)
    alpha = 1 - nivel_confianza
    var_diario = -np.percentile(simulados, alpha * 100)
    var_anual = var_diario * np.sqrt(252)

    return {
        "metodo": f"Montecarlo ({n_simulaciones:,} sim.)",
        "nivel_confianza": nivel_confianza,
        "var_diario": var_diario,
        "var_anual": var_anual,
        "simulaciones": simulados,
        "interpretacion": (
            f"Simulación Montecarlo con {n_simulaciones:,} escenarios. "
            f"VaR diario al {nivel_confianza*100:.0f}%: {var_diario*100:.2f}%."
        )
    }


def cvar(rendimientos: pd.Series,
         nivel_confianza: float = 0.95) -> dict:
    """
    CVaR (Conditional VaR) o Expected Shortfall.
    Promedio de las pérdidas que exceden el VaR.
    """
    alpha = 1 - nivel_confianza
    var = rendimientos.quantile(alpha)
    # CVaR = promedio de los rendimientos peores que el VaR
    cvar_diario = -rendimientos[rendimientos <= var].mean()
    cvar_anual = cvar_diario * np.sqrt(252)

    return {
        "metodo": "CVaR (Expected Shortfall)",
        "nivel_confianza": nivel_confianza,
        "cvar_diario": cvar_diario,
        "cvar_anual": cvar_anual,
        "var_diario": -var,  # VaR para referencia
        "interpretacion": (
            f"Si las pérdidas superan el VaR ({-var*100:.2f}%), "
            f"la pérdida promedio esperada es de {cvar_diario*100:.2f}%. "
            f"El CVaR es una medida más conservadora que el VaR."
        )
    }


def tabla_comparativa_var(rendimientos: pd.Series,
                          niveles: list = [0.95, 0.99]) -> pd.DataFrame:
    """
    Genera tabla comparativa de todos los métodos de VaR y CVaR.
    """
    resultados = []
    for nivel in niveles:
        vp = var_parametrico(rendimientos, nivel)
        vh = var_historico(rendimientos, nivel)
        vm = var_montecarlo(rendimientos, nivel)
        cv = cvar(rendimientos, nivel)

        resultados.extend([
            {
                "Nivel": f"{nivel*100:.0f}%",
                "Método": "Paramétrico",
                "VaR Diario": f"{vp['var_diario']*100:.2f}%",
                "VaR Anual": f"{vp['var_anual']*100:.2f}%",
            },
            {
                "Nivel": f"{nivel*100:.0f}%",
                "Método": "Histórico",
                "VaR Diario": f"{vh['var_diario']*100:.2f}%",
                "VaR Anual": f"{vh['var_anual']*100:.2f}%",
            },
            {
                "Nivel": f"{nivel*100:.0f}%",
                "Método": "Montecarlo",
                "VaR Diario": f"{vm['var_diario']*100:.2f}%",
                "VaR Anual": f"{vm['var_anual']*100:.2f}%",
            },
            {
                "Nivel": f"{nivel*100:.0f}%",
                "Método": "CVaR (ES)",
                "VaR Diario": f"{cv['cvar_diario']*100:.2f}%",
                "VaR Anual": f"{cv['cvar_anual']*100:.2f}%",
            },
        ])

    return pd.DataFrame(resultados)


def var_portafolio(rendimientos: pd.DataFrame,
                   pesos: np.ndarray,
                   nivel_confianza: float = 0.95) -> dict:
    """
    Calcula VaR del portafolio ponderado.
    """
    rendimiento_portafolio = (rendimientos * pesos).sum(axis=1)
    return {
        "parametrico": var_parametrico(rendimiento_portafolio, nivel_confianza),
        "historico": var_historico(rendimiento_portafolio, nivel_confianza),
        "montecarlo": var_montecarlo(rendimiento_portafolio, nivel_confianza),
        "cvar": cvar(rendimiento_portafolio, nivel_confianza),
    }
