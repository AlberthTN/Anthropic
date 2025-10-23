# 🤖 Claude Programming Agent para Slack

Un agente de inteligencia artificial avanzado especializado en programación que se integra perfectamente con Slack. Proporciona asistencia experta en desarrollo de software, generación de código, debugging, testing, análisis de código y mucho más.

## ✨ Características Principales

### 🧠 Capacidades de IA
- **Generación inteligente de código** en múltiples lenguajes (Python, JavaScript, TypeScript, Java, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, Dart)
- **Análisis de código avanzado** con detección de problemas, vulnerabilidades y sugerencias de mejora
- **Debugging asistido** con identificación automática de errores y soluciones propuestas
- **Testing automático** con generación y ejecución de pruebas unitarias
- **Revisión de código** con mejores prácticas y estándares de la industria

### 🔗 Integración y Conectividad
- **Integración completa con Slack** mediante webhooks HTTP
- **Memoria persistente** con BigQuery para recordar conversaciones y contexto
- **Monitoreo de salud** en tiempo real con métricas detalladas
- **Sistema de degradación graceful** para alta disponibilidad
- **Logging robusto** con rotación automática y múltiples niveles

### 🛡️ Seguridad y Confiabilidad
- **Validación de configuración** automática al inicio
- **Manejo de errores** robusto con recuperación automática
- **Validación de seguridad** para código generado
- **Rate limiting** y protección contra abuso
- **Encriptación** de credenciales y datos sensibles

## 📋 Requisitos Previos

- **Python 3.10 o superior**
- **Cuenta de Anthropic** con API key válida
- **Workspace de Slack** con permisos para crear aplicaciones
- **Google Cloud Platform** (opcional, para memoria persistente)
- **Docker** (opcional, para despliegue en contenedores)

## 🔧 Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd claude-slack-agent
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus API keys
   ```

## 🔑 Configuración de Variables de Entorno

Edita el archivo `.env` con tus credenciales:

```env
# Anthropic Claude
ANTHROPIC_API_KEY=tu_claude_api_key
CLAUDE_MODEL=claude-4-sonnet

# Slack
SLACK_BOT_TOKEN=xoxb-tu-bot-token
SLACK_APP_TOKEN=xapp-tu-app-token
SLACK_SIGNING_SECRET=tu-signing-secret

# Google ADK
GOOGLE_ADK_PROJECT_ID=tu-proyecto-id
GOOGLE_ADK_LOCATION=us-central1

# Configuración de la aplicación
APP_NAME=ClaudeProgrammingAgent
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
```

## 🤖 Configuración de Slack

1. **Crear una nueva app en Slack**
   - Ve a [api.slack.com/apps](https://api.slack.com/apps)
   - Crea una nueva app desde cero
   - Selecciona tu workspace

2. **Configurar Socket Mode**
   - Activa Socket Mode en la sección "Socket Mode"
   - Genera un App-Level Token con `connections:write` scope

3. **Configurar Event Subscriptions**
   - Activa Event Subscriptions
   - Suscribe a los siguientes eventos:
     - `app_mention`
     - `message.im`
     - `file_shared`

4. **Configurar OAuth & Permissions**
   - Agrega estos scopes de Bot Token:
     - `chat:write`
     - `files:read`
     - `files:write`
     - `channels:read`
     - `groups:read`
     - `im:read`
     - `mpim:read`

5. **Instalar la app en tu workspace**

## 🎯 Uso

### Iniciar el agente
```bash
python main.py
```

### Comandos de Slack disponibles

- **/code** - Generar código basado en requisitos
- **/analyze** - Analizar código para detectar problemas
- **/test** - Generar y ejecutar pruebas unitarias
- **/debug** - Ayudar con debugging de errores
- **/deploy** - Asistencia con deployment
- **/review** - Revisión de código
- **/help** - Mostrar ayuda y comandos disponibles

### Ejemplos de uso

#### Generar código
```
/code Crea una función en Python que ordene una lista de números usando quicksort
```

#### Analizar código
```
/analyze
```
(Adjunta un archivo de código)

#### Debugging
```
/debug Estoy obteniendo un IndexError en mi lista, ¿puedes ayudarme?
```

## 🧪 Testing y Evaluación

### Ejecutar evaluaciones del agente
```bash
python evals/run_evaluations.py
```

### Ejecutar pruebas unitarias
```bash
python -m pytest tests/
```

## 🐳 Deployment con Docker

### Construir la imagen
```bash
docker build -t claude-slack-agent .
```

### Ejecutar el contenedor
```bash
docker run -d \
  --name claude-agent \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/evals/results:/app/evals/results \
  claude-slack-agent
```

### Docker Compose
```bash
docker-compose up -d
```

## 📊 Monitoreo y Logs

Los logs se guardan en el directorio `logs/` con rotación automática. Puedes monitorear el rendimiento del agente mediante:

- Logs de aplicación: `logs/app.log`
- Logs de errores: `logs/error.log`
- Resultados de evaluaciones: `evals/results/results.json`

## 🔒 Seguridad

- Nunca compartas tus API keys
- Usa variables de entorno para credenciales
- Implementa rate limiting para prevenir abuso
- Revisa regularmente los logs de seguridad
- Mantén las dependencias actualizadas

## 🐛 Solución de Problemas

### El agente no responde en Slack
1. Verifica que Socket Mode esté activado
2. Confirma que los tokens sean correctos
3. Revisa los logs de la aplicación

### Errores de API
1. Verifica que tu API key de Anthropic sea válida
2. Confirma que tienes créditos disponibles
3. Revisa los límites de rate limit

### Problemas de memoria
1. Ajusta `MAX_WORKERS` en el archivo `.env`
2. Implementa límites de tamaño de código
3. Usa procesamiento por lotes para archivos grandes

## 📚 Documentación

### 🚀 Empezar Rápido
- [⚡ Guía de Inicio Rápido](QUICK_START.md) - ¡Funcionando en 10 minutos!
- [📋 Resumen del Proyecto](PROJECT_SUMMARY.md) - Visión general completa

### 📖 Guías Detalladas
- [🚀 Guía de Instalación](INSTALLATION.md) - Instalación paso a paso
- [🏗️ Arquitectura del Sistema](ARCHITECTURE.md) - Diseño y componentes
- [🚢 Guía de Deployment](DEPLOYMENT.md) - Despliegue en producción

### 🔧 Configuración Técnica
- [📡 Documentación de API](API_DOCUMENTATION.md) - Endpoints y uso
- [🗄️ Configuración BigQuery](BIGQUERY_SETUP.md) - Base de datos
- [🐙 Configuración GitHub](GITHUB_SETUP.md) - Subir a GitHub

### 🤝 Desarrollo y Contribución
- [🤝 Guía de Contribución](CONTRIBUTING.md) - Cómo contribuir
- [📋 Historial de Cambios](CHANGELOG.md) - Versiones y updates

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- Anthropic por Claude AI
- Slack por su API y plataforma
- Google por ADK
- Comunidad open source

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la sección de solución de problemas
2. Abre un issue en GitHub
3. Contacta al equipo de soporte

---

**⚡ Hecho con ❤️ por el equipo de desarrollo de Claude Programming Agent**