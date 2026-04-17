"""
garch_models.py — Modelos de volatilidad condicional.

Módulo 3: ARCH(1), GARCH(1,1), EGARCH(1,1).
Diagnóstico de residuos, tabla comparativa AIC/BIC, pronóstico.
"""

import pandas as pd
import numpy as np
from arch import arch_model
from scipy import stats
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


def ajustar_arch(rendimientos: pd.Series, p: int = 1) -> dict:
    """
    Ajusta un modelo ARCH(p).

    Returns
    -------
    dict con modelo ajustado, resumen y métricas.
    """
    datos = rendimientos.dropna() * 100
    modelo = arch_model(datos, vol="ARCH", p=p, mean="Constant", dist="studentst")
    resultado = modelo.fit(disp="off")

    # Extraer coeficientes y p-valores
    params = resultado.params
    pvalues = resultado.pvalues
    coefs = []
    for name in params.index:
        coefs.append({
            "parametro": name,
            "valor": round(float(params[name]), 6),
            "p_valor": round(float(pvalues[name]), 6),
            "significancia": "***" if pvalues[name] < 0.01 else ("**" if pvalues[name] < 0.05 else ("*" if pvalues[name] < 0.1 else ""))
        })

    return {
        "nombre": f"ARCH({p})",
        "resultado": resultado,
        "aic": resultado.aic,
        "bic": resultado.bic,
        "loglik": resultado.loglikelihood,
        "volatilidad_condicional": resultado.conditional_volatility / 100,
        "residuos_estandarizados": resultado.std_resid,
        "coeficientes": coefs,
        "distribución": "t-Student"
    }


def ajustar_garch(rendimientos: pd.Series, p: int = 1, q: int = 1) -> dict:
    """Ajusta un modelo GARCH(p,q)."""
    datos = rendimientos.dropna() * 100
    modelo = arch_model(datos, vol="Garch", p=p, q=q, mean="Constant", dist="studentst")
    resultado = modelo.fit(disp="off")

    params = resultado.params
    pvalues = resultado.pvalues
    coefs = []
    for name in params.index:
        coefs.append({
            "parametro": name,
            "valor": round(float(params[name]), 6),
            "p_valor": round(float(pvalues[name]), 6),
            "significancia": "***" if pvalues[name] < 0.01 else ("**" if pvalues[name] < 0.05 else ("*" if pvalues[name] < 0.1 else ""))
        })

    return {
        "nombre": f"GARCH({p},{q})",
        "resultado": resultado,
        "aic": resultado.aic,
        "bic": resultado.bic,
        "loglik": resultado.loglikelihood,
        "volatilidad_condicional": resultado.conditional_volatility / 100,
        "residuos_estandarizados": resultado.std_resid,
        "coeficientes": coefs,
        "distribución": "t-Student"
    }


def ajustar_egarch(rendimientos: pd.Series, p: int = 1, q: int = 1) -> dict:
    """Ajusta un modelo EGARCH(p,q) — captura el efecto apalancamiento."""
    datos = rendimientos.dropna() * 100
    modelo = arch_model(datos, vol="EGARCH", p=p, q=q, mean="Constant", dist="studentst")
    resultado = modelo.fit(disp="off")

    params = resultado.params
    pvalues = resultado.pvalues
    coefs = []
    for name in params.index:
        coefs.append({
            "parametro": name,
            "valor": round(float(params[name]), 6),
            "p_valor": round(float(pvalues[name]), 6),
            "significancia": "***" if pvalues[name] < 0.01 else ("**" if pvalues[name] < 0.05 else ("*" if pvalues[name] < 0.1 else ""))
        })

    return {
        "nombre": f"EGARCH({p},{q})",
        "resultado": resultado,
        "aic": resultado.aic,
        "bic": resultado.bic,
        "loglik": resultado.loglikelihood,
        "volatilidad_condicional": resultado.conditional_volatility / 100,
        "residuos_estandarizados": resultado.std_resid,
        "coeficientes": coefs,
        "distribución": "t-Student"
    }


def comparar_modelos(rendimientos: pd.Series) -> pd.DataFrame:
    """
    Ajusta ARCH(1), GARCH(1,1) y EGARCH(1,1) y retorna tabla comparativa.
    """
    model_funcs = [
        lambda: ajustar_arch(rendimientos, p=1),
        lambda: ajustar_garch(rendimientos, p=1, q=1),
        lambda: ajustar_egarch(rendimientos, p=1, q=1),
    ]

    modelos = []
    for func in model_funcs:
        try:
            m = func()
            modelos.append(m)
        except Exception as e:
            # Si un modelo falla, lo ignoramos para no romper el reporte
            continue

    if not modelos:
        raise ValueError("Ninguno de los modelos ARCH/GARCH logró converger con los datos proporcionados.")


    tabla = pd.DataFrame([{
        "Modelo": m["nombre"],
        "Log-Likelihood": round(m["loglik"], 2),
        "AIC": round(m["aic"], 2),
        "BIC": round(m["bic"], 2),
    } for m in modelos]).set_index("Modelo")

    tabla["Mejor AIC"] = tabla["AIC"] == tabla["AIC"].min()
    tabla["Mejor BIC"] = tabla["BIC"] == tabla["BIC"].min()

    return tabla, modelos


def diagnostico_residuos(modelo_dict: dict) -> dict:
    """
    Ejecuta diagnóstico sobre los residuos estandarizados del modelo ajustado.
    """
    residuos = modelo_dict["residuos_estandarizados"].dropna()

    # Jarque-Bera sobre residuos
    jb_stat, jb_pval = stats.jarque_bera(residuos)

    # Estadísticas descriptivas
    media = residuos.mean()
    std = residuos.std()
    skew = residuos.skew() if hasattr(residuos, 'skew') else stats.skew(residuos)
    kurt = residuos.kurtosis() if hasattr(residuos, 'kurtosis') else stats.kurtosis(residuos)

    return {
        "nombre_modelo": modelo_dict["nombre"],
        "media_residuos": round(float(media), 4),
        "std_residuos": round(float(std), 4),
        "asimetria": round(float(skew), 4),
        "curtosis_exc": round(float(kurt), 4),
        "JB_estadistico": float(round(jb_stat, 4)),
        "JB_p_valor": float(round(jb_pval, 6)),
        "residuos_normales": bool(jb_pval > 0.05),
        "interpretacion": (
            "Los residuos estandarizados satisfacen normalidad (p > 0.05). "
            "El modelo captura adecuadamente la dinámica de la volatilidad."
            if jb_pval > 0.05 else
            "Los residuos estandarizados NO satisfacen normalidad. "
            "Se podría considerar una distribución t-Student en la especificación del modelo."
        )
    }


def pronostico_volatilidad(modelo_dict: dict, horizonte: int = 30) -> pd.DataFrame:
    """
    Genera pronóstico de volatilidad N-pasos adelante.

    Parameters
    ----------
    modelo_dict : dict
        Output de ajustar_garch() o similar.
    horizonte : int
        Número de pasos adelante.

    Returns
    -------
    DataFrame con fecha relativa y volatilidad pronosticada.
    """
    resultado = modelo_dict["resultado"]
    # Usamos method='simulation' porque 'analytic' no soporta horizonte > 1 en modelos como EGARCH
    forecast = resultado.forecast(horizon=horizonte, method='simulation', reindex=False)

    # Varianza pronosticada → volatilidad
    # En simulation, variance es un DataFrame (1, horizonte)
    varianza = forecast.variance.iloc[-1].values
    volatilidad = np.sqrt(varianza) / 100  # Des-escalar

    return pd.DataFrame({
        "Día": range(1, horizonte + 1),
        "Volatilidad_Pronosticada": volatilidad
    })


def justificacion_heterocedasticidad(rendimientos: pd.Series) -> str:
    """
    Genera texto justificando la necesidad de modelos de volatilidad condicional.
    """
    rendimientos_sq = rendimientos ** 2

    # Test de efectos ARCH (Engle's ARCH-LM test)
    from statsmodels.stats.diagnostic import het_arch
    lm_stat, lm_pval, _, _ = het_arch(rendimientos.dropna(), nlags=5)

    texto = "### Justificación de heterocedasticidad condicional\n\n"
    texto += f"**Test de efectos ARCH (Engle's LM test, 5 lags):**\n"
    texto += f"- Estadístico LM: {lm_stat:.4f}\n"
    texto += f"- P-valor: {lm_pval:.6f}\n\n"

    if lm_pval < 0.05:
        texto += (
            "✅ **Se rechaza la hipótesis nula** de no-efecto ARCH (p < 0.05). "
            "Existe evidencia estadística de heterocedasticidad condicional en los "
            "rendimientos, lo que justifica el uso de modelos ARCH/GARCH.\n\n"
            "Los rendimientos muestran **agrupamiento de volatilidad**: períodos de "
            "alta volatilidad tienden a estar seguidos por períodos de alta volatilidad, "
            "y viceversa."
        )
    else:
        texto += (
            "⚠️ No se encontró evidencia estadística significativa de efectos ARCH. "
            "Los modelos de volatilidad condicional podrían no ser necesarios para este activo."
        )

    return texto
