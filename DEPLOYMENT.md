# 🚀 Guía de Despliegue - Claude Programming Agent

## 📋 Opciones de Despliegue

### 1. 🐳 Despliegue con Docker (Recomendado)
### 2. 🖥️ Despliegue Local
### 3. ☁️ Despliegue en la Nube

---

## 🐳 Despliegue con Docker

### Prerrequisitos
- Docker 20.10 o superior
- Docker Compose 2.0 o superior
- Archivo `.env` configurado

### Construcción de la Imagen

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd claude-programming-agent

# Construir la imagen Docker
docker build -t claude-slack-agent:latest .

# O usar el script de construcción
./build-docker-image.sh  # Linux/Mac
.\build-docker-image.ps1  # Windows
```

### Ejecución con Docker Run

```bash
# Ejecutar el contenedor
docker run -d \
  --name claude-agent \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/evals/results:/app/evals/results \
  --restart unless-stopped \
  claude-slack-agent:latest
```

### Ejecución con Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  claude-agent:
    build: .
    container_name: claude-agent
    env_file: .env
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/app/logs
      - ./evals/results:/app/evals/results
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Opcional: Redis para caché
  redis:
    image: redis:7-alpine
    container_name: claude-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

```bash
# Iniciar con Docker Compose
docker-compose up -d

# Ver logs
docker-compose logs -f claude-agent

# Detener
docker-compose down
```

---

## 🖥️ Despliegue Local

### Prerrequisitos
- Python 3.10 o superior
- pip o pipenv
- Git

### Instalación

```bash
# Clonar el repositorio
git clone <url-del-repositorio>
cd claude-programming-agent

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Ejecución

```bash
# Ejecutar el agente
python main.py

# O con puerto específico
WEBHOOK_PORT=8080 python main.py

# En Windows PowerShell
$env:WEBHOOK_PORT="8080"; python main.py
```

---

## ☁️ Despliegue en la Nube

### Google Cloud Platform (GCP)

#### Cloud Run (Recomendado)

```bash
# Configurar gcloud CLI
gcloud auth login
gcloud config set project TU-PROYECTO-ID

# Construir y subir imagen
gcloud builds submit --tag gcr.io/TU-PROYECTO-ID/claude-agent

# Desplegar en Cloud Run
gcloud run deploy claude-agent \
  --image gcr.io/TU-PROYECTO-ID/claude-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars WEBHOOK_PORT=8080
```

#### Google Kubernetes Engine (GKE)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: claude-agent
  template:
    metadata:
      labels:
        app: claude-agent
    spec:
      containers:
      - name: claude-agent
        image: gcr.io/TU-PROYECTO-ID/claude-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: WEBHOOK_PORT
          value: "8080"
        envFrom:
        - secretRef:
            name: claude-agent-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: claude-agent-service
spec:
  selector:
    app: claude-agent
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### AWS

#### AWS ECS Fargate

```json
{
  "family": "claude-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "claude-agent",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/claude-agent:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "WEBHOOK_PORT",
          "value": "8080"
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:claude-agent/anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/claude-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Azure

#### Azure Container Instances

```bash
# Crear grupo de recursos
az group create --name claude-agent-rg --location eastus

# Desplegar contenedor
az container create \
  --resource-group claude-agent-rg \
  --name claude-agent \
  --image claude-slack-agent:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8080 \
  --environment-variables WEBHOOK_PORT=8080 \
  --secure-environment-variables \
    ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
    SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
```

---

## 🔧 Configuración de Entornos

### Desarrollo
```bash
# .env para desarrollo
DEBUG=true
LOG_LEVEL=DEBUG
DEPLOYMENT_TYPE=development
ENABLE_UNIT_TESTS=true
```

### Staging
```bash
# .env para staging
DEBUG=false
LOG_LEVEL=INFO
DEPLOYMENT_TYPE=staging
ENABLE_UNIT_TESTS=true
```

### Producción
```bash
# .env para producción
DEBUG=false
LOG_LEVEL=WARNING
DEPLOYMENT_TYPE=production
ENABLE_UNIT_TESTS=false
MAX_WORKERS=4
```

---

## 📊 Monitoreo y Observabilidad

### Health Checks

```bash
# Verificar estado del servicio
curl http://localhost:8080/health

# Respuesta esperada:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "components": {
    "anthropic_api": "healthy",
    "slack_api": "healthy",
    "bigquery": "healthy"
  }
}
```

### Logs

```bash
# Ver logs en tiempo real
docker logs -f claude-agent

# Logs específicos
tail -f logs/claude_agent.log
tail -f logs/claude_agent_errors.log
```

### Métricas

```bash
# Endpoint de métricas (si está habilitado)
curl http://localhost:8080/metrics

# Métricas en formato JSON
curl http://localhost:8080/metrics.json
```

---

## 🛡️ Seguridad en Producción

### Variables de Entorno Seguras

```bash
# Usar secretos del sistema
# Kubernetes
kubectl create secret generic claude-agent-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-... \
  --from-literal=SLACK_BOT_TOKEN=xoxb-...

# Docker Swarm
echo "sk-ant-..." | docker secret create anthropic_api_key -
echo "xoxb-..." | docker secret create slack_bot_token -
```

### Firewall y Red

```bash
# Permitir solo tráfico necesario
# Puerto 8080 para webhooks de Slack
# Puerto 443 para APIs externas (Anthropic, Slack)

# Ejemplo con iptables
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
```

### SSL/TLS

```nginx
# Configuración Nginx como proxy reverso
server {
    listen 443 ssl;
    server_name tu-dominio.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Claude Agent

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build and push Docker image
      run: |
        docker build -t claude-agent:${{ github.sha }} .
        docker tag claude-agent:${{ github.sha }} claude-agent:latest
        # Push to registry
    - name: Deploy to production
      run: |
        # Deploy commands here
```

---

## 🚨 Solución de Problemas

### Problemas Comunes

#### El contenedor no inicia
```bash
# Verificar logs
docker logs claude-agent

# Verificar configuración
docker run --rm claude-slack-agent:latest python -c "from src.utils.config_validator import ConfigValidator; print(ConfigValidator.validate_configuration())"
```

#### Problemas de conectividad
```bash
# Verificar conectividad a APIs
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" https://slack.com/api/auth.test
```

#### Problemas de memoria
```bash
# Aumentar límites de memoria
docker run --memory=2g claude-slack-agent:latest

# En Kubernetes
resources:
  limits:
    memory: "2Gi"
```

### Comandos de Diagnóstico

```bash
# Estado del contenedor
docker ps
docker stats claude-agent

# Información del sistema
docker exec claude-agent python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"

# Verificar configuración
docker exec claude-agent python -c "from src.utils.config_validator import ConfigValidator; ConfigValidator.validate_configuration()"
```