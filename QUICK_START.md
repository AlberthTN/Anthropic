# ⚡ Guía de Inicio Rápido - Claude Programming Agent

¿Quieres empezar a usar el Claude Programming Agent **ahora mismo**? Esta guía te llevará de cero a productivo en menos de 10 minutos.

## 🎯 Lo que Necesitas (5 minutos)

### 1. 🔑 API Keys Requeridas

**Anthropic Claude API** (2 minutos)
1. Ve a [console.anthropic.com](https://console.anthropic.com)
2. Crea una cuenta o inicia sesión
3. Ve a "API Keys" → "Create Key"
4. Copia tu API key (empieza con `sk-ant-`)

**Slack App** (3 minutos)
1. Ve a [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From an app manifest"
3. Selecciona tu workspace
4. Copia y pega este manifest:

```yaml
display_information:
  name: Claude Programming Agent
  description: AI-powered programming assistant
  background_color: "#2c2d30"
features:
  bot_user:
    display_name: Claude Agent
    always_online: true
  slash_commands:
    - command: /help
      description: Show available commands
      should_escape: false
    - command: /analyze
      description: Analyze code
      should_escape: false
    - command: /generate
      description: Generate code
      should_escape: false
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history
      - chat:write
      - commands
      - files:write
      - im:history
      - im:read
      - im:write
      - users:read
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
```

5. Instala la app en tu workspace
6. Ve a "OAuth & Permissions" → copia el "Bot User OAuth Token" (empieza con `xoxb-`)
7. Ve a "Basic Information" → copia el "Signing Secret"
8. Ve a "Socket Mode" → habilítalo → crea un token → copia el "App-Level Token" (empieza con `xapp-`)

## 🚀 Instalación Express (2 minutos)

### Opción A: Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/claude-programming-agent.git
cd claude-programming-agent

# 2. Configurar variables
cp .env.example .env
```

Edita `.env` con tus API keys:
```env
# Claude AI
ANTHROPIC_API_KEY=sk-ant-tu-api-key-aqui
CLAUDE_MODEL=claude-3-sonnet-20240229

# Slack
SLACK_BOT_TOKEN=xoxb-tu-bot-token
SLACK_APP_TOKEN=xapp-tu-app-token
SLACK_SIGNING_SECRET=tu-signing-secret

# App
APP_NAME=claude-slack-agent
WEBHOOK_PORT=8080
DEBUG_MODE=true
```

```bash
# 3. Iniciar con Docker
docker-compose up -d
```

### Opción B: Local

```bash
# 1. Clonar e instalar
git clone https://github.com/tu-usuario/claude-programming-agent.git
cd claude-programming-agent
pip install -r requirements.txt

# 2. Configurar variables (mismo .env de arriba)
cp .env.example .env
# Editar .env con tus API keys

# 3. Iniciar
python main.py
```

## ✅ Verificación (1 minuto)

1. **Verificar que el agente esté corriendo**:
   ```bash
   # Deberías ver logs como:
   # ✅ Claude Programming Agent iniciado correctamente
   # 🔗 Slack WebSocket conectado
   # 🌐 Servidor HTTP corriendo en puerto 8080
   ```

2. **Probar en Slack**:
   - Ve a tu workspace de Slack
   - Busca "Claude Agent" en la lista de apps
   - Envía un mensaje directo: `help`
   - Deberías recibir la lista de comandos disponibles

## 🎮 Primeros Comandos (2 minutos)

### 1. 🆘 Obtener Ayuda
```
help
```
**Resultado**: Lista completa de comandos disponibles

### 2. 🔍 Analizar Código
```
analyze
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```
**Resultado**: Análisis de complejidad, sugerencias de optimización

### 3. ⚡ Generar Código
```
generate función para validar email con regex
```
**Resultado**: Función completa con validación de email

### 4. 📝 Explicar Código
```
explain
list(map(lambda x: x**2, filter(lambda x: x%2==0, range(10))))
```
**Resultado**: Explicación paso a paso del código

### 5. 🔧 Optimizar Código
```
optimize
def find_max(numbers):
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num
```
**Resultado**: Versión optimizada usando `max()`

## 🎯 Casos de Uso Inmediatos

### Para Desarrolladores Python
```
generate clase para manejar conexiones a base de datos con pool de conexiones
```

### Para Desarrolladores JavaScript
```
generate función async para hacer peticiones HTTP con retry automático
```

### Para Code Review
```
review
// Pega aquí el código que quieres revisar
function processData(data) {
    var result = [];
    for (var i = 0; i < data.length; i++) {
        if (data[i] != null) {
            result.push(data[i].toUpperCase());
        }
    }
    return result;
}
```

### Para Debugging
```
debug
Error: TypeError: Cannot read property 'length' of undefined
at processArray (script.js:15:20)
```

### Para Documentación
```
document
def calculate_compound_interest(principal, rate, time, compound_frequency):
    return principal * (1 + rate/compound_frequency) ** (compound_frequency * time)
```

## 🔧 Configuración Avanzada (Opcional)

### BigQuery (Para Persistencia)
Si quieres habilitar la persistencia de conversaciones:

1. **Crear proyecto GCP**:
   - Ve a [console.cloud.google.com](https://console.cloud.google.com)
   - Crea un nuevo proyecto
   - Habilita BigQuery API

2. **Crear Service Account**:
   - Ve a "IAM & Admin" → "Service Accounts"
   - Crea nueva cuenta de servicio
   - Descarga el archivo JSON de credenciales

3. **Configurar en .env**:
   ```env
   # Google Cloud
   GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
   BIGQUERY_PROJECT_ID=tu-proyecto-gcp
   BIGQUERY_DATASET_ID=claude_agent_data
   ```

4. **Crear tablas**:
   ```bash
   python create_tables.py
   ```

### Monitoreo (Para Métricas)
```env
# Habilitar métricas
ENABLE_METRICS=true
METRICS_PORT=9090
```

Accede a métricas en: `http://localhost:9090/metrics`

## 🚨 Solución de Problemas Rápidos

### ❌ "Error: Invalid API Key"
- Verifica que `ANTHROPIC_API_KEY` esté correctamente configurada
- Asegúrate de que la API key sea válida en console.anthropic.com

### ❌ "Slack connection failed"
- Verifica los tokens de Slack
- Asegúrate de que Socket Mode esté habilitado
- Confirma que la app esté instalada en el workspace

### ❌ "Port already in use"
- Cambia `WEBHOOK_PORT` en .env a otro puerto (ej: 8081)
- O mata el proceso que usa el puerto: `lsof -ti:8080 | xargs kill`

### ❌ "Module not found"
- Reinstala dependencias: `pip install -r requirements.txt`
- Verifica que estés en el directorio correcto

## 📱 Comandos de Slack Disponibles

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `help` | Mostrar ayuda | `help` |
| `analyze` | Analizar código | `analyze [código]` |
| `generate` | Generar código | `generate función para...` |
| `explain` | Explicar código | `explain [código complejo]` |
| `optimize` | Optimizar código | `optimize [código]` |
| `debug` | Ayudar con debugging | `debug [error]` |
| `review` | Revisar código | `review [código]` |
| `test` | Generar tests | `test [función]` |
| `document` | Generar docs | `document [código]` |
| `refactor` | Sugerir refactoring | `refactor [código]` |

## 🎉 ¡Listo para Usar!

¡Felicitaciones! Ya tienes tu Claude Programming Agent funcionando. Ahora puedes:

- 💬 **Chatear con Claude** directamente en Slack
- 🔍 **Analizar y optimizar** tu código
- ⚡ **Generar código** automáticamente
- 📚 **Obtener explicaciones** detalladas
- 🐛 **Resolver bugs** más rápido

## 📚 Próximos Pasos

1. **Lee la documentación completa**: [README.md](README.md)
2. **Explora casos de uso avanzados**: [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Configura BigQuery**: [BIGQUERY_SETUP.md](BIGQUERY_SETUP.md)
4. **Despliega en producción**: [DEPLOYMENT.md](DEPLOYMENT.md)

## 🤝 ¿Necesitas Ayuda?

- 📖 **Documentación**: Lee los archivos .md en el repositorio
- 🐛 **Bugs**: Crea un issue en GitHub
- 💡 **Ideas**: Usa GitHub Discussions
- 📧 **Soporte**: support@tu-dominio.com

---

**¡Disfruta programando con tu nuevo asistente AI!** 🚀✨