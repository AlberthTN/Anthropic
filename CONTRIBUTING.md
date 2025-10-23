# 🤝 Guía de Contribución - Claude Programming Agent

¡Gracias por tu interés en contribuir al Claude Programming Agent! Esta guía te ayudará a empezar y te proporcionará las mejores prácticas para contribuir efectivamente al proyecto.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [Cómo Contribuir](#cómo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Reportar Bugs](#reportar-bugs)
- [Solicitar Funcionalidades](#solicitar-funcionalidades)
- [Documentación](#documentación)
- [Testing](#testing)
- [Comunidad](#comunidad)

## 📜 Código de Conducta

Este proyecto adhiere a un código de conducta. Al participar, se espera que mantengas este código. Por favor reporta comportamientos inaceptables a [maintainer@email.com].

### Nuestros Compromisos

- **Ser inclusivos**: Damos la bienvenida a contribuidores de todos los backgrounds
- **Ser respetuosos**: Tratamos a todos con respeto y profesionalismo
- **Ser constructivos**: Proporcionamos feedback útil y constructivo
- **Ser colaborativos**: Trabajamos juntos hacia objetivos comunes

## 🚀 Cómo Contribuir

### Tipos de Contribuciones Bienvenidas

1. **🐛 Reportar Bugs**
   - Errores en el código
   - Problemas de rendimiento
   - Problemas de documentación

2. **✨ Nuevas Funcionalidades**
   - Nuevos comandos Slack
   - Mejoras en la IA
   - Integraciones adicionales

3. **📚 Documentación**
   - Mejorar documentación existente
   - Agregar ejemplos
   - Traducir documentación

4. **🧪 Testing**
   - Escribir tests unitarios
   - Mejorar cobertura de tests
   - Tests de integración

5. **🔧 Mejoras de Código**
   - Refactoring
   - Optimizaciones de rendimiento
   - Mejoras de seguridad

## 🛠️ Configuración del Entorno de Desarrollo

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork

git clone https://github.com/tu-usuario/claude-programming-agent.git
cd claude-programming-agent

# Agregar upstream remote
git remote add upstream https://github.com/original-owner/claude-programming-agent.git
```

### 2. Configurar Entorno Virtual

```bash
# Crear entorno virtual
python -m venv dev-env

# Activar entorno virtual
# Windows:
dev-env\Scripts\activate
# macOS/Linux:
source dev-env/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt
```

### 3. Configurar Pre-commit Hooks

```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Ejecutar en todos los archivos (opcional)
pre-commit run --all-files
```

### 4. Configurar Variables de Entorno de Desarrollo

```bash
# Copiar archivo de ejemplo
cp .env.example .env.dev

# Configurar variables para desarrollo
# Usar valores de test/desarrollo, no producción
```

### 5. Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con cobertura
pytest --cov=src --cov-report=html

# Ejecutar tests específicos
pytest tests/test_agent.py -v
```

## 📏 Estándares de Código

### Estilo de Código Python

Seguimos [PEP 8](https://pep8.org/) con algunas modificaciones:

```python
# ✅ BUENO
def process_user_message(user_id: str, message: str) -> dict:
    """
    Procesa un mensaje del usuario y genera una respuesta.
    
    Args:
        user_id: ID único del usuario
        message: Mensaje del usuario
        
    Returns:
        dict: Respuesta procesada con metadata
        
    Raises:
        ValueError: Si el mensaje está vacío
    """
    if not message.strip():
        raise ValueError("El mensaje no puede estar vacío")
    
    return {
        "response": "Respuesta procesada",
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }

# ❌ MALO
def processMsg(uid,msg):
    if msg=="": return None
    return {"resp":"ok","uid":uid}
```

### Configuración de Herramientas

#### Black (Formateo de Código)

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### isort (Ordenamiento de Imports)

```toml
# pyproject.toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]
```

#### flake8 (Linting)

```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist
```

#### mypy (Type Checking)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Estructura de Archivos

```
src/
├── agents/
│   ├── __init__.py
│   ├── claude_agent.py          # Agente principal
│   └── base_agent.py           # Clase base para agentes
├── slack/
│   ├── __init__.py
│   ├── handlers.py             # Manejadores de eventos Slack
│   ├── commands.py             # Comandos disponibles
│   └── utils.py                # Utilidades Slack
├── tools/
│   ├── __init__.py
│   ├── code_analyzer.py        # Análisis de código
│   ├── code_generator.py       # Generación de código
│   └── memory_manager.py       # Gestión de memoria/BigQuery
├── utils/
│   ├── __init__.py
│   ├── config.py               # Configuración
│   ├── logging.py              # Configuración de logging
│   └── validators.py           # Validadores
└── config/
    ├── __init__.py
    ├── settings.py             # Configuraciones
    └── constants.py            # Constantes
```

### Convenciones de Naming

```python
# Variables y funciones: snake_case
user_message = "Hello"
def process_message():
    pass

# Clases: PascalCase
class ClaudeAgent:
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_TOKENS = 4096
API_BASE_URL = "https://api.anthropic.com"

# Archivos: snake_case.py
# claude_agent.py
# memory_manager.py

# Directorios: snake_case
# src/tools/
# src/slack/
```

## 🔄 Proceso de Pull Request

### 1. Crear Branch

```bash
# Actualizar main
git checkout main
git pull upstream main

# Crear branch para tu feature
git checkout -b feature/nueva-funcionalidad
# o
git checkout -b fix/corregir-bug
# o
git checkout -b docs/actualizar-readme
```

### 2. Hacer Cambios

```bash
# Hacer tus cambios
# Seguir estándares de código
# Agregar tests si es necesario

# Verificar que todo funciona
pytest
black .
isort .
flake8
mypy src/
```

### 3. Commit Changes

```bash
# Agregar archivos
git add .

# Commit con mensaje descriptivo
git commit -m "feat: agregar comando de análisis de código

- Implementar análisis estático de código Python
- Agregar detección de problemas comunes
- Incluir sugerencias de mejora
- Agregar tests unitarios

Closes #123"
```

### Formato de Mensajes de Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>[scope opcional]: <descripción>

[cuerpo opcional]

[footer opcional]
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (no afectan funcionalidad)
- `refactor`: Refactoring de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

**Ejemplos:**
```bash
feat(slack): agregar comando /analyze para análisis de código
fix(bigquery): corregir error de conexión en memory_manager
docs(readme): actualizar instrucciones de instalación
test(agent): agregar tests para procesamiento de mensajes
```

### 4. Push y Pull Request

```bash
# Push a tu fork
git push origin feature/nueva-funcionalidad

# Crear Pull Request en GitHub
# Usar template de PR
```

### Template de Pull Request

```markdown
## 📝 Descripción

Breve descripción de los cambios realizados.

## 🔗 Issue Relacionado

Fixes #(número de issue)

## 🧪 Tipo de Cambio

- [ ] Bug fix (cambio que corrige un issue)
- [ ] Nueva funcionalidad (cambio que agrega funcionalidad)
- [ ] Breaking change (cambio que rompe compatibilidad)
- [ ] Documentación (cambio solo en documentación)

## 🧪 Testing

- [ ] Tests unitarios pasan
- [ ] Tests de integración pasan
- [ ] Cobertura de código mantenida/mejorada
- [ ] Tests manuales realizados

## 📋 Checklist

- [ ] Mi código sigue las guías de estilo del proyecto
- [ ] He realizado self-review de mi código
- [ ] He comentado mi código, especialmente en áreas complejas
- [ ] He actualizado la documentación correspondiente
- [ ] Mis cambios no generan nuevos warnings
- [ ] He agregado tests que prueban mi fix/funcionalidad
- [ ] Tests nuevos y existentes pasan localmente

## 📸 Screenshots (si aplica)

Agregar screenshots para cambios en UI.

## 📚 Documentación Adicional

Enlaces a documentación relevante.
```

## 🐛 Reportar Bugs

### Antes de Reportar

1. **Buscar issues existentes** para evitar duplicados
2. **Verificar con la última versión** del código
3. **Reproducir el bug** consistentemente

### Template de Bug Report

```markdown
## 🐛 Descripción del Bug

Descripción clara y concisa del bug.

## 🔄 Pasos para Reproducir

1. Ir a '...'
2. Hacer click en '...'
3. Scroll down to '...'
4. Ver error

## ✅ Comportamiento Esperado

Descripción clara de lo que esperabas que pasara.

## ❌ Comportamiento Actual

Descripción clara de lo que realmente pasó.

## 📸 Screenshots

Si aplica, agregar screenshots para explicar el problema.

## 🖥️ Información del Sistema

- OS: [e.g. Windows 10, macOS 11.2, Ubuntu 20.04]
- Python Version: [e.g. 3.9.1]
- Agent Version: [e.g. 1.2.3]
- Docker Version: [e.g. 20.10.5] (si aplica)

## 📋 Logs

```
Pegar logs relevantes aquí
```

## 🔧 Configuración

```bash
# Variables de entorno relevantes (sin secretos)
ANTHROPIC_MODEL=claude-3-sonnet-20240229
SLACK_SOCKET_MODE=true
```

## 📝 Contexto Adicional

Cualquier otra información relevante sobre el problema.
```

## ✨ Solicitar Funcionalidades

### Template de Feature Request

```markdown
## 🚀 Descripción de la Funcionalidad

Descripción clara y concisa de la funcionalidad que te gustaría ver.

## 🎯 Problema que Resuelve

Descripción clara del problema que esta funcionalidad resolvería.

## 💡 Solución Propuesta

Descripción clara de lo que te gustaría que pasara.

## 🔄 Alternativas Consideradas

Descripción de soluciones alternativas que has considerado.

## 📋 Casos de Uso

- Como [tipo de usuario], quiero [funcionalidad] para [beneficio]
- Como [tipo de usuario], quiero [funcionalidad] para [beneficio]

## 🧪 Criterios de Aceptación

- [ ] Criterio 1
- [ ] Criterio 2
- [ ] Criterio 3

## 📝 Contexto Adicional

Cualquier otra información relevante sobre la funcionalidad.

## 🎨 Mockups/Wireframes

Si aplica, agregar mockups o wireframes.
```

## 📚 Documentación

### Escribir Documentación

1. **Usar Markdown** para toda la documentación
2. **Ser claro y conciso** en las explicaciones
3. **Incluir ejemplos** cuando sea posible
4. **Mantener actualizada** la documentación

### Estructura de Documentación

```markdown
# 📖 Título del Documento

## 📋 Descripción Breve

Breve descripción del contenido.

## 🎯 Audiencia

Para quién está dirigido este documento.

## 📚 Contenido

### Sección 1

Contenido de la sección.

```python
# Ejemplo de código
def ejemplo():
    return "Hello World"
```

### Sección 2

Más contenido.

## 🔗 Referencias

- [Enlace 1](url)
- [Enlace 2](url)
```

## 🧪 Testing

### Escribir Tests

```python
import pytest
from unittest.mock import Mock, patch
from src.agents.claude_agent import ClaudeAgent

class TestClaudeAgent:
    """Tests para ClaudeAgent"""
    
    @pytest.fixture
    def agent(self):
        """Fixture para crear instancia de agente"""
        return ClaudeAgent(api_key="test-key")
    
    def test_process_message_success(self, agent):
        """Test procesamiento exitoso de mensaje"""
        # Arrange
        message = "Genera código Python para ordenar una lista"
        
        # Act
        result = agent.process_message(message)
        
        # Assert
        assert result is not None
        assert "response" in result
        assert result["status"] == "success"
    
    def test_process_message_empty_input(self, agent):
        """Test manejo de input vacío"""
        # Arrange
        message = ""
        
        # Act & Assert
        with pytest.raises(ValueError, match="El mensaje no puede estar vacío"):
            agent.process_message(message)
    
    @patch('src.agents.claude_agent.anthropic.Anthropic')
    def test_api_error_handling(self, mock_anthropic, agent):
        """Test manejo de errores de API"""
        # Arrange
        mock_anthropic.return_value.messages.create.side_effect = Exception("API Error")
        
        # Act
        result = agent.process_message("test message")
        
        # Assert
        assert result["status"] == "error"
        assert "API Error" in result["error"]
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_agent.py

# Con cobertura
pytest --cov=src --cov-report=html

# Tests de integración
pytest tests/integration/ -v

# Tests con marcadores
pytest -m "not slow"
```

### Configuración de pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

## 🏗️ Arquitectura y Patrones

### Principios de Diseño

1. **Single Responsibility**: Cada clase/función tiene una responsabilidad
2. **Open/Closed**: Abierto para extensión, cerrado para modificación
3. **Dependency Injection**: Inyectar dependencias en lugar de crearlas
4. **Interface Segregation**: Interfaces específicas mejor que generales

### Patrones Utilizados

```python
# Strategy Pattern para diferentes tipos de análisis
class CodeAnalyzer:
    def __init__(self, strategy: AnalysisStrategy):
        self.strategy = strategy
    
    def analyze(self, code: str) -> dict:
        return self.strategy.analyze(code)

# Factory Pattern para crear agentes
class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str) -> BaseAgent:
        if agent_type == "claude":
            return ClaudeAgent()
        elif agent_type == "gpt":
            return GPTAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

# Observer Pattern para eventos
class EventManager:
    def __init__(self):
        self.observers = []
    
    def subscribe(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for observer in self.observers:
            observer.handle(event)
```

## 🔒 Seguridad

### Mejores Prácticas

1. **Nunca commitear secretos** (API keys, passwords, etc.)
2. **Validar todas las entradas** del usuario
3. **Usar HTTPS** para todas las comunicaciones
4. **Implementar rate limiting** para APIs
5. **Sanitizar datos** antes de almacenar en BigQuery

### Ejemplo de Validación

```python
from pydantic import BaseModel, validator
import re

class UserMessage(BaseModel):
    user_id: str
    message: str
    channel: str
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not re.match(r'^U[A-Z0-9]{8,}$', v):
            raise ValueError('Invalid Slack user ID format')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v) > 4000:
            raise ValueError('Message too long')
        return v.strip()
```

## 🌍 Comunidad

### Comunicación

- **GitHub Issues**: Para bugs y feature requests
- **GitHub Discussions**: Para preguntas y discusiones generales
- **Pull Requests**: Para contribuciones de código
- **Email**: [maintainer@email.com] para temas sensibles

### Eventos

- **Code Reviews**: Todos los PRs requieren review
- **Release Planning**: Discusión de nuevas versiones
- **Bug Triage**: Revisión semanal de issues

### Reconocimientos

Todos los contribuidores son reconocidos en:
- `CONTRIBUTORS.md`
- Release notes
- README principal

## 📊 Métricas y Monitoreo

### Métricas de Código

```bash
# Cobertura de tests
pytest --cov=src --cov-report=term-missing

# Complejidad de código
radon cc src/ -a

# Métricas de mantenibilidad
radon mi src/

# Análisis de dependencias
pipdeptree
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: flake8 src/ tests/
    
    - name: Type check with mypy
      run: mypy src/
    
    - name: Test with pytest
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

## 🎉 ¡Gracias por Contribuir!

Tu contribución hace que este proyecto sea mejor para todos. Cada bug reportado, cada línea de código, cada mejora en la documentación es valiosa.

### Próximos Pasos

1. **Lee esta guía completamente**
2. **Configura tu entorno de desarrollo**
3. **Encuentra un issue para trabajar** (busca etiquetas `good first issue`)
4. **Haz tu primera contribución**
5. **Únete a la comunidad**

### Recursos Adicionales

- [Documentación del Proyecto](README.md)
- [Guía de Instalación](INSTALLATION.md)
- [Arquitectura del Sistema](ARCHITECTURE.md)
- [API Documentation](API_DOCUMENTATION.md)

¡Esperamos tus contribuciones! 🚀