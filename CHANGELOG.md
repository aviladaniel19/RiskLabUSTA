# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/) y este proyecto sigue [Semantic Versioning](https://semver.org/).

## [2.0.0] — 2026-04-15

### Added

- **Backend (FastAPI)**: API REST completa con 9 endpoints para análisis cuantitativo
  - Endpoints para técnico, rendimientos, GARCH, CAPM, VaR, Markowitz, señales, macro
  - Swagger/OpenAPI UI en `/docs`
  - Inyección de dependencias con Pydantic
  - Configuración centralizada con `BaseSettings`

- **Frontend (Streamlit)**: Dashboard interactivo con 8 páginas
  - Análisis técnico con indicadores Bollinger, RSI, MACD
  - Backtesting de estrategias
  - Modelos GARCH para volatilidad
  - CAPM y beta cálculos
  - Value at Risk (VaR) y Conditional VaR
  - Optimización de portafolio (Markowitz)
  - Señales de trading automatizadas
  - Indicadores macroeconómicos

- **Docker**: `docker-compose.yml` para despliegue de desarrollo
  - Contenedores separados para backend y frontend
  - Volúmenes para hot-reload
  - Health checks configurados
  - Red interna para comunicación segura

- **APIs Externas**:
  - Yahoo Finance para precios históricos
  - FRED (Federal Reserve) para tasas libre de riesgo
  - Soporte para múltiples activos y portafolios

- **Documentación**:
  - README completo con instrucciones de instalación
  - Guía de contribución (CONTRIBUTING.md)
  - Changelog (este archivo)
  - .env.example con variables de configuración

### Changed

- Migración a Python 3.11+ para mejor rendimiento
- Actualización de dependencias a versiones estables
- Refactorización de módulos de cálculo para reutilización

### Fixed

- Correcciones en cálculos de volatilidad
- Mejora en manejo de errores de API

## [1.0.0] — 2025-09-01

### Added

- Versión inicial del proyecto
- Módulos básicos de análisis (returns, volatility, correlation)
- Dashboard básico en Streamlit
- Integración con Yahoo Finance

---

**Versiones futuras**: Envíanos tus feature requests en [Issues](../../issues)
