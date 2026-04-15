# =============================================================================
# Dockerfile — Frontend Streamlit (RiskLab Dashboard)
# =============================================================================

FROM python:3.11-slim

LABEL description="RiskLab Streamlit Frontend - Teoria del Riesgo USTA"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# --server.address=0.0.0.0 necesario para acceso externo al contenedor
# --server.headless=true desactiva el dialogo de email al iniciar
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
