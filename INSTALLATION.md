# 🚀 Guía de Instalación - Claude Programming Agent

## 📋 Requisitos Previos

### Requisitos del Sistema

- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows 10/11, macOS 10.14+, o Linux Ubuntu 18.04+
- **RAM**: Mínimo 4GB, recomendado 8GB+
- **Espacio en Disco**: Mínimo 2GB libres
- **Conexión a Internet**: Requerida para APIs externas

### Cuentas y APIs Necesarias

1. **Anthropic Claude API**
   - Cuenta en [Anthropic](https://console.anthropic.com/)
   - API Key con créditos disponibles
   - Modelo recomendado: `claude-3-sonnet-20240229`

2. **Slack Workspace**
   - Permisos de administrador en el workspace
   - Capacidad para crear aplicaciones Slack

3. **Google Cloud Platform**
   - Proyecto GCP activo
   - BigQuery habilitado
   - Cuenta de servicio configurada

## 🛠️ Instalación Paso a Paso

### Opción 1: Instalación con Docker (Recomendada)

#### 1. Instalar Docker

**Windows:**
```powershell
# Descargar Docker Desktop desde https://docker.com/products/docker-desktop
# Ejecutar el instalador y reiniciar el sistema
```

**macOS:**
```bash
# Usando Homebrew
brew install --cask docker

# O descargar desde https://docker.com/products/docker-desktop
```

**Linux (Ubuntu):**
```bash
# Actualizar paquetes
sudo apt update

# Instalar Docker
sudo apt install docker.io docker-compose

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Reiniciar sesión o ejecutar
newgrp docker
```

#### 2. Clonar el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/claude-programming-agent.git
cd claude-programming-agent

# Verificar contenido
ls -la
```

#### 3. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar configuración (usar tu editor preferido)
nano .env
# o
code .env
# o
notepad .env
```

#### 4. Construir y Ejecutar con Docker

```bash
# Construir imagen
docker build -t claude-agent .

# Ejecutar contenedor
docker run -d \
  --name claude-agent \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  claude-agent

# Verificar que está funcionando
docker logs claude-agent
```

#### 5. Usar Docker Compose (Alternativa)

```bash
# Ejecutar con docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

### Opción 2: Instalación Local

#### 1. Preparar Entorno Python

**Windows:**
```powershell
# Verificar Python
python --version

# Crear entorno virtual
python -m venv claude-agent-env

# Activar entorno virtual
.\claude-agent-env\Scripts\Activate.ps1

# Si hay error de ejecución de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS/Linux:**
```bash
# Verificar Python
python3 --version

# Crear entorno virtual
python3 -m venv claude-agent-env

# Activar entorno virtual
source claude-agent-env/bin/activate
```

#### 2. Clonar e Instalar Dependencias

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/claude-programming-agent.git
cd claude-programming-agent

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list
```

#### 3. Configurar Variables de Entorno

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración
# Windows: notepad .env
# macOS: open -e .env
# Linux: nano .env
```

#### 4. Ejecutar el Agente

```bash
# Ejecutar directamente
python main.py

# O con variables específicas
WEBHOOK_PORT=8080 python main.py

# En segundo plano (Linux/macOS)
nohup python main.py > logs/agent.log 2>&1 &

# En segundo plano (Windows)
start /B python main.py
```

## ⚙️ Configuración Detallada

### 1. Configuración de Anthropic Claude

```bash
# En tu archivo .env
ANTHROPIC_API_KEY=sk-ant-api03-tu-clave-aqui
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7
```

**Obtener API Key:**
1. Visita [Anthropic Console](https://console.anthropic.com/)
2. Crea una cuenta o inicia sesión
3. Ve a "API Keys" en el dashboard
4. Crea una nueva API key
5. Copia la clave y pégala en tu `.env`

### 2. Configuración de Slack

#### Crear Aplicación Slack

1. **Ir a Slack API**
   - Visita [api.slack.com/apps](https://api.slack.com/apps)
   - Click en "Create New App"
   - Selecciona "From scratch"
   - Nombra tu app: "Claude Programming Agent"
   - Selecciona tu workspace

2. **Configurar OAuth & Permissions**
   ```
   Bot Token Scopes:
   - app_mentions:read
   - channels:history
   - channels:read
   - chat:write
   - files:read
   - files:write
   - groups:history
   - groups:read
   - im:history
   - im:read
   - im:write
   - mpim:history
   - mpim:read
   - users:read
   - users:read.email
   ```

3. **Configurar Event Subscriptions**
   - Habilitar eventos
   - Request URL: `https://tu-dominio.com/slack/events`
   - Subscribe to bot events:
     - `app_mention`
     - `message.channels`
     - `message.groups`
     - `message.im`
     - `message.mpim`

4. **Configurar Socket Mode**
   - Habilitar Socket Mode
   - Crear App-Level Token con scope `connections:write`

#### Variables de Entorno Slack

```bash
# En tu archivo .env
SLACK_BOT_TOKEN=xoxb-tu-bot-token-aqui
SLACK_APP_TOKEN=xapp-tu-app-token-aqui
SLACK_SIGNING_SECRET=tu-signing-secret-aqui
SLACK_SOCKET_MODE=true
```

### 3. Configuración de Google Cloud Platform

#### Crear Proyecto y Habilitar APIs

```bash
# Instalar Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Autenticarse
gcloud auth login

# Crear proyecto
gcloud projects create claude-agent-proyecto --name="Claude Agent"

# Configurar proyecto activo
gcloud config set project claude-agent-proyecto

# Habilitar APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerystorage.googleapis.com
```

#### Crear Cuenta de Servicio

```bash
# Crear cuenta de servicio
gcloud iam service-accounts create claude-agent \
    --display-name="Claude Agent Service" \
    --description="Service account for Claude Programming Agent"

# Asignar permisos
gcloud projects add-iam-policy-binding claude-agent-proyecto \
    --member="serviceAccount:claude-agent@claude-agent-proyecto.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding claude-agent-proyecto \
    --member="serviceAccount:claude-agent@claude-agent-proyecto.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Generar clave JSON
gcloud iam service-accounts keys create claude-agent-key.json \
    --iam-account=claude-agent@claude-agent-proyecto.iam.gserviceaccount.com
```

#### Variables de Entorno Google Cloud

```bash
# En tu archivo .env
BIGQUERY_PROJECT_ID=claude-agent-proyecto
BIGQUERY_DATASET=agente_anthropic
BIGQUERY_LOCATION=us-central1
BIGQUERY_MAX_BYTES_BILLED=30000000000

# Contenido del archivo JSON (una línea)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"claude-agent-proyecto",...}
```

### 4. Configuración de BigQuery

```bash
# Ejecutar script de inicialización
python scripts/create_bigquery_tables.py

# O crear manualmente las tablas siguiendo BIGQUERY_SETUP.md
```

## 🔧 Configuración Avanzada

### Variables de Entorno Completas

```bash
# ===== ANTHROPIC CLAUDE =====
ANTHROPIC_API_KEY=sk-ant-api03-tu-clave-aqui
ANTHROPIC_MODEL=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_TIMEOUT=60

# ===== SLACK =====
SLACK_BOT_TOKEN=xoxb-tu-bot-token
SLACK_APP_TOKEN=xapp-tu-app-token
SLACK_SIGNING_SECRET=tu-signing-secret
SLACK_SOCKET_MODE=true
SLACK_RETRY_ATTEMPTS=3
SLACK_RETRY_DELAY=1

# ===== APLICACIÓN =====
APP_NAME=Claude Programming Agent
APP_VERSION=1.0.0
APP_ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG_MODE=false

# ===== GOOGLE CLOUD =====
BIGQUERY_PROJECT_ID=tu-proyecto-gcp
BIGQUERY_DATASET=agente_anthropic
BIGQUERY_LOCATION=us-central1
BIGQUERY_MAX_BYTES_BILLED=30000000000
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}

# ===== SEGURIDAD =====
SECRET_KEY=tu-clave-secreta-muy-segura
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
CORS_ORIGINS=https://tu-dominio.com
RATE_LIMIT_PER_MINUTE=60

# ===== DESARROLLO =====
WEBHOOK_PORT=8080
WEBHOOK_HOST=0.0.0.0
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# ===== TESTING =====
TEST_MODE=false
TEST_SLACK_CHANNEL=C1234567890
TEST_USER_ID=U1234567890

# ===== DEPLOYMENT =====
CONTAINER_NAME=claude-agent
RESTART_POLICY=unless-stopped
MEMORY_LIMIT=2g
CPU_LIMIT=1.0
```

### Configuración de Logging

```python
# En config/logging.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'logs/agent.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
}
```

## 🧪 Verificación de Instalación

### 1. Verificar Dependencias

```bash
# Verificar Python y paquetes
python --version
pip list | grep -E "(anthropic|slack|google-cloud)"

# Verificar Docker (si aplica)
docker --version
docker-compose --version
```

### 2. Probar Conexiones

```bash
# Probar conexión a Anthropic
python -c "
import os
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
print('✅ Anthropic API conectada')
"

# Probar conexión a BigQuery
python -c "
import os
from google.cloud import bigquery
client = bigquery.Client()
print('✅ BigQuery conectado')
"
```

### 3. Ejecutar Tests

```bash
# Ejecutar tests unitarios
python -m pytest tests/ -v

# Ejecutar test de integración
python tests/test_integration.py

# Verificar health check
curl http://localhost:8080/health
```

### 4. Verificar Slack

1. **Invitar el bot a un canal**
   ```
   /invite @claude-agent
   ```

2. **Probar comando básico**
   ```
   @claude-agent help
   ```

3. **Verificar respuesta**
   - El bot debe responder con la lista de comandos disponibles

## 🚨 Solución de Problemas Comunes

### Error: "ModuleNotFoundError"

```bash
# Verificar entorno virtual activado
which python
# Debe mostrar la ruta del entorno virtual

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error: "Anthropic API Key Invalid"

```bash
# Verificar variable de entorno
echo $ANTHROPIC_API_KEY

# Verificar formato (debe empezar con sk-ant-api03-)
# Regenerar clave en console.anthropic.com si es necesario
```

### Error: "Slack Socket Connection Failed"

```bash
# Verificar tokens Slack
echo $SLACK_BOT_TOKEN  # Debe empezar con xoxb-
echo $SLACK_APP_TOKEN  # Debe empezar con xapp-

# Verificar permisos en api.slack.com/apps
# Reinstalar app en workspace si es necesario
```

### Error: "BigQuery Permission Denied"

```bash
# Verificar proyecto GCP
gcloud config get-value project

# Verificar permisos de cuenta de servicio
gcloud projects get-iam-policy tu-proyecto-gcp

# Regenerar clave de cuenta de servicio si es necesario
```

### Error: "Port Already in Use"

```bash
# Encontrar proceso usando el puerto
# Windows:
netstat -ano | findstr :8080

# macOS/Linux:
lsof -i :8080

# Cambiar puerto en .env
WEBHOOK_PORT=8081
```

## 📊 Monitoreo Post-Instalación

### 1. Verificar Logs

```bash
# Ver logs en tiempo real
tail -f logs/agent.log

# Buscar errores
grep -i error logs/agent.log

# Ver logs de Docker
docker logs claude-agent -f
```

### 2. Métricas del Sistema

```bash
# Verificar uso de recursos
# Windows:
Get-Process -Name python | Select-Object CPU,WorkingSet

# macOS/Linux:
ps aux | grep python
top -p $(pgrep -f "python main.py")
```

### 3. Health Checks

```bash
# Verificar endpoint de salud
curl http://localhost:8080/health

# Verificar métricas
curl http://localhost:8080/metrics

# Verificar estado de Slack
curl http://localhost:8080/slack/status
```

## 🔄 Actualizaciones

### Actualizar el Agente

```bash
# Detener agente
docker-compose down
# o
pkill -f "python main.py"

# Actualizar código
git pull origin main

# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Reconstruir Docker (si aplica)
docker build -t claude-agent .

# Reiniciar
docker-compose up -d
# o
python main.py
```

### Migrar Configuración

```bash
# Comparar archivos de configuración
diff .env .env.example

# Agregar nuevas variables si es necesario
# Mantener valores existentes
```

## 📞 Soporte

Si encuentras problemas durante la instalación:

1. **Revisa los logs** en `logs/agent.log`
2. **Consulta la documentación** en los archivos `.md`
3. **Verifica la configuración** en `.env`
4. **Ejecuta los tests** para identificar problemas
5. **Contacta soporte** si el problema persiste

### Información para Soporte

Cuando contactes soporte, incluye:

```bash
# Información del sistema
python --version
pip list
docker --version  # si aplica

# Logs relevantes
tail -50 logs/agent.log

# Configuración (sin secretos)
cat .env | grep -v -E "(API_KEY|TOKEN|SECRET)"
```