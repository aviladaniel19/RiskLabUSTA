# Guía de Contribución — RiskLab USTA

¡Gracias por tu interés en contribuir a RiskLab USTA! Este documento describe cómo puedes participar en el desarrollo del proyecto.

## Reporte de Bugs

Si encuentras un bug:

1. **Verifica que no exista ya** — Busca en [Issues](../../issues)
2. **Crea un nuevo issue** con:
   - Título claro y descriptivo
   - Descripción detallada del comportamiento inesperado
   - Pasos para reproducir el error
   - Comportamiento esperado vs actual
   - Entorno: SO, versión Python, etc.

## Propuesta de Nuevas Características

Para sugerir una nueva característica:

1. Abre un [issue de discusión](../../issues) con el título `[FEATURE]`
2. Describe el caso de uso y beneficio
3. Espera feedback de los maintainers antes de codificar

## Flujo de Contribución

### 1. Fork y Rama

```bash
git clone https://github.com/tu-usuario/RiskLabUSTA.git
cd RiskLabUSTA
git checkout -b feature/nombre-descriptivo
```

### 2. Desarrollo Local

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend (en otra terminal)
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

# Alternativamente, con Docker
docker-compose up -d
```

### 3. Código y Estilo

- Usa **PEP 8** para Python
- Incluye **docstrings** en funciones y clases
- Escribe **type hints** cuando sea posible
- Comenta lógica compleja

Ejemplo:

```python
def calculate_var(returns: np.ndarray, confidence: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR) using historical method.
    
    Args:
        returns: Array of asset returns
        confidence: Confidence level (default: 0.95 = 95%)
    
    Returns:
        VaR at specified confidence level
    """
    return np.percentile(returns, (1 - confidence) * 100)
```

### 4. Tests

- Escribe tests para nuevas funcionalidades
- Localización: `tests/` (crear si no existe)
- Ejecuta: `pytest tests/`

### 5. Commit y Push

```bash
git add .
git commit -m "feat: descripción clara del cambio"
git push origin feature/nombre-descriptivo
```

**Formato de commit** (Conventional Commits):

- `feat:` nueva característica
- `fix:` corrección de bug
- `docs:` cambios en documentación
- `style:` formato, whitespace
- `refactor:` refactorización sin cambios funcionales
- `test:` agregar o actualizar tests
- `chore:` actualizaciones de dependencias, config

### 6. Pull Request

1. Crea un PR desde tu rama hacia `main`
2. Llena la plantilla de PR
3. Espera revisión
4. Realiza cambios si se solicita
5. ¡Merge! 🎉

## Estándares

- **Python**: 3.11+
- **Dependencias**: Pin versiones en `requirements.txt`
- **Documentación**: Toda característica nueva incluye docstring y actualización de README

## Código de Conducta

- Sé respetuoso con otros contribuyentes
- No tolera discriminación ni acoso
- Proporciona feedback constructivo

## Preguntas?

- Abre un [Discussion](../../discussions)
- Contacta a los maintainers

---

**¡Gracias por contribuir a RiskLab USTA!** 🚀
