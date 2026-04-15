"""
markowitz.py — Optimización de portafolio: Frontera Eficiente de Markowitz.

Módulo 6: Simulación de portafolios, frontera eficiente, mínima varianza,
máximo ratio de Sharpe, composición detallada.
"""

import pandas as pd
import numpy as np
from scipy.optimize import minimize


def simular_portafolios(rendimientos: pd.DataFrame,
                        n_portafolios: int = 10000,
                        rf: float = 0.05,
                        seed: int = 42) -> pd.DataFrame:
    """
    Simula n_portafolios aleatorios variando los pesos.

    Returns
    -------
    DataFrame con columnas: Rendimiento, Volatilidad, Sharpe, + peso de cada activo.
    """
    np.random.seed(seed)
    n_activos = rendimientos.shape[1]
    nombres = rendimientos.columns.tolist()

    # Rendimiento y covarianza anualizados
    mu_anual = rendimientos.mean() * 252
    cov_anual = rendimientos.cov() * 252

    resultados = []
    for _ in range(n_portafolios):
        # Pesos aleatorios que suman 1
        pesos = np.random.random(n_activos)
        pesos /= pesos.sum()

        # Rendimiento y volatilidad del portafolio
        ret_port = np.dot(pesos, mu_anual)
        vol_port = np.sqrt(np.dot(pesos.T, np.dot(cov_anual, pesos)))
        sharpe = (ret_port - rf) / vol_port

        fila = {
            "Rendimiento": ret_port,
            "Volatilidad": vol_port,
            "Sharpe": sharpe,
        }
        for i, nombre in enumerate(nombres):
            fila[nombre] = pesos[i]

        resultados.append(fila)

    return pd.DataFrame(resultados)


def portafolio_minima_varianza(rendimientos: pd.DataFrame,
                                rf: float = 0.05) -> dict:
    """
    Encuentra el portafolio de mínima varianza por optimización numérica.
    """
    n = rendimientos.shape[1]
    mu_anual = rendimientos.mean().values * 252
    cov_anual = rendimientos.cov().values * 252
    nombres = rendimientos.columns.tolist()

    def volatilidad(pesos):
        return np.sqrt(np.dot(pesos.T, np.dot(cov_anual, pesos)))

    # Restricciones: pesos suman 1, todos >= 0
    restricciones = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    limites = tuple((0, 1) for _ in range(n))
    pesos_iniciales = np.ones(n) / n

    resultado = minimize(volatilidad, pesos_iniciales,
                         method="SLSQP",
                         bounds=limites,
                         constraints=restricciones)

    pesos_opt = resultado.x
    ret = np.dot(pesos_opt, mu_anual)
    vol = volatilidad(pesos_opt)
    sharpe = (ret - rf) / vol

    return {
        "nombre": "Mínima Varianza",
        "pesos": dict(zip(nombres, np.round(pesos_opt, 4))),
        "rendimiento": ret,
        "volatilidad": vol,
        "sharpe": sharpe,
    }


def portafolio_max_sharpe(rendimientos: pd.DataFrame,
                           rf: float = 0.05) -> dict:
    """
    Encuentra el portafolio de máximo ratio de Sharpe.
    """
    n = rendimientos.shape[1]
    mu_anual = rendimientos.mean().values * 252
    cov_anual = rendimientos.cov().values * 252
    nombres = rendimientos.columns.tolist()

    def neg_sharpe(pesos):
        ret = np.dot(pesos, mu_anual)
        vol = np.sqrt(np.dot(pesos.T, np.dot(cov_anual, pesos)))
        return -(ret - rf) / vol

    restricciones = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    limites = tuple((0, 1) for _ in range(n))
    pesos_iniciales = np.ones(n) / n

    resultado = minimize(neg_sharpe, pesos_iniciales,
                         method="SLSQP",
                         bounds=limites,
                         constraints=restricciones)

    pesos_opt = resultado.x
    ret = np.dot(pesos_opt, mu_anual)
    vol = np.sqrt(np.dot(pesos_opt.T, np.dot(cov_anual, pesos_opt)))
    sharpe = (ret - rf) / vol

    return {
        "nombre": "Máximo Sharpe",
        "pesos": dict(zip(nombres, np.round(pesos_opt, 4))),
        "rendimiento": ret,
        "volatilidad": vol,
        "sharpe": sharpe,
    }


def frontera_eficiente(rendimientos: pd.DataFrame,
                       n_puntos: int = 100,
                       rf: float = 0.05) -> pd.DataFrame:
    """
    Calcula la frontera eficiente variando el rendimiento objetivo.
    """
    n = rendimientos.shape[1]
    mu_anual = rendimientos.mean().values * 252
    cov_anual = rendimientos.cov().values * 252

    # Rango de rendimientos objetivo
    ret_min = mu_anual.min() * 0.5
    ret_max = mu_anual.max() * 1.2
    target_returns = np.linspace(ret_min, ret_max, n_puntos)

    frontera = []
    for target in target_returns:
        def volatilidad(pesos):
            return np.sqrt(np.dot(pesos.T, np.dot(cov_anual, pesos)))

        restricciones = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "eq", "fun": lambda w, t=target: np.dot(w, mu_anual) - t},
        ]
        limites = tuple((0, 1) for _ in range(n))
        pesos_iniciales = np.ones(n) / n

        try:
            resultado = minimize(volatilidad, pesos_iniciales,
                                 method="SLSQP",
                                 bounds=limites,
                                 constraints=restricciones)
            if resultado.success:
                frontera.append({
                    "Rendimiento": target,
                    "Volatilidad": resultado.fun,
                    "Sharpe": (target - rf) / resultado.fun,
                })
        except Exception:
            continue

    return pd.DataFrame(frontera)


def tabla_composicion(portafolio: dict) -> pd.DataFrame:
    """Crea tabla con la composición porcentual de un portafolio."""
    pesos = portafolio["pesos"]
    df = pd.DataFrame({
        "Activo": pesos.keys(),
        "Peso": pesos.values(),
        "Peso (%)": [f"{v*100:.1f}%" for v in pesos.values()],
    }).set_index("Activo")
    df = df[df["Peso"] > 0.001]  # Filtrar pesos despreciables
    return df.sort_values("Peso", ascending=False)
