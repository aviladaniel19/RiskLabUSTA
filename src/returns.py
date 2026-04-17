"""
returns.py — Análisis estadístico de rendimientos.

Módulo 2: rendimientos simples/logarítmicos, estadísticas descriptivas,
pruebas de normalidad (Jarque-Bera, Shapiro-Wilk), hechos estilizados.
"""

import pandas as pd
import numpy as np
from scipy import stats


def rendimientos_simples(precios: pd.DataFrame) -> pd.DataFrame:
    """Calcula rendimientos simples: r_t = (P_t - P_{t-1}) / P_{t-1}."""
    return precios.pct_change().dropna()


def rendimientos_log(precios: pd.DataFrame) -> pd.DataFrame:
    """Calcula rendimientos logarítmicos: r_t = ln(P_t / P_{t-1})."""
    return np.log(precios / precios.shift(1)).dropna()


def estadisticas_descriptivas(rendimientos: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula estadísticas descriptivas completas para cada activo.

    Returns
    -------
    DataFrame con: media, desv. estándar, asimetría, curtosis, mínimo, máximo, N.
    """
    estadisticas = pd.DataFrame({
        "Media": rendimientos.mean(),
        "Media anualizada": rendimientos.mean() * 252,
        "Desv. Estándar": rendimientos.std(),
        "Volatilidad anualizada": rendimientos.std() * np.sqrt(252),
        "Asimetría (Skewness)": rendimientos.skew(),
        "Curtosis (Excess)": rendimientos.kurtosis(),  # excess kurtosis (Fisher)
        "Mínimo": rendimientos.min(),
        "Máximo": rendimientos.max(),
        "Observaciones": rendimientos.count()
    })

    return estadisticas.round(6)


def prueba_jarque_bera(rendimientos: pd.Series) -> dict:
    """
    Test de Jarque-Bera para normalidad.

    H0: Los datos siguen una distribución normal.
    Si p-valor < 0.05 → se rechaza H0 → NO son normales.
    """
    stat, p_value = stats.jarque_bera(rendimientos.dropna())
    return {
        "estadístico": round(stat, 4),
        "p_valor": round(p_value, 6),
        "normal": p_value > 0.05,
        "interpretación": (
            "No se rechaza H₀: los rendimientos podrían seguir una distribución normal."
            if p_value > 0.05 else
            "Se rechaza H₀: los rendimientos NO siguen una distribución normal "
            "(colas pesadas y/o asimetría significativa)."
        )
    }


def prueba_shapiro_wilk(rendimientos: pd.Series, max_obs: int = 5000) -> dict:
    """
    Test de Shapiro-Wilk para normalidad.
    Nota: Shapiro-Wilk acepta máximo 5000 observaciones.

    H0: Los datos siguen una distribución normal.
    """
    datos = rendimientos.dropna()
    if len(datos) > max_obs:
        datos = datos.sample(max_obs, random_state=42)

    stat, p_value = stats.shapiro(datos)
    return {
        "estadístico": round(stat, 6),
        "p_valor": round(p_value, 6),
        "normal": p_value > 0.05,
        "interpretación": (
            "No se rechaza H₀: los rendimientos podrían seguir una distribución normal."
            if p_value > 0.05 else
            "Se rechaza H₀: los rendimientos NO siguen una distribución normal."
        )
    }


def pruebas_normalidad(rendimientos: pd.Series) -> dict:
    """Ejecuta ambas pruebas de normalidad y retorna resultados."""
    return {
        "Jarque-Bera": prueba_jarque_bera(rendimientos),
        "Shapiro-Wilk": prueba_shapiro_wilk(rendimientos)
    }


def tabla_pruebas_normalidad(rendimientos: pd.DataFrame) -> pd.DataFrame:
    """
    Ejecuta pruebas de normalidad para todos los activos.

    Returns
    -------
    DataFrame con resultados de Jarque-Bera y Shapiro-Wilk por activo.
    """
    resultados = []
    for col in rendimientos.columns:
        jb = prueba_jarque_bera(rendimientos[col])
        sw = prueba_shapiro_wilk(rendimientos[col])
        resultados.append({
            "Activo": col,
            "JB Estadístico": jb["estadístico"],
            "JB p-valor": jb["p_valor"],
            "JB Normal": "✅ Sí" if jb["normal"] else "❌ No",
            "SW Estadístico": sw["estadístico"],
            "SW p-valor": sw["p_valor"],
            "SW Normal": "✅ Sí" if sw["normal"] else "❌ No",
        })

    return pd.DataFrame(resultados).set_index("Activo")


def interpretar_hechos_estilizados(rendimientos: pd.Series,
                                    nombre: str = "activo") -> str:
    """
    Genera texto interpretativo sobre los hechos estilizados observados.
    """
    kurt = rendimientos.kurtosis()
    skew = rendimientos.skew()

    texto = f"**Hechos estilizados de {nombre}:**\n\n"

    # Colas pesadas
    if kurt > 0:
        texto += (
            f"- **Colas pesadas (leptocurtosis):** La curtosis en exceso es "
            f"{kurt:.2f} (> 0), lo que indica que los rendimientos tienen colas "
            f"más gruesas que la distribución normal. Esto implica mayor probabilidad "
            f"de eventos extremos (grandes pérdidas o ganancias).\n\n"
        )
    else:
        texto += f"- La curtosis en exceso es {kurt:.2f}, cercana a la distribución normal.\n\n"

    # Asimetría
    if abs(skew) > 0.5:
        direccion = "negativa (izquierda)" if skew < 0 else "positiva (derecha)"
        texto += (
            f"- **Asimetría:** La distribución muestra asimetría {direccion} "
            f"(skewness = {skew:.2f}). "
        )
        if skew < 0:
            texto += "Esto sugiere que las caídas extremas son más frecuentes que las subidas extremas.\n\n"
        else:
            texto += "Esto sugiere que hay más eventos extremos positivos.\n\n"
    else:
        texto += f"- La distribución es aproximadamente simétrica (skewness = {skew:.2f}).\n\n"

    # Agrupamiento de volatilidad
    texto += (
        "- **Agrupamiento de volatilidad (volatility clustering):** Los períodos "
        "de alta volatilidad tienden a seguirse entre sí. Esto se evidencia en la "
        "serie temporal de rendimientos al cuadrado y es la base para los modelos GARCH.\n\n"
    )

    # Efecto apalancamiento
    texto += (
        "- **Efecto apalancamiento:** Las caídas del mercado tienden a aumentar la "
        "volatilidad más que las subidas de la misma magnitud. Los modelos EGARCH y "
        "GJR-GARCH capturan este efecto asimétrico.\n"
    )
    
    return texto

def calcular_qq_plot(rendimientos: pd.Series, n_puntos: int = 100) -> list[dict]:
    """
    Genera puntos para un gráfico Q-Q (Cuantil-Cuantil).
    Compara los cuantiles empíricos de los rendimientos con los cuantiles
    teóricos de una distribución normal estándar.
    """
    datos = rendimientos.dropna().sort_values()
    n = len(datos)
    
    # Cuantiles teóricos (Z-scores)
    # Usamos una muestra de n_puntos para no saturar el frontend
    proporciones = np.linspace(0.01, 0.99, n_puntos)
    teoricos = stats.norm.ppf(proporciones)
    
    # Cuantiles empíricos (estandarizados)
    media, std = datos.mean(), datos.std()
    datos_std = (datos - media) / std
    empiricos = np.percentile(datos_std, proporciones * 100)
    
    puntos = []
    for t, e in zip(teoricos, empiricos):
        puntos.append({"teorico": round(float(t), 4), "empirico": round(float(e), 4)})
    
    return puntos


def calcular_stats_boxplot(rendimientos: pd.Series) -> dict:
    """Calcula los 5 números estadísticos para un Boxplot."""
    d = rendimientos.dropna()
    return {
        "min": float(d.min()),
        "q1": float(np.percentile(d, 25)),
        "med": float(d.median()),
        "q3": float(np.percentile(d, 75)),
        "max": float(d.max())
    }


def test_kupiec(excepciones: int, n_observaciones: int, nivel_confianza: float) -> dict:
    """
    Realiza el Test de Kupiec (Proportion of Failures - POF) para backtesting de VaR.
    
    H0: El modelo de VaR es correcto (la tasa de fallos observada es igual a la esperada).
    Si p-valor < 0.05 → se rechaza el modelo.
    """
    p = 1 - nivel_confianza  # Probabilidad de excepción esperada
    n = n_observaciones
    x = excepciones
    
    if x == 0:
        # Si no hay excepciones, el modelo es conservador/bueno
        return {"estadistico": 0.0, "p_valor": 1.0, "valido": True, "interpretacion": "Modelo válido (conservador)."}

    # Tasa observada
    p_hat = x / n
    
    # Likelihood Ratio (LR)
    try:
        lr = -2 * (
            (n - x) * np.log(1 - p) + x * np.log(p) -
            (n - x) * np.log(1 - p_hat) - x * np.log(p_hat)
        )
        # El estadístico LR sigue una chi-cuadrado con 1 grado de libertad
        p_value = 1 - stats.chi2.cdf(lr, df=1)
    except Exception:
        return {"estadistico": 0.0, "p_valor": 0.01, "valido": False, "interpretacion": "Error en cálculo de Kupiec."}

    return {
        "estadistico": round(float(lr), 4),
        "p_valor": round(float(p_value), 6),
        "valido": bool(p_value > 0.05),
        "interpretacion": (
            "Modelo Válido: No se rechaza la precisión del VaR."
            if p_value > 0.05 else
            "Modelo Inválido: La tasa de excepciones difiere significativamente de la esperada."
        )
    }
