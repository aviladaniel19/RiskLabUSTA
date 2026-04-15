"""
dependencies.py — Inyección de dependencias con Depends() de FastAPI.

Patrón del curso Python para APIs e IA (Semana 6):
  Las rutas NO contienen lógica directa. Reciben servicios ya
  configurados a través de Depends(), lo que facilita:
    - Testing (se puede reemplazar el servicio por un mock)
    - Desacoplamiento (cambiar yfinance por otro proveedor = 1 archivo)
    - Reutilización (varios endpoints comparten la misma dependencia)
"""

import sys
import os
from functools import lru_cache
from fastapi import Depends

# Agrega el directorio raíz del proyecto al path para importar src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import get_settings, Settings


# ──────────────────────────────────────────────
# SERVICIO DE DATOS FINANCIEROS
# ──────────────────────────────────────────────

class DataService:
    """
    Servicio centralizado de acceso a APIs financieras externas.

    Encapsula yfinance y fredapi. Al estar inyectado con Depends(),
    el cliente de FRED se crea UNA VEZ y se reutiliza en todos los requests.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._fred_client = None  # Lazy initialization

    def get_fred(self):
        """
        Conexión lazy a FRED API.
        Solo crea el cliente la primera vez que se necesita.
        """
        if self._fred_client is None:
            api_key = self.settings.FRED_API_KEY
            if not api_key or api_key == "tu_clave_fred_aqui":
                raise RuntimeError(
                    "FRED_API_KEY no configurada. "
                    "Edita el archivo .env con tu clave de "
                    "https://fred.stlouisfed.org/docs/api/api_key.html"
                )
            from fredapi import Fred
            self._fred_client = Fred(api_key=api_key)
        return self._fred_client


def get_data_service(
    settings: Settings = Depends(get_settings)
) -> DataService:
    """
    Dependencia que provee el servicio de datos.

    Uso en un endpoint:
        @app.get("/macro")
        async def macro(svc: DataService = Depends(get_data_service)):
            fred = svc.get_fred()
            ...
    """
    return DataService(settings)
