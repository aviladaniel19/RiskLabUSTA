"""
capm.py — CAPM y riesgo sistemático.

Módulo 4: Beta por regresión, CAPM con Rf desde FRED API,
clasificación de activos, discusión de diversificación.
"""

import pandas as pd
import numpy as np
from scipy import stats
from src.api_client import obtener_rf_actual


def calcular_beta(rendimientos_activo: pd.Series,
                  rendimientos_indice: pd.Series) -> dict:
    """
    Calcula Beta del activo por regresión OLS:
        R_activo = alpha + beta * R_indice + epsilon

    Returns
    -------
    dict con beta, alpha, R², p-valor, error estándar.
    """
    # Alinear índices
    datos = pd.DataFrame({
        "activo": rendimientos_activo,
        "indice": rendimientos_indice
    }).dropna()

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        datos["indice"], datos["activo"]
    )

    return {
        "beta": round(slope, 4),
        "alpha": round(intercept, 6),
        "r_cuadrado": round(r_value**2, 4),
        "p_valor": round(p_value, 6),
        "error_estandar": round(std_err, 6),
    }


def clasificar_beta(beta: float) -> str:
    """Clasifica un activo según su Beta."""
    if beta > 1.2:
        return "🔴 Agresivo"
    elif beta > 0.8:
        return "🟡 Neutro"
    else:
        return "🟢 Defensivo"


def calcular_capm(beta: float, rf: float = None,
                  rendimiento_mercado: float = None) -> dict:
    """
    Calcula el rendimiento esperado según el CAPM:
        E(R_i) = R_f + β_i × (E(R_m) - R_f)

    Parameters
    ----------
    beta : float
        Beta del activo.
    rf : float, optional
        Tasa libre de riesgo (anualizada). Si None, la obtiene de FRED.
    rendimiento_mercado : float
        Rendimiento esperado del mercado (anualizado).
    """
    if rf is None:
        rf = obtener_rf_actual()

    if rendimiento_mercado is None:
        rendimiento_mercado = 0.10  # 10% histórico del S&P 500

    prima_riesgo = rendimiento_mercado - rf
    rendimiento_esperado = rf + beta * prima_riesgo

    return {
        "beta": beta,
        "rf": rf,
        "rendimiento_mercado": rendimiento_mercado,
        "prima_riesgo_mercado": prima_riesgo,
        "rendimiento_esperado": rendimiento_esperado,
        "clasificacion": clasificar_beta(beta),
    }


def tabla_capm(rendimientos: pd.DataFrame,
               rendimientos_indice: pd.Series,
               rf: float = None) -> pd.DataFrame:
    """
    Calcula Beta y CAPM para todos los activos.

    Returns
    -------
    DataFrame con Beta, rendimiento esperado, clasificación por activo.
    """
    if rf is None:
        rf = obtener_rf_actual()

    # Rendimiento anualizado del mercado
    r_mercado_anual = rendimientos_indice.mean() * 252

    resultados = []
    for col in rendimientos.columns:
        beta_info = calcular_beta(rendimientos[col], rendimientos_indice)
        capm_info = calcular_capm(
            beta_info["beta"], rf=rf,
            rendimiento_mercado=r_mercado_anual
        )

        resultados.append({
            "Activo": col,
            "Beta": beta_info["beta"],
            "Alpha (Jensen)": beta_info["alpha"] * 252,  # Anualizar
            "R²": beta_info["r_cuadrado"],
            "Rf (anual)": f"{rf*100:.2f}%",
            "E(Ri) CAPM": f"{capm_info['rendimiento_esperado']*100:.2f}%",
            "Clasificación": capm_info["clasificacion"],
        })

    return pd.DataFrame(resultados).set_index("Activo")


def discusion_riesgo_sistematico() -> str:
    """Genera texto de discusión sobre riesgo sistemático vs no sistemático."""
    return """
### Riesgo Sistemático vs. No Sistemático

**Riesgo Sistemático (no diversificable):**
- Afecta a todo el mercado: recesiones, cambios en tasas de interés, inflación, eventos geopolíticos.
- Se mide con **Beta (β)**: β > 1 → mayor sensibilidad al mercado; β < 1 → menor sensibilidad.
- NO puede eliminarse mediante diversificación.
- Es el único riesgo que el mercado compensa con rendimiento adicional (prima de riesgo).

**Riesgo No Sistemático (diversificable):**
- Específico de una empresa o sector: decisiones gerenciales, demandas, competencia.
- Puede reducirse significativamente añadiendo activos poco correlacionados al portafolio.
- No genera rendimiento adicional según el CAPM — por eso es importante diversificar.

**Diversificación:**
- La correlación entre activos determina qué tan efectiva es la diversificación.
- Portafolios con activos de baja correlación logran menor volatilidad para un nivel dado de rendimiento.
- Markowitz formalizó esta idea con la **frontera eficiente** (Módulo 6).
"""
