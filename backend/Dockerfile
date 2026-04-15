# =============================================================================
# Dockerfile — Backend FastAPI (RiskLab API)
#
# GUIA DIDACTICA (para sustentacion):
#
#  FROM    = Imagen base. python:3.11-slim es Python oficial liviano (~150MB)
#  WORKDIR = Carpeta de trabajo DENTRO del contenedor
#  COPY    = Copia archivos desde tu PC al contenedor
#  RUN     = Ejecuta comandos durante la CONSTRUCCION (no en runtime)
#  EXPOSE  = Documenta el puerto (docker-compose lo publica realmente)
#  CMD     = Comando que ejecuta el contenedor al ARRANCAR
#
#  TRUCO DE CACHE:
#    Se copia requirements.txt ANTES que el codigo. Si el codigo cambia
#    pero requirements.txt no, Docker no reinstala las librerias.
#    Resultado: builds 10x mas rapidos en iteraciones de desarrollo.
# =============================================================================

FROM python:3.11-slim

LABEL maintainer="risklab@usta.edu.co"
LABEL description="RiskLab FastAPI Backend - Teoria del Riesgo USTA"

WORKDIR /app

# Evita archivos .pyc y bufferiza logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias del sistema (build-essential para compilar arch/GARCH)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Capa de dependencias Python (se cachea si requirements.txt no cambia)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Codigo fuente (despues de deps para aprovechar cache)
COPY . .

EXPOSE 8000

# --host 0.0.0.0 es OBLIGATORIO para que el puerto sea accesible desde fuera
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
