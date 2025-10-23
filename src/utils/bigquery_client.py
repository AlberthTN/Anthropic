"""
BigQuery Client para memoria persistente del agente Claude.
Maneja la conexión y operaciones con BigQuery para almacenar conversaciones y contexto.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud.exceptions import NotFound, Forbidden, BadRequest, Conflict
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)

class BigQueryConnectionError(Exception):
    """Error específico para problemas de conexión con BigQuery."""
    pass

class BigQueryConfigurationError(Exception):
    """Error específico para problemas de configuración de BigQuery."""
    pass

class BigQueryClient:
    """Cliente para interactuar con BigQuery para memoria persistente."""
    
    def __init__(self):
        """Inicializa el cliente de BigQuery con las credenciales del .env"""
        logger.info("🔧 Inicializando cliente BigQuery...")
        
        # Validar variables de entorno requeridas
        self._validate_environment_variables()
        
        self.project_id = os.getenv('BIGQUERY_PROJECT_ID')
        self.dataset_id = os.getenv('BIGQUERY_DATASET')
        self.location = os.getenv('BIGQUERY_LOCATION', 'us-central1')
        self.max_bytes_billed = int(os.getenv('BIGQUERY_MAX_BYTES_BILLED', '30000000000'))
        
        logger.info(f"📊 Configuración BigQuery:")
        logger.info(f"   - Proyecto: {self.project_id}")
        logger.info(f"   - Dataset: {self.dataset_id}")
        logger.info(f"   - Ubicación: {self.location}")
        logger.info(f"   - Límite de bytes: {self.max_bytes_billed:,}")
        
        # Configurar credenciales desde JSON en variable de entorno
        try:
            self._initialize_credentials()
            logger.info("✅ Cliente BigQuery inicializado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando BigQuery: {e}")
            raise BigQueryConnectionError(f"No se pudo inicializar BigQuery: {e}")
    
    def _validate_environment_variables(self):
        """Valida que todas las variables de entorno requeridas estén presentes."""
        required_vars = [
            'BIGQUERY_PROJECT_ID',
            'BIGQUERY_DATASET', 
            'GOOGLE_APPLICATION_CREDENTIALS_JSON'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            error_msg = f"Variables de entorno faltantes: {', '.join(missing_vars)}"
            logger.error(f"❌ {error_msg}")
            raise BigQueryConfigurationError(error_msg)
        
        logger.info("✅ Variables de entorno validadas correctamente")
    
    def _initialize_credentials(self):
        """Inicializa las credenciales de Google Cloud."""
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        
        try:
            logger.info("🔐 Configurando credenciales de Google Cloud...")
            credentials_info = json.loads(credentials_json)
            
            # Validar campos requeridos en las credenciales
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in credentials_info]
            
            if missing_fields:
                raise BigQueryConfigurationError(f"Campos faltantes en credenciales: {', '.join(missing_fields)}")
            
            self.credentials = service_account.Credentials.from_service_account_info(credentials_info)
            self.client = bigquery.Client(
                credentials=self.credentials,
                project=self.project_id,
                location=self.location
            )
            
            # Probar la conexión
            self._test_connection()
            logger.info("✅ Credenciales configuradas y conexión verificada")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON de credenciales: {e}")
            raise BigQueryConfigurationError("Formato inválido en GOOGLE_APPLICATION_CREDENTIALS_JSON")
        except Exception as e:
            logger.error(f"❌ Error configurando credenciales: {e}")
            raise
    
    def _test_connection(self):
        """Prueba la conexión con BigQuery."""
        try:
            # Intentar listar datasets para verificar conexión
            list(self.client.list_datasets(max_results=1))
            logger.info("🔗 Conexión con BigQuery verificada")
        except Forbidden as e:
            logger.error(f"❌ Sin permisos para acceder a BigQuery: {e}")
            raise BigQueryConnectionError("Sin permisos suficientes para BigQuery")
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {e}")
            raise BigQueryConnectionError(f"No se pudo conectar a BigQuery: {e}")
    
    def create_dataset_if_not_exists(self) -> bool:
        """Crea el dataset si no existe."""
        try:
            logger.info(f"📁 Verificando dataset '{self.dataset_id}'...")
            dataset_ref = self.client.dataset(self.dataset_id)
            
            try:
                dataset = self.client.get_dataset(dataset_ref)
                logger.info(f"✅ Dataset '{self.dataset_id}' ya existe")
                logger.info(f"   - Creado: {dataset.created}")
                logger.info(f"   - Ubicación: {dataset.location}")
                return True
                
            except NotFound:
                logger.info(f"📁 Creando dataset '{self.dataset_id}'...")
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = self.location
                dataset.description = "Dataset para memoria persistente del agente Claude"
                
                created_dataset = self.client.create_dataset(dataset)
                logger.info(f"✅ Dataset '{self.dataset_id}' creado exitosamente")
                logger.info(f"   - ID: {created_dataset.dataset_id}")
                logger.info(f"   - Ubicación: {created_dataset.location}")
                return True
                
        except Forbidden as e:
            logger.error(f"❌ Sin permisos para crear dataset: {e}")
            return False
        except Conflict as e:
            logger.warning(f"⚠️ Dataset ya existe (conflicto): {e}")
            return True
        except Exception as e:
            logger.error(f"❌ Error inesperado creando dataset: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Crea las tablas necesarias para la memoria persistente."""
        try:
            logger.info("🏗️ Iniciando creación de tablas...")
            
            # Crear dataset primero
            if not self.create_dataset_if_not_exists():
                logger.error("❌ No se pudo crear o verificar el dataset")
                return False
            
            # Esquema para tabla de usuarios
            users_schema = [
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("slack_user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("real_name", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("display_name", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("team_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("timezone", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("profile_image", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("is_admin", "BOOLEAN", mode="NULLABLE"),
                bigquery.SchemaField("is_bot", "BOOLEAN", mode="NULLABLE"),
                bigquery.SchemaField("preferences", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            # Esquema para tabla de conversaciones
            conversations_schema = [
                bigquery.SchemaField("conversation_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("slack_channel_id", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("slack_thread_ts", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("conversation_type", "STRING", mode="REQUIRED"),  # 'dm', 'channel', 'thread'
                bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # 'active', 'archived', 'deleted'
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("last_activity_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            # Esquema para tabla de mensajes
            messages_schema = [
                bigquery.SchemaField("message_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("conversation_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("slack_message_ts", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("message_type", "STRING", mode="REQUIRED"),  # 'user', 'assistant', 'system'
                bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
                bigquery.SchemaField("tokens_used", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("model_used", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("response_time_ms", "INTEGER", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            # Esquema para tabla de contexto
            context_schema = [
                bigquery.SchemaField("context_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("conversation_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("context_type", "STRING", mode="REQUIRED"),  # 'summary', 'entities', 'preferences', 'history'
                bigquery.SchemaField("context_data", "JSON", mode="REQUIRED"),
                bigquery.SchemaField("relevance_score", "FLOAT", mode="NULLABLE"),
                bigquery.SchemaField("expires_at", "TIMESTAMP", mode="NULLABLE"),
                bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            # Crear tablas
            tables_to_create = [
                ("users", users_schema),
                ("conversations", conversations_schema),
                ("messages", messages_schema),
                ("context", context_schema)
            ]
            
            created_count = 0
            existing_count = 0
            
            for table_name, schema in tables_to_create:
                try:
                    logger.info(f"🔍 Verificando tabla '{table_name}'...")
                    table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
                    
                    try:
                        existing_table = self.client.get_table(table_id)
                        logger.info(f"✅ Tabla '{table_name}' ya existe")
                        logger.info(f"   - Filas: {existing_table.num_rows:,}")
                        logger.info(f"   - Tamaño: {existing_table.num_bytes:,} bytes")
                        existing_count += 1
                        
                    except NotFound:
                        logger.info(f"🏗️ Creando tabla '{table_name}'...")
                        table = bigquery.Table(table_id, schema=schema)
                        created_table = self.client.create_table(table)
                        logger.info(f"✅ Tabla '{table_name}' creada exitosamente")
                        logger.info(f"   - ID: {created_table.table_id}")
                        logger.info(f"   - Esquema: {len(schema)} campos")
                        created_count += 1
                        
                except Forbidden as e:
                    logger.error(f"❌ Sin permisos para crear tabla '{table_name}': {e}")
                    return False
                except BadRequest as e:
                    logger.error(f"❌ Error en esquema de tabla '{table_name}': {e}")
                    return False
                except Exception as e:
                    logger.error(f"❌ Error inesperado creando tabla '{table_name}': {e}")
                    return False
            
            logger.info(f"🎉 Proceso de tablas completado:")
            logger.info(f"   - Tablas creadas: {created_count}")
            logger.info(f"   - Tablas existentes: {existing_count}")
            logger.info(f"   - Total: {created_count + existing_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error crítico creando tablas: {e}")
            return False
    
    def execute_query(self, query: str, parameters: Optional[List] = None) -> List[Dict]:
        """Ejecuta una consulta SQL en BigQuery."""
        try:
            logger.info(f"🔍 Ejecutando consulta BigQuery...")
            logger.debug(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
            
            job_config = bigquery.QueryJobConfig()
            job_config.maximum_bytes_billed = self.max_bytes_billed
            
            if parameters:
                job_config.query_parameters = parameters
                logger.debug(f"Parámetros: {len(parameters)} elementos")
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            # Obtener estadísticas del job
            job_stats = query_job._properties.get('statistics', {})
            query_stats = job_stats.get('query', {})
            
            bytes_processed = int(query_stats.get('totalBytesProcessed', 0))
            bytes_billed = int(query_stats.get('totalBytesBilled', 0))
            
            result_list = [dict(row) for row in results]
            
            logger.info(f"✅ Consulta ejecutada exitosamente")
            logger.info(f"   - Filas devueltas: {len(result_list):,}")
            logger.info(f"   - Bytes procesados: {bytes_processed:,}")
            logger.info(f"   - Bytes facturados: {bytes_billed:,}")
            
            return result_list
            
        except Forbidden as e:
            logger.error(f"❌ Sin permisos para ejecutar consulta: {e}")
            raise BigQueryConnectionError("Sin permisos para ejecutar consulta")
        except BadRequest as e:
            logger.error(f"❌ Error en sintaxis de consulta: {e}")
            raise ValueError(f"Consulta SQL inválida: {e}")
        except Exception as e:
            logger.error(f"❌ Error ejecutando consulta: {e}")
            raise
    
    def insert_rows(self, table_name: str, rows: List[Dict]) -> bool:
        """Inserta filas en una tabla de BigQuery."""
        try:
            if not rows:
                logger.warning(f"⚠️ No hay filas para insertar en '{table_name}'")
                return True
            
            logger.info(f"💾 Insertando {len(rows)} filas en tabla '{table_name}'...")
            
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            try:
                table = self.client.get_table(table_id)
            except NotFound:
                logger.error(f"❌ Tabla '{table_name}' no existe")
                return False
            
            # Validar estructura de las filas
            if rows:
                sample_row = rows[0]
                logger.debug(f"Campos en fila de ejemplo: {list(sample_row.keys())}")
            
            errors = self.client.insert_rows_json(table, rows)
            
            if errors:
                logger.error(f"❌ Errores insertando filas en '{table_name}':")
                for i, error in enumerate(errors[:5]):  # Mostrar solo los primeros 5 errores
                    logger.error(f"   Error {i+1}: {error}")
                if len(errors) > 5:
                    logger.error(f"   ... y {len(errors) - 5} errores más")
                return False
            
            logger.info(f"✅ {len(rows)} filas insertadas exitosamente en '{table_name}'")
            return True
            
        except Forbidden as e:
            logger.error(f"❌ Sin permisos para insertar en tabla '{table_name}': {e}")
            return False
        except BadRequest as e:
            logger.error(f"❌ Error en datos para tabla '{table_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado insertando en '{table_name}': {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Obtiene información sobre una tabla."""
        try:
            logger.info(f"📊 Obteniendo información de tabla '{table_name}'...")
            
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            table = self.client.get_table(table_id)
            
            info = {
                "table_id": table.table_id,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created": table.created,
                "modified": table.modified,
                "schema": [{"name": field.name, "type": field.field_type, "mode": field.mode} 
                          for field in table.schema]
            }
            
            logger.info(f"✅ Información de tabla '{table_name}' obtenida:")
            logger.info(f"   - Filas: {info['num_rows']:,}")
            logger.info(f"   - Tamaño: {info['num_bytes']:,} bytes")
            logger.info(f"   - Campos: {len(info['schema'])}")
            
            return info
            
        except NotFound:
            logger.warning(f"⚠️ Tabla '{table_name}' no encontrada")
            return None
        except Forbidden as e:
            logger.error(f"❌ Sin permisos para acceder a tabla '{table_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo información de tabla '{table_name}': {e}")
            return None