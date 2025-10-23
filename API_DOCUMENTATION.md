# 📡 Documentación de API - Claude Programming Agent

## 📋 Visión General

El Claude Programming Agent expone varios endpoints HTTP para interactuar con el sistema, recibir webhooks de Slack y proporcionar información de estado y métricas.

## 🔗 Endpoints Principales

### 1. 🏥 Health Check

#### `GET /health`
Verifica el estado de salud del sistema y sus componentes.

**Respuesta Exitosa (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "components": {
    "anthropic_api": {
      "status": "healthy",
      "response_time_ms": 150,
      "last_check": "2024-01-01T12:00:00.000Z"
    },
    "slack_api": {
      "status": "healthy",
      "response_time_ms": 80,
      "last_check": "2024-01-01T12:00:00.000Z"
    },
    "bigquery": {
      "status": "healthy",
      "response_time_ms": 200,
      "last_check": "2024-01-01T12:00:00.000Z"
    },
    "memory_manager": {
      "status": "healthy",
      "cached_conversations": 45,
      "last_cleanup": "2024-01-01T11:30:00.000Z"
    }
  },
  "system_metrics": {
    "cpu_usage_percent": 25.5,
    "memory_usage_percent": 68.2,
    "disk_usage_percent": 45.1,
    "active_connections": 12
  }
}
```

**Respuesta con Problemas (503):**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "version": "1.0.0",
  "errors": [
    {
      "component": "anthropic_api",
      "error": "Connection timeout",
      "last_error_time": "2024-01-01T11:58:30.000Z"
    }
  ],
  "components": {
    "anthropic_api": {
      "status": "unhealthy",
      "error": "Connection timeout"
    },
    "slack_api": {
      "status": "healthy"
    }
  }
}
```

### 2. 📊 Métricas del Sistema

#### `GET /metrics`
Proporciona métricas detalladas del sistema en formato Prometheus.

**Respuesta (200):**
```
# HELP claude_agent_requests_total Total number of requests processed
# TYPE claude_agent_requests_total counter
claude_agent_requests_total{method="POST",endpoint="/slack/events"} 1234

# HELP claude_agent_response_time_seconds Response time in seconds
# TYPE claude_agent_response_time_seconds histogram
claude_agent_response_time_seconds_bucket{le="0.1"} 100
claude_agent_response_time_seconds_bucket{le="0.5"} 450
claude_agent_response_time_seconds_bucket{le="1.0"} 800
claude_agent_response_time_seconds_bucket{le="+Inf"} 1000

# HELP claude_agent_active_conversations Current active conversations
# TYPE claude_agent_active_conversations gauge
claude_agent_active_conversations 25

# HELP claude_agent_errors_total Total number of errors
# TYPE claude_agent_errors_total counter
claude_agent_errors_total{type="api_error"} 5
claude_agent_errors_total{type="validation_error"} 2
```

#### `GET /metrics.json`
Métricas en formato JSON para integración con sistemas de monitoreo.

**Respuesta (200):**
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "metrics": {
    "requests": {
      "total": 1234,
      "successful": 1200,
      "failed": 34,
      "rate_per_minute": 15.5
    },
    "response_times": {
      "average_ms": 450,
      "p50_ms": 380,
      "p95_ms": 850,
      "p99_ms": 1200
    },
    "conversations": {
      "active": 25,
      "total_today": 156,
      "average_length": 8.5
    },
    "code_generation": {
      "requests_today": 89,
      "languages": {
        "python": 45,
        "javascript": 23,
        "typescript": 12,
        "java": 9
      }
    },
    "errors": {
      "total_today": 12,
      "by_type": {
        "api_timeout": 5,
        "validation_error": 4,
        "rate_limit": 2,
        "unknown": 1
      }
    }
  }
}
```

### 3. 💬 Webhook de Slack

#### `POST /slack/events`
Endpoint principal para recibir eventos de Slack.

**Headers Requeridos:**
```
Content-Type: application/json
X-Slack-Signature: v0=signature
X-Slack-Request-Timestamp: timestamp
```

**Cuerpo de Solicitud (Event API):**
```json
{
  "token": "verification_token",
  "team_id": "T1234567890",
  "api_app_id": "A1234567890",
  "event": {
    "type": "app_mention",
    "user": "U1234567890",
    "text": "<@U0BOTUSER> genera una función de ordenamiento en Python",
    "ts": "1234567890.123456",
    "channel": "C1234567890",
    "event_ts": "1234567890.123456"
  },
  "type": "event_callback",
  "event_id": "Ev1234567890",
  "event_time": 1234567890
}
```

**Respuesta de Verificación (200):**
```json
{
  "challenge": "challenge_string"
}
```

**Respuesta de Procesamiento (200):**
```json
{
  "status": "ok",
  "message_id": "msg_1234567890",
  "processing_time_ms": 450
}
```

### 4. 🔧 Configuración

#### `GET /config`
Obtiene la configuración actual del sistema (sin credenciales sensibles).

**Respuesta (200):**
```json
{
  "app_name": "claude-slack-agent",
  "version": "1.0.0",
  "deployment_type": "production",
  "features": {
    "bigquery_enabled": true,
    "unit_tests_enabled": false,
    "code_analysis_enabled": true,
    "security_checks_enabled": true
  },
  "limits": {
    "max_code_length": 10000,
    "max_execution_time": 30,
    "max_workers": 4
  },
  "supported_languages": [
    "python",
    "javascript",
    "typescript",
    "java",
    "csharp",
    "go",
    "rust",
    "php",
    "ruby",
    "swift",
    "kotlin",
    "dart"
  ]
}
```

### 5. 📝 Logs

#### `GET /logs`
Obtiene logs recientes del sistema.

**Parámetros de Query:**
- `level`: Nivel de log (DEBUG, INFO, WARNING, ERROR)
- `limit`: Número máximo de entradas (default: 100)
- `since`: Timestamp desde cuando obtener logs

**Respuesta (200):**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T12:00:00.000Z",
      "level": "INFO",
      "message": "Processing message from user U1234567890",
      "context": {
        "user_id": "U1234567890",
        "channel_id": "C1234567890",
        "message_type": "code_generation"
      }
    },
    {
      "timestamp": "2024-01-01T11:59:45.000Z",
      "level": "DEBUG",
      "message": "Claude API response received",
      "context": {
        "response_time_ms": 450,
        "tokens_used": 150
      }
    }
  ],
  "total_count": 1234,
  "has_more": true
}
```

### 6. 🧪 Testing

#### `POST /test/code-generation`
Endpoint para probar la generación de código.

**Cuerpo de Solicitud:**
```json
{
  "prompt": "Crea una función que ordene una lista usando quicksort",
  "language": "python",
  "context": "Esta función será usada en un sistema de análisis de datos"
}
```

**Respuesta (200):**
```json
{
  "generated_code": "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
  "explanation": "Esta implementación de quicksort utiliza...",
  "language": "python",
  "estimated_complexity": "O(n log n) promedio, O(n²) peor caso",
  "processing_time_ms": 850,
  "tokens_used": 120
}
```

#### `POST /test/code-analysis`
Endpoint para probar el análisis de código.

**Cuerpo de Solicitud:**
```json
{
  "code": "def divide(a, b):\n    return a / b",
  "language": "python"
}
```

**Respuesta (200):**
```json
{
  "analysis": {
    "issues": [
      {
        "type": "error",
        "severity": "high",
        "line": 2,
        "message": "Potential division by zero",
        "suggestion": "Add check for b != 0 before division"
      }
    ],
    "metrics": {
      "complexity": 1,
      "maintainability_index": 85,
      "lines_of_code": 2
    },
    "suggestions": [
      "Add input validation",
      "Add docstring documentation",
      "Consider using type hints"
    ]
  },
  "processing_time_ms": 200
}
```

## 🔐 Autenticación y Seguridad

### Slack Webhook Verification
Todos los webhooks de Slack son verificados usando:
- **X-Slack-Signature**: Firma HMAC-SHA256
- **X-Slack-Request-Timestamp**: Timestamp de la solicitud
- **Verificación de token**: Token de verificación de Slack

### Rate Limiting
- **Por usuario**: 10 requests por minuto
- **Global**: 100 requests por minuto
- **Por IP**: 50 requests por minuto

### Headers de Seguridad
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## 📊 Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Solicitud exitosa |
| 201 | Recurso creado exitosamente |
| 400 | Solicitud malformada |
| 401 | No autorizado |
| 403 | Prohibido |
| 404 | Recurso no encontrado |
| 429 | Demasiadas solicitudes (rate limit) |
| 500 | Error interno del servidor |
| 502 | Bad Gateway (error de API externa) |
| 503 | Servicio no disponible |

## 🔄 Webhooks Salientes

### Notificaciones de Estado
El agente puede enviar webhooks a URLs configuradas para notificar cambios de estado:

```json
{
  "event": "agent_status_change",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "previous_status": "healthy",
    "current_status": "degraded",
    "reason": "Anthropic API timeout",
    "affected_components": ["code_generation"]
  }
}
```

### Métricas Periódicas
```json
{
  "event": "metrics_report",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "period": "hourly",
  "data": {
    "requests_processed": 156,
    "average_response_time_ms": 450,
    "error_rate_percent": 2.5,
    "active_users": 23
  }
}
```

## 🛠️ SDKs y Clientes

### Python Client
```python
import requests

class ClaudeAgentClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def generate_code(self, prompt, language="python"):
        data = {"prompt": prompt, "language": language}
        response = requests.post(f"{self.base_url}/test/code-generation", json=data)
        return response.json()

# Uso
client = ClaudeAgentClient("http://localhost:8080")
health = client.health_check()
code = client.generate_code("Create a sorting function", "python")
```

### JavaScript Client
```javascript
class ClaudeAgentClient {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }
    
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }
    
    async generateCode(prompt, language = 'python') {
        const response = await fetch(`${this.baseUrl}/test/code-generation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, language })
        });
        return response.json();
    }
}

// Uso
const client = new ClaudeAgentClient('http://localhost:8080');
const health = await client.healthCheck();
const code = await client.generateCode('Create a sorting function', 'python');
```

## 📚 Ejemplos de Integración

### Monitoreo con Prometheus
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'claude-agent'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Alertas con Grafana
```json
{
  "alert": {
    "name": "Claude Agent High Error Rate",
    "condition": "avg(rate(claude_agent_errors_total[5m])) > 0.1",
    "message": "Claude Agent error rate is above 10%"
  }
}
```

### Integración con Slack (Notificaciones)
```python
import requests

def send_slack_notification(webhook_url, message):
    payload = {
        "text": f"🤖 Claude Agent Alert: {message}",
        "channel": "#alerts",
        "username": "Claude Agent Monitor"
    }
    requests.post(webhook_url, json=payload)
```