# 🗄️ Configuración de BigQuery - Claude Programming Agent

## 📋 Visión General

El Claude Programming Agent utiliza Google BigQuery como sistema de memoria persistente para almacenar conversaciones, métricas y datos generados. Esta guía te ayudará a configurar BigQuery correctamente.

## 🚀 Configuración Inicial

### 1. Crear Proyecto en Google Cloud Platform

```bash
# Instalar Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Autenticarse
gcloud auth login

# Crear nuevo proyecto (opcional)
gcloud projects create tu-proyecto-claude-agent --name="Claude Agent"

# Configurar proyecto activo
gcloud config set project tu-proyecto-claude-agent

# Habilitar APIs necesarias
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerystorage.googleapis.com
```

### 2. Crear Cuenta de Servicio

```bash
# Crear cuenta de servicio
gcloud iam service-accounts create claude-agent-service \
    --display-name="Claude Agent Service Account" \
    --description="Service account for Claude Programming Agent"

# Asignar roles necesarios
gcloud projects add-iam-policy-binding tu-proyecto-claude-agent \
    --member="serviceAccount:claude-agent-service@tu-proyecto-claude-agent.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding tu-proyecto-claude-agent \
    --member="serviceAccount:claude-agent-service@tu-proyecto-claude-agent.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Generar clave JSON
gcloud iam service-accounts keys create claude-agent-key.json \
    --iam-account=claude-agent-service@tu-proyecto-claude-agent.iam.gserviceaccount.com
```

### 3. Configurar Variables de Entorno

```bash
# En tu archivo .env
BIGQUERY_PROJECT_ID=tu-proyecto-claude-agent
BIGQUERY_DATASET=agente_anthropic
BIGQUERY_LOCATION=us-central1
BIGQUERY_MAX_BYTES_BILLED=30000000000

# Contenido del archivo JSON de la cuenta de servicio
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"tu-proyecto-claude-agent",...}
```

## 🏗️ Estructura de la Base de Datos

### Dataset Principal: `agente_anthropic`

```sql
-- Crear dataset
CREATE SCHEMA IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic`
OPTIONS (
  description = "Dataset para Claude Programming Agent",
  location = "us-central1"
);
```

### Tabla 1: `conversaciones`
Almacena el historial completo de conversaciones.

```sql
CREATE TABLE IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic.conversaciones` (
  `Id Slack` STRING NOT NULL,
  `Nombre Usuario` STRING,
  `Fecha` STRING NOT NULL,
  `Nombre Agente` STRING DEFAULT 'A-Anthropic',
  `Input Usuario` STRING NOT NULL,
  `Respuesta Agente` STRING,
  `Contexto Conversacion` JSON,
  `Metadata` JSON,
  `Canal` STRING,
  `Thread Ts` STRING,
  `Tokens Utilizados` INTEGER,
  `Tiempo Respuesta Ms` INTEGER,
  `Tipo Consulta` STRING,
  `Lenguaje Programacion` STRING,
  `Estado` STRING DEFAULT 'completado',
  `Timestamp Creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  `Timestamp Actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', `Fecha`))
CLUSTER BY `Id Slack`, `Tipo Consulta`
OPTIONS (
  description = "Historial completo de conversaciones del agente Claude",
  partition_expiration_days = 365
);
```

### Tabla 2: `agentes_slack`
Métricas y estadísticas del agente.

```sql
CREATE TABLE IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic.agentes_slack` (
  `Id Slack` STRING NOT NULL,
  `Nombre Usuario` STRING,
  `Fecha` STRING NOT NULL,
  `Nombre Agente` STRING DEFAULT 'A-Anthropic',
  `Input Usuario` STRING NOT NULL,
  `Velocidad de Respuesta` INTEGER,
  `Tokens Ejecucion` INTEGER,
  `Tipo Operacion` STRING,
  `Estado Operacion` STRING DEFAULT 'exitoso',
  `Canal` STRING,
  `Timestamp Creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', `Fecha`))
CLUSTER BY `Id Slack`, `Tipo Operacion`
OPTIONS (
  description = "Métricas y estadísticas del agente Claude",
  partition_expiration_days = 730
);
```

### Tabla 3: `codigo_generado`
Código generado por el agente con metadatos.

```sql
CREATE TABLE IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic.codigo_generado` (
  `Id` STRING NOT NULL,
  `Id Slack` STRING NOT NULL,
  `Fecha` STRING NOT NULL,
  `Lenguaje` STRING NOT NULL,
  `Prompt Original` STRING NOT NULL,
  `Codigo Generado` STRING NOT NULL,
  `Explicacion` STRING,
  `Complejidad Estimada` STRING,
  `Lineas Codigo` INTEGER,
  `Funciones Detectadas` JSON,
  `Imports Detectados` JSON,
  `Calidad Score` FLOAT64,
  `Tiempo Generacion Ms` INTEGER,
  `Tokens Utilizados` INTEGER,
  `Version Agente` STRING DEFAULT '1.0.0',
  `Timestamp Creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', `Fecha`))
CLUSTER BY `Lenguaje`, `Id Slack`
OPTIONS (
  description = "Código generado por el agente con metadatos detallados",
  partition_expiration_days = 1095
);
```

### Tabla 4: `analisis_codigo`
Resultados de análisis de código.

```sql
CREATE TABLE IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic.analisis_codigo` (
  `Id` STRING NOT NULL,
  `Id Slack` STRING NOT NULL,
  `Fecha` STRING NOT NULL,
  `Lenguaje` STRING NOT NULL,
  `Codigo Original` STRING NOT NULL,
  `Problemas Detectados` JSON,
  `Sugerencias` JSON,
  `Metricas Calidad` JSON,
  `Vulnerabilidades` JSON,
  `Score Mantenibilidad` FLOAT64,
  `Complejidad Ciclomatica` INTEGER,
  `Lineas Codigo` INTEGER,
  `Tiempo Analisis Ms` INTEGER,
  `Version Analizador` STRING DEFAULT '1.0.0',
  `Timestamp Creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', `Fecha`))
CLUSTER BY `Lenguaje`, `Score Mantenibilidad`
OPTIONS (
  description = "Resultados de análisis de código realizados por el agente",
  partition_expiration_days = 730
);
```

### Tabla 5: `metricas_sistema`
Métricas del sistema y rendimiento.

```sql
CREATE TABLE IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic.metricas_sistema` (
  `Timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  `Metrica` STRING NOT NULL,
  `Valor` FLOAT64 NOT NULL,
  `Unidad` STRING,
  `Etiquetas` JSON,
  `Instancia` STRING DEFAULT 'default',
  `Version` STRING DEFAULT '1.0.0'
)
PARTITION BY DATE(`Timestamp`)
CLUSTER BY `Metrica`, `Instancia`
OPTIONS (
  description = "Métricas del sistema y rendimiento del agente",
  partition_expiration_days = 90
);
```

## 🔧 Script de Inicialización

Crea un archivo `create_tables.py` para inicializar todas las tablas:

```python
from google.cloud import bigquery
import os
import json

def create_bigquery_tables():
    """Crea todas las tablas necesarias en BigQuery"""
    
    # Configurar cliente
    credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if credentials_json:
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        client = bigquery.Client(credentials=credentials, project=credentials_info['project_id'])
    else:
        client = bigquery.Client()
    
    project_id = os.getenv('BIGQUERY_PROJECT_ID')
    dataset_id = os.getenv('BIGQUERY_DATASET', 'agente_anthropic')
    location = os.getenv('BIGQUERY_LOCATION', 'us-central1')
    
    # Crear dataset
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset {dataset_id} ya existe")
    except:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        dataset.description = "Dataset para Claude Programming Agent"
        client.create_dataset(dataset)
        print(f"✅ Dataset {dataset_id} creado")
    
    # Definir esquemas de tablas
    tables_schemas = {
        'conversaciones': [
            bigquery.SchemaField("Id Slack", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Nombre Usuario", "STRING"),
            bigquery.SchemaField("Fecha", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Nombre Agente", "STRING"),
            bigquery.SchemaField("Input Usuario", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Respuesta Agente", "STRING"),
            bigquery.SchemaField("Contexto Conversacion", "JSON"),
            bigquery.SchemaField("Metadata", "JSON"),
            bigquery.SchemaField("Canal", "STRING"),
            bigquery.SchemaField("Thread Ts", "STRING"),
            bigquery.SchemaField("Tokens Utilizados", "INTEGER"),
            bigquery.SchemaField("Tiempo Respuesta Ms", "INTEGER"),
            bigquery.SchemaField("Tipo Consulta", "STRING"),
            bigquery.SchemaField("Lenguaje Programacion", "STRING"),
            bigquery.SchemaField("Estado", "STRING"),
            bigquery.SchemaField("Timestamp Creacion", "TIMESTAMP"),
            bigquery.SchemaField("Timestamp Actualizacion", "TIMESTAMP"),
        ],
        'agentes_slack': [
            bigquery.SchemaField("Id Slack", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Nombre Usuario", "STRING"),
            bigquery.SchemaField("Fecha", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Nombre Agente", "STRING"),
            bigquery.SchemaField("Input Usuario", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Velocidad de Respuesta", "INTEGER"),
            bigquery.SchemaField("Tokens Ejecucion", "INTEGER"),
            bigquery.SchemaField("Tipo Operacion", "STRING"),
            bigquery.SchemaField("Estado Operacion", "STRING"),
            bigquery.SchemaField("Canal", "STRING"),
            bigquery.SchemaField("Timestamp Creacion", "TIMESTAMP"),
        ],
        'codigo_generado': [
            bigquery.SchemaField("Id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Id Slack", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Fecha", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Lenguaje", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Prompt Original", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Codigo Generado", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Explicacion", "STRING"),
            bigquery.SchemaField("Complejidad Estimada", "STRING"),
            bigquery.SchemaField("Lineas Codigo", "INTEGER"),
            bigquery.SchemaField("Funciones Detectadas", "JSON"),
            bigquery.SchemaField("Imports Detectados", "JSON"),
            bigquery.SchemaField("Calidad Score", "FLOAT64"),
            bigquery.SchemaField("Tiempo Generacion Ms", "INTEGER"),
            bigquery.SchemaField("Tokens Utilizados", "INTEGER"),
            bigquery.SchemaField("Version Agente", "STRING"),
            bigquery.SchemaField("Timestamp Creacion", "TIMESTAMP"),
        ]
    }
    
    # Crear tablas
    for table_name, schema in tables_schemas.items():
        table_ref = dataset_ref.table(table_name)
        try:
            client.get_table(table_ref)
            print(f"✅ Tabla {table_name} ya existe")
        except:
            table = bigquery.Table(table_ref, schema=schema)
            
            # Configurar particionado
            if table_name in ['conversaciones', 'agentes_slack', 'codigo_generado']:
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="Timestamp Creacion" if "Timestamp Creacion" in [f.name for f in schema] else None
                )
            
            client.create_table(table)
            print(f"✅ Tabla {table_name} creada")

if __name__ == "__main__":
    create_bigquery_tables()
```

## 📊 Consultas Útiles

### Estadísticas de Uso

```sql
-- Conversaciones por día
SELECT 
  DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', Fecha)) as fecha,
  COUNT(*) as total_conversaciones,
  COUNT(DISTINCT `Id Slack`) as usuarios_unicos
FROM `tu-proyecto-claude-agent.agente_anthropic.conversaciones`
WHERE DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', Fecha)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY fecha
ORDER BY fecha DESC;

-- Lenguajes más solicitados
SELECT 
  `Lenguaje Programacion`,
  COUNT(*) as solicitudes,
  AVG(`Tiempo Respuesta Ms`) as tiempo_promedio_ms
FROM `tu-proyecto-claude-agent.agente_anthropic.conversaciones`
WHERE `Lenguaje Programacion` IS NOT NULL
GROUP BY `Lenguaje Programacion`
ORDER BY solicitudes DESC;

-- Usuarios más activos
SELECT 
  `Id Slack`,
  `Nombre Usuario`,
  COUNT(*) as total_consultas,
  AVG(`Tokens Utilizados`) as tokens_promedio
FROM `tu-proyecto-claude-agent.agente_anthropic.conversaciones`
WHERE DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', Fecha)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY `Id Slack`, `Nombre Usuario`
ORDER BY total_consultas DESC
LIMIT 10;
```

### Análisis de Rendimiento

```sql
-- Métricas de rendimiento por hora
SELECT 
  EXTRACT(HOUR FROM PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', Fecha)) as hora,
  COUNT(*) as total_requests,
  AVG(`Velocidad de Respuesta`) as tiempo_promedio_ms,
  PERCENTILE_CONT(`Velocidad de Respuesta`, 0.95) OVER() as p95_tiempo_ms
FROM `tu-proyecto-claude-agent.agente_anthropic.agentes_slack`
WHERE DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', Fecha)) = CURRENT_DATE()
GROUP BY hora
ORDER BY hora;

-- Análisis de errores
SELECT 
  `Estado Operacion`,
  COUNT(*) as total,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
FROM `tu-proyecto-claude-agent.agente_anthropic.agentes_slack`
WHERE DATE(PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', Fecha)) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY `Estado Operacion`
ORDER BY total DESC;
```

## 🔒 Seguridad y Permisos

### Roles Recomendados

```bash
# Para el agente (mínimos permisos necesarios)
gcloud projects add-iam-policy-binding tu-proyecto-claude-agent \
    --member="serviceAccount:claude-agent-service@tu-proyecto-claude-agent.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding tu-proyecto-claude-agent \
    --member="serviceAccount:claude-agent-service@tu-proyecto-claude-agent.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"

# Para desarrolladores (acceso de lectura)
gcloud projects add-iam-policy-binding tu-proyecto-claude-agent \
    --member="user:desarrollador@empresa.com" \
    --role="roles/bigquery.dataViewer"

# Para administradores
gcloud projects add-iam-policy-binding tu-proyecto-claude-agent \
    --member="user:admin@empresa.com" \
    --role="roles/bigquery.admin"
```

### Configuración de Firewall

```bash
# Permitir solo IPs específicas para acceso a BigQuery
gcloud compute firewall-rules create allow-bigquery-access \
    --allow tcp:443 \
    --source-ranges="IP-DE-TU-SERVIDOR/32" \
    --target-tags=bigquery-client
```

## 💰 Optimización de Costos

### Configuración de Límites

```bash
# Configurar límite de bytes procesados
export BIGQUERY_MAX_BYTES_BILLED=30000000000  # 30GB

# Configurar expiración de particiones
# (ya configurado en las definiciones de tabla)
```

### Consultas Optimizadas

```sql
-- ✅ BUENO: Usar particiones y clustering
SELECT * FROM `proyecto.dataset.conversaciones`
WHERE DATE(Timestamp_Creacion) = '2024-01-01'
  AND Id_Slack = 'U1234567890';

-- ❌ MALO: Escanear toda la tabla
SELECT * FROM `proyecto.dataset.conversaciones`
WHERE CONTAINS_SUBSTR(Input_Usuario, 'python');

-- ✅ MEJOR: Usar índices de texto completo si es necesario
SELECT * FROM `proyecto.dataset.conversaciones`
WHERE DATE(Timestamp_Creacion) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND REGEXP_CONTAINS(Input_Usuario, r'python|Python');
```

## 🔧 Mantenimiento

### Script de Limpieza

```python
def cleanup_old_data():
    """Limpia datos antiguos para optimizar costos"""
    
    # Eliminar datos de métricas más antiguos de 90 días
    query = """
    DELETE FROM `tu-proyecto-claude-agent.agente_anthropic.metricas_sistema`
    WHERE DATE(Timestamp) < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
    """
    
    # Archivar conversaciones antiguas (más de 1 año)
    archive_query = """
    CREATE TABLE IF NOT EXISTS `tu-proyecto-claude-agent.agente_anthropic.conversaciones_archivo`
    PARTITION BY DATE(Timestamp_Creacion)
    AS SELECT * FROM `tu-proyecto-claude-agent.agente_anthropic.conversaciones`
    WHERE DATE(Timestamp_Creacion) < DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    """
```

### Monitoreo de Costos

```sql
-- Consulta para monitorear uso y costos
SELECT 
  DATE(creation_time) as fecha,
  job_type,
  user_email,
  SUM(total_bytes_processed) / POW(10, 9) as gb_procesados,
  COUNT(*) as total_jobs
FROM `tu-proyecto-claude-agent.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE DATE(creation_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY fecha, job_type, user_email
ORDER BY fecha DESC, gb_procesados DESC;
```