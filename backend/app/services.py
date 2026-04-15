"""
services.py — Orquestador de la lógica de negocio.

Patrón del curso Python para APIs e IA (Semana 2 — POO):
  Encapsula todos los módulos de src/ en una clase RiskService.
  Las rutas de FastAPI no hacen cálculos directamente; delegan a este servicio.

Reutilización de src/ existentes:
  - src/api_client.py    → descargar_precios, obtener_rf_actual
  - src/returns.py       → rendimientos_log, estadisticas_descriptivas, pruebas
  - src/indicators.py    → sma, ema, rsi, macd, bollinger_bands, estocastico
  - src/var_cvar.py      → var_portafolio, var_parametrico, var_historico, cvar
  - src/capm.py          → calcular_beta, calcular_capm, tabla_capm
  - src/garch_models.py  → ajustar_garch, comparar_modelos
  - src/markowitz.py     → frontera_eficiente
  - src/signals.py       → generar_senales
  - src/macro_benchmark.py → metricas_benchmark
"""

import sys
import os
import types
from datetime import datetime
from functools import lru_cache

import numpy as np
import pandas as pd

# ── Ruta al directorio src/ (está un nivel arriba de backend/app/)
_SRC_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src")
)
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

# ── Alias de compatibilidad para módulos que usan 'from src.xxx import ...'
# signals.py y macro_benchmark.py del monolito original usan ese prefijo.
# Creamos un alias 'src' en sys.modules que apunte a un módulo paquete
# que redirige hacia los módulos ya agregados en sys.path.
#
# Esto permite reusar el código original SIN modificarlo.
if "src" not in sys.modules:
    _src_mod = types.ModuleType("src")
    _src_mod.__path__ = [_SRC_PATH]
    _src_mod.__package__ = "src"
    sys.modules["src"] = _src_mod

from api_client import (
    descargar_precios,
    descargar_indice,
    obtener_info_ticker,
    obtener_rf_actual,
    obtener_dato_macro,
    obtener_tasa_libre_riesgo,
)
from returns import (
    rendimientos_log,
    rendimientos_simples,
    estadisticas_descriptivas,
    pruebas_normalidad,
    interpretar_hechos_estilizados,
)
from indicators import (
    sma, ema, rsi, macd, bollinger_bands,
    estocastico_desde_close,
)
from var_cvar import (
    var_portafolio,
    var_parametrico,
    var_historico,
    var_montecarlo,
    cvar,
)
from capm import calcular_beta, calcular_capm, discusion_riesgo_sistematico
from garch_models import comparar_modelos, pronostico_volatilidad, ajustar_garch, diagnostico_residuos
from markowitz import simular_portafolios, portafolio_minima_varianza, portafolio_max_sharpe
from signals import resumen_senales
from macro_benchmark import (
    alpha_jensen, tracking_error, information_ratio,
    max_drawdown, interpretacion_benchmark
)


class RiskService:
    """
    Servicio central de cálculo de riesgo financiero.

    Orquesta todos los módulos de src/ y provee métodos de alto nivel
    que los endpoints de FastAPI consumen vía inyección de dependencias.
    """

    def __init__(self, settings):
        self.settings = settings

    # ── Decorador personalizado: registra tiempo de ejecución ──────────
    @staticmethod
    def _log_tiempo(nombre_metodo: str):
        """
        Decorador de comportamiento que registra el tiempo de ejecución.
        Implementa el requerimiento de la rúbrica (buenas prácticas — Semana 1).
        """
        import functools
        import time
        import logging
        logger = logging.getLogger("risklab.services")

        def decorador(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                inicio = time.perf_counter()
                try:
                    resultado = func(*args, **kwargs)
                    ms = (time.perf_counter() - inicio) * 1000
                    logger.info(f"[OK] {nombre_metodo} completado en {ms:.1f}ms")
                    return resultado
                except Exception as e:
                    ms = (time.perf_counter() - inicio) * 1000
                    logger.error(f"[ERR] {nombre_metodo} falló en {ms:.1f}ms: {e}")
                    raise
            return wrapper
        return decorador

    # ════════════════════════════════════════════════════
    # MÉTODOS DE DATOS BASE
    # ════════════════════════════════════════════════════

    def obtener_precios(
        self,
        ticker: str,
        periodo: str = "2y",
        inicio: str = None,
        fin: str = None,
    ) -> pd.DataFrame:
        """Descarga y limpia precios de un ticker desde Yahoo Finance."""
        precios = descargar_precios(
            [ticker], inicio=inicio, fin=fin, periodo=periodo
        )
        precios = precios.ffill().dropna()
        return precios

    def obtener_precios_multiples(
        self,
        tickers: list[str],
        periodo: str = "2y",
    ) -> pd.DataFrame:
        """Descarga precios de múltiples tickers alineados en el mismo DataFrame."""
        precios = descargar_precios(tickers, periodo=periodo)
        precios = precios.ffill().dropna()
        return precios

    def obtener_rendimientos(
        self, precios: pd.DataFrame, tipo: str = "log"
    ) -> pd.DataFrame:
        """Calcula rendimientos log o simples a partir de precios."""
        if tipo == "log":
            return rendimientos_log(precios)
        return rendimientos_simples(precios)

    # ════════════════════════════════════════════════════
    # MÓDULO 1: INDICADORES TÉCNICOS
    # ════════════════════════════════════════════════════

    def calcular_indicadores(
        self,
        ticker: str,
        periodo: str = "2y",
    ) -> dict:
        """Calcula todos los indicadores técnicos para un ticker."""
        precios_df = self.obtener_precios(ticker, periodo=periodo)
        precios = precios_df.iloc[:, 0]

        sma_20 = sma(precios, 20)
        sma_50 = sma(precios, 50)
        ema_20 = ema(precios, 20)
        rsi_14 = rsi(precios, 14)
        macd_df = macd(precios)
        bb = bollinger_bands(precios)
        esto = estocastico_desde_close(precios)

        # Construir lista de puntos (últimos 500 para no saturar la respuesta)
        idx = precios.index[-500:]
        puntos = []
        for fecha in idx:
            def safe(serie, f):
                try:
                    v = serie.loc[f]
                    return None if pd.isna(v) else float(v)
                except Exception:
                    return None

            puntos.append({
                "fecha": str(fecha.date()),
                "precio": float(precios.loc[fecha]),
                "sma_20": safe(sma_20, fecha),
                "sma_50": safe(sma_50, fecha),
                "ema_20": safe(ema_20, fecha),
                "rsi_14": safe(rsi_14, fecha),
                "macd": safe(macd_df["MACD"], fecha),
                "macd_signal": safe(macd_df["Signal"], fecha),
                "macd_hist": safe(macd_df["Histograma"], fecha),
                "bb_superior": safe(bb["Superior"], fecha),
                "bb_media": safe(bb["Media"], fecha),
                "bb_inferior": safe(bb["Inferior"], fecha),
                "estocastico_k": safe(esto["%K"], fecha),
                "estocastico_d": safe(esto["%D"], fecha),
            })

        ultimo = precios.iloc[-1]
        return {
            "ticker": ticker,
            "n_observaciones": len(precios),
            "ultimo_precio": float(ultimo),
            "ultimo_rsi": safe(rsi_14, rsi_14.index[-1]),
            "ultimo_macd": safe(macd_df["MACD"], macd_df.index[-1]),
            "indicadores": puntos,
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 2: RENDIMIENTOS
    # ════════════════════════════════════════════════════

    def calcular_rendimientos_completo(
        self,
        ticker: str,
        periodo: str = "2y",
    ) -> dict:
        """Calcula rendimientos, estadísticas y pruebas de normalidad."""
        precios_df = self.obtener_precios(ticker, periodo=periodo)
        precios = precios_df.iloc[:, 0]

        ret_log = rendimientos_log(precios_df).iloc[:, 0]
        ret_simple = rendimientos_simples(precios_df).iloc[:, 0]
        stats_df = estadisticas_descriptivas(precios_df.rename(columns={precios_df.columns[0]: ticker}))
        stats_row = stats_df.loc[ticker]
        pruebas = pruebas_normalidad(ret_log)
        hechos = interpretar_hechos_estilizados(ret_log, ticker)

        def fmt_prueba(p: dict, key_stat="estadístico", key_interp="interpretación") -> dict:
            return {
                "estadístico": p.get("estadístico", p.get("estadistico", 0)),
                "p_valor": p.get("p_valor", 0),
                "es_normal": p.get("normal", False),
                "interpretación": p.get("interpretación", p.get("interpretacion", "")),
            }

        # Serie de puntos (últimos 500)
        fechas = ret_log.index[-500:]
        puntos = [
            {
                "fecha": str(f.date()),
                "rendimiento_log": float(ret_log.loc[f]),
                "rendimiento_simple": float(ret_simple.loc[f]) if f in ret_simple.index else 0.0,
            }
            for f in fechas
        ]

        return {
            "ticker": ticker,
            "tipo": "log",
            "estadisticas": {
                "media_diaria": float(stats_row.get("Media", 0)),
                "media_anualizada": float(stats_row.get("Media anualizada", 0)),
                "volatilidad_diaria": float(stats_row.get("Desv. Estándar", 0)),
                "volatilidad_anualizada": float(stats_row.get("Volatilidad anualizada", 0)),
                "asimetría": float(stats_row.get("Asimetría (Skewness)", 0)),
                "curtosis_exceso": float(stats_row.get("Curtosis (Excess)", 0)),
                "mínimo": float(stats_row.get("Mínimo", 0)),
                "máximo": float(stats_row.get("Máximo", 0)),
                "n_observaciones": int(stats_row.get("Observaciones", 0)),
            },
            "jarque_bera": fmt_prueba(pruebas["Jarque-Bera"]),
            "shapiro_wilk": fmt_prueba(pruebas["Shapiro-Wilk"]),
            "rendimientos": puntos,
            "hechos_estilizados": hechos,
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 3: GARCH
    # ════════════════════════════════════════════════════

    def calcular_garch(self, ticker: str, periodo: str = "2y") -> dict:
        """Ajusta modelos GARCH y retorna comparación AIC/BIC."""
        precios_df = self.obtener_precios(ticker, periodo=periodo)
        ret = rendimientos_log(precios_df).iloc[:, 0].dropna()

        # comparar_modelos retorna (tabla_df, lista_de_modelos)
        tabla, modelos_lista = comparar_modelos(ret)

        # Obtener el mejor modelo (menor AIC) para pronóstico
        mejor_modelo_dict = min(modelos_lista, key=lambda m: m["aic"])
        mejor_nombre = mejor_modelo_dict["nombre"]

        # Pronóstico de volatilidad usando el mejor modelo
        pronostico_df = pronostico_volatilidad(mejor_modelo_dict, horizonte=10)
        pronostico_lista = pronostico_df["Volatilidad_Pronosticada"].tolist()

        # Diagnóstico de residuos del mejor modelo
        diag = diagnostico_residuos(mejor_modelo_dict)

        # Construir lista de modelos para la respuesta
        modelos_comparados = []
        mejor_aic = min(m["aic"] for m in modelos_lista)
        for m in modelos_lista:
            modelos_comparados.append({
                "nombre": m["nombre"],
                "aic": round(m["aic"], 2),
                "bic": round(m["bic"], 2),
                "log_likelihood": round(m["loglik"], 2),
                "volatilidad_anualizada": round(
                    float(m["volatilidad_condicional"].iloc[-1]) * np.sqrt(252), 4
                ),
                "es_mejor": m["aic"] == mejor_aic,
            })

        return {
            "ticker": ticker,
            "modelos_comparados": modelos_comparados,
            "mejor_modelo": mejor_nombre,
            "pronostico_volatilidad": pronostico_lista,
            "jarque_bera_residuos": {
                "estadístico": diag["JB_estadistico"],
                "p_valor": diag["JB_p_valor"],
                "es_normal": diag["residuos_normales"],
                "interpretación": diag["interpretacion"],
            },
            "interpretacion": (
                f"Mejor modelo por AIC/BIC: {mejor_nombre}. "
                "Se verifica el diagnóstico de residuos estandarizados."
            ),
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 4: CAPM
    # ════════════════════════════════════════════════════

    def calcular_capm_completo(
        self,
        tickers: list[str],
        periodo: str = "2y",
    ) -> dict:
        """Calcula Beta y CAPM para todos los tickers vs benchmark."""
        benchmark = self.settings.BENCHMARK_TICKER
        rf = obtener_rf_actual()

        precios = self.obtener_precios_multiples(tickers + [benchmark], periodo=periodo)
        ret = rendimientos_log(precios)

        ret_mkt = ret[benchmark]
        ret_mkt_anual = float(ret_mkt.mean() * 252)

        activos = []
        for t in tickers:
            if t not in ret.columns:
                continue
            beta_info = calcular_beta(ret[t], ret_mkt)
            capm_info = calcular_capm(
                beta_info["beta"], rf=rf, rendimiento_mercado=ret_mkt_anual
            )
            re_pct = capm_info["rendimiento_esperado"]
            activos.append({
                "ticker": t,
                "beta": beta_info["beta"],
                "alpha_jensen": beta_info["alpha"] * 252,
                "r_cuadrado": beta_info["r_cuadrado"],
                "clasificacion": capm_info["clasificacion"],
                "rendimiento_esperado_capm": re_pct,
                "rendimiento_esperado_capm_pct": f"{re_pct*100:.2f}%",
            })

        return {
            "benchmark": benchmark,
            "rf_actual": rf,
            "rf_actual_pct": f"{rf*100:.2f}%",
            "rendimiento_mercado_anual": ret_mkt_anual,
            "activos": activos,
            "discusion": discusion_riesgo_sistematico(),
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 5: VaR y CVaR
    # ════════════════════════════════════════════════════

    def calcular_var(
        self,
        tickers: list[str],
        pesos: list[float],
        nivel_confianza: float = 0.95,
        periodo: str = "2y",
    ) -> dict:
        """Calcula VaR paramétrico, histórico, Montecarlo y CVaR del portafolio."""
        precios = self.obtener_precios_multiples(tickers, periodo=periodo)
        ret = rendimientos_log(precios)

        pesos_np = np.array(pesos)
        ret_port = (ret * pesos_np).sum(axis=1)

        vp = var_parametrico(ret_port, nivel_confianza)
        vh = var_historico(ret_port, nivel_confianza)
        vm = var_montecarlo(ret_port, nivel_confianza, self.settings.MONTECARLO_N_SIM)
        cv = cvar(ret_port, nivel_confianza)

        def fmt(v: dict) -> dict:
            return {
                "metodo": v["metodo"],
                "nivel_confianza": v["nivel_confianza"],
                "var_diario": float(v["var_diario"]),
                "var_diario_pct": f"{v['var_diario']*100:.2f}%",
                "var_anual": float(v["var_anual"]),
                "var_anual_pct": f"{v['var_anual']*100:.2f}%",
                "interpretacion": v["interpretacion"],
            }

        ret_anual = float(ret_port.mean() * 252)
        vol_anual = float(ret_port.std() * np.sqrt(252))

        return {
            "tickers": tickers,
            "pesos": pesos,
            "nivel_confianza": nivel_confianza,
            "parametrico": fmt(vp),
            "historico": fmt(vh),
            "montecarlo": fmt(vm),
            "cvar": {
                "cvar_diario": float(cv["cvar_diario"]),
                "cvar_diario_pct": f"{cv['cvar_diario']*100:.2f}%",
                "interpretacion": cv["interpretacion"],
            },
            "rendimiento_portafolio_anual": ret_anual,
            "volatilidad_portafolio_anual": vol_anual,
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 6: MARKOWITZ
    # ════════════════════════════════════════════════════

    def calcular_frontera(
        self,
        tickers: list[str],
        periodo: str = "2y",
        n_simulaciones: int = 10_000,
    ) -> dict:
        """Simula portafolios y calcula la frontera eficiente."""
        precios = self.obtener_precios_multiples(tickers, periodo=periodo)
        ret = rendimientos_log(precios)
        rf = obtener_rf_actual()

        resultados = simular_portafolios(ret, n_simulaciones=n_simulaciones, rf=rf)
        # portafolio_minima_varianza y portafolio_max_sharpe trabajan sobre ret directamente
        opt_mv_dict = portafolio_minima_varianza(ret, rf=rf)
        opt_ms_dict = portafolio_max_sharpe(ret, rf=rf)

        corr = ret.corr().round(4).to_dict()

        # Solo mandamos max 2000 puntos al frontend para no sobrecargar
        # (columnas del DataFrame de simular_portafolios: Rendimiento, Volatilidad, Sharpe)
        muestra = resultados.sample(min(2000, len(resultados)), random_state=42)
        puntos = [
            {"rendimiento": row["Rendimiento"], "volatilidad": row["Volatilidad"], "sharpe": row["Sharpe"]}
            for _, row in muestra.iterrows()
        ]

        def fmt_portafolio(opt_dict: dict, t_list: list[str]) -> dict:
            pesos_dict = opt_dict["pesos"]
            return {
                "tipo": opt_dict["nombre"],
                "tickers": list(pesos_dict.keys()),
                "pesos": list(pesos_dict.values()),
                "rendimiento_anual": float(opt_dict["rendimiento"]),
                "volatilidad_anual": float(opt_dict["volatilidad"]),
                "sharpe_ratio": float(opt_dict["sharpe"]),
            }

        return {
            "tickers": tickers,
            "n_simulaciones": n_simulaciones,
            "portafolio_min_varianza": fmt_portafolio(opt_mv_dict, tickers),
            "portafolio_max_sharpe": fmt_portafolio(opt_ms_dict, tickers),
            "puntos_simulados": puntos,
            "matriz_correlacion": corr,
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 7: SEÑALES Y ALERTAS
    # ════════════════════════════════════════════════════

    def calcular_alertas(
        self,
        tickers: list[str],
        periodo: str = "1y",
    ) -> dict:
        """Genera señales automáticas para cada ticker."""
        alertas = []
        for t in tickers:
            try:
                precios_df = self.obtener_precios(t, periodo=periodo)
                precios = precios_df.iloc[:, 0]
                res = resumen_senales(precios, nombre=t)
                senales_list = res["senales"]

                def get_senal(ind_name):
                    for s in senales_list:
                        if ind_name in s.get("indicador", ""):
                            return s.get("señal", "N/D")
                    return "N/D"

                # Mapear veredicto al formato esperado
                veredicto = res["veredicto"]
                senal_global = "COMPRAR" if "COMPRA" in veredicto else ("VENDER" if "VENTA" in veredicto else "MANTENER")

                alertas.append({
                    "ticker": t,
                    "senal_global": senal_global,
                    "macd_senal": get_senal("MACD"),
                    "rsi_senal": get_senal("RSI"),
                    "bollinger_senal": get_senal("Bollinger"),
                    "cruce_medias": get_senal("Cruce"),
                    "estocastico_senal": get_senal("Estocástico"),
                    "ultimo_precio": float(precios.iloc[-1]),
                    "rsi_actual": None,
                    "texto_interpretativo": res["veredicto"],
                })
            except Exception as e:
                alertas.append({
                    "ticker": t,
                    "senal_global": "MANTENER",
                    "macd_senal": "N/D",
                    "rsi_senal": "N/D",
                    "bollinger_senal": "N/D",
                    "cruce_medias": "N/D",
                    "estocastico_senal": "N/D",
                    "ultimo_precio": 0.0,
                    "rsi_actual": None,
                    "texto_interpretativo": f"Error: {e}",
                })

        return {
            "tickers": tickers,
            "alertas": alertas,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

    # ════════════════════════════════════════════════════
    # MÓDULO 8: MACRO Y BENCHMARK
    # ════════════════════════════════════════════════════

    def calcular_macro(
        self,
        tickers: list[str],
        pesos: list[float],
        periodo: str = "2y",
    ) -> dict:
        """Obtiene datos macro de FRED y calcula métricas vs benchmark."""
        benchmark_ticker = self.settings.BENCHMARK_TICKER

        precios = self.obtener_precios_multiples(
            tickers + [benchmark_ticker], periodo=periodo
        )
        ret = rendimientos_log(precios)

        pesos_np = np.array(pesos)
        ret_port = (ret[tickers] * pesos_np).sum(axis=1)
        ret_bench = ret[benchmark_ticker]

        rf = obtener_rf_actual()

        # Calcular métricas de benchmark usando funciones de macro_benchmark.py
        alpha = alpha_jensen(ret_port, ret_bench, rf)
        te = tracking_error(ret_port, ret_bench)
        ir = information_ratio(ret_port, ret_bench)
        interpretacion = interpretacion_benchmark(ret_port, ret_bench, rf)

        def metricas_serie(r, rf_rate):
            ret_anual = float(r.mean() * 252)
            vol_anual = float(r.std() * np.sqrt(252))
            sharpe = (ret_anual - rf_rate) / vol_anual if vol_anual > 0 else 0
            mdd = float(max_drawdown(r))
            ret_acum = float((1 + r).prod() - 1)
            return {
                "rendimiento_acumulado": ret_acum,
                "rendimiento_anualizado": ret_anual,
                "volatilidad_anualizada": vol_anual,
                "sharpe_ratio": round(sharpe, 4),
                "maximo_drawdown": mdd,
            }

        metricas_port = metricas_serie(ret_port, rf)
        metricas_bench = metricas_serie(ret_bench, rf)

        # Indicadores macro
        macro_series = {
            "DGS3MO": ("Tasa Libre de Riesgo (T-Bill 3M)", "%"),
            "CPIAUCSL": ("Inflación (CPI)", "índice"),
            "DFF": ("Federal Funds Rate", "%"),
            "T10Y2Y": ("Spread 10Y-2Y", "puntos base"),
        }
        indicadores = []
        for serie, (nombre, unidad) in macro_series.items():
            try:
                datos = obtener_dato_macro(serie)
                indicadores.append({
                    "nombre": nombre,
                    "serie_fred": serie,
                    "valor_actual": float(datos.iloc[-1]),
                    "unidad": unidad,
                    "fecha_actualizacion": str(datos.index[-1].date()),
                })
            except Exception:
                indicadores.append({
                    "nombre": nombre,
                    "serie_fred": serie,
                    "valor_actual": 0.0,
                    "unidad": unidad,
                    "fecha_actualizacion": "N/D",
                })

        return {
            "indicadores_macro": indicadores,
            "desempeno_portafolio": metricas_port,
            "desempeno_benchmark": metricas_bench,
            "alpha_jensen": float(alpha),
            "tracking_error": float(te),
            "information_ratio": float(ir),
            "interpretacion": interpretacion,
        }
