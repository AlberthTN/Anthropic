"""
Memory Manager para el agente Claude.
Gestiona la memoria persistente usando BigQuery para almacenar y recuperar contexto de conversaciones.
"""

import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from .bigquery_client import BigQueryClient, BigQueryConnectionError, BigQueryConfigurationError

logger = logging.getLogger(__name__)

class MemoryManagerError(Exception):
    """Error específico para problemas del MemoryManager."""
    pass

class MemoryValidationError(Exception):
    """Error específico para problemas de validación de datos."""
    pass

@dataclass
class User:
    """Modelo de datos para usuario."""
    user_id: str
    slack_user_id: str
    real_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    team_id: Optional[str] = None
    timezone: Optional[str] = None
    profile_image: Optional[str] = None
    is_admin: Optional[bool] = False
    is_bot: Optional[bool] = False
    preferences: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Conversation:
    """Modelo de datos para conversación."""
    conversation_id: str
    user_id: str
    slack_channel_id: Optional[str] = None
    slack_thread_ts: Optional[str] = None
    conversation_type: str = "dm"  # 'dm', 'channel', 'thread'
    title: Optional[str] = None
    status: str = "active"  # 'active', 'archived', 'deleted'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None

@dataclass
class Message:
    """Modelo de datos para mensaje."""
    message_id: str
    conversation_id: str
    user_id: str
    slack_message_ts: Optional[str] = None
    message_type: str = "user"  # 'user', 'assistant', 'system'
    content: str = ""
    metadata: Optional[Dict] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass
class Context:
    """Modelo de datos para contexto."""
    context_id: str
    conversation_id: str
    user_id: str
    context_type: str  # 'summary', 'entities', 'preferences', 'history'
    context_data: Dict
    relevance_score: Optional[float] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class MemoryManager:
    """Gestor de memoria persistente para el agente Claude."""
    
    def __init__(self):
        """Inicializa el gestor de memoria."""
        logger.info("🧠 Inicializando MemoryManager...")
        
        try:
            self.bq_client = BigQueryClient()
            logger.info("✅ BigQuery client inicializado correctamente")
            
            # Inicializar las tablas
            if self._initialize_tables():
                logger.info("✅ MemoryManager inicializado exitosamente")
            else:
                raise MemoryManagerError("No se pudieron inicializar las tablas")
                
        except (BigQueryConnectionError, BigQueryConfigurationError) as e:
            logger.error(f"❌ Error de configuración BigQuery: {e}")
            raise MemoryManagerError(f"Error configurando BigQuery: {e}")
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando MemoryManager: {e}")
            raise MemoryManagerError(f"Error inicializando MemoryManager: {e}")
    
    def _initialize_tables(self) -> bool:
        """Inicializa las tablas necesarias en BigQuery."""
        try:
            logger.info("🏗️ Inicializando tablas de memoria persistente...")
            success = self.bq_client.create_tables()
            
            if success:
                logger.info("✅ Tablas de memoria inicializadas correctamente")
                return True
            else:
                logger.error("❌ Error inicializando tablas de memoria")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error crítico inicializando tablas: {e}")
            return False
    
    # Métodos para usuarios
    def create_or_update_user(self, slack_user_info: Dict) -> Optional[User]:
        """Crea o actualiza un usuario basado en información de Slack."""
        try:
            logger.info("👤 Procesando información de usuario de Slack...")
            
            slack_user_id = slack_user_info.get('id')
            if not slack_user_id:
                logger.error("❌ ID de usuario de Slack no proporcionado")
                raise MemoryValidationError("ID de usuario de Slack requerido")
            
            # Validar estructura básica de datos
            if not isinstance(slack_user_info, dict):
                logger.error("❌ Información de usuario inválida")
                raise MemoryValidationError("Información de usuario debe ser un diccionario")
            
            # Buscar usuario existente
            existing_user = self.get_user_by_slack_id(slack_user_id)
            
            now = datetime.now(timezone.utc)
            
            if existing_user:
                logger.info(f"🔄 Usuario existente encontrado: {slack_user_id}")
                # Para evitar problemas con streaming buffer, simplemente retornamos el usuario existente
                # sin hacer UPDATE. En un entorno de producción, se podría implementar una cola
                # para actualizaciones diferidas o usar MERGE en lugar de UPDATE
                logger.debug("⚠️ Saltando actualización para evitar conflicto con streaming buffer")
                return User(
                    user_id=existing_user['user_id'],
                    slack_user_id=existing_user['slack_user_id'],
                    real_name=existing_user.get('real_name'),
                    display_name=existing_user.get('display_name'),
                    email=existing_user.get('email'),
                    team_id=existing_user.get('team_id'),
                    timezone=existing_user.get('timezone'),
                    profile_image=existing_user.get('profile_image'),
                    is_admin=existing_user.get('is_admin', False),
                    is_bot=existing_user.get('is_bot', False),
                    preferences=existing_user.get('preferences', {}),
                    created_at=existing_user.get('created_at'),
                    updated_at=existing_user.get('updated_at')
                )
            
            else:
                logger.info(f"➕ Creando nuevo usuario: {slack_user_id}")
                # Crear nuevo usuario
                user_id = str(uuid.uuid4())
                user_data = {
                    'user_id': user_id,
                    'slack_user_id': slack_user_id,
                    'real_name': slack_user_info.get('real_name'),
                    'display_name': slack_user_info.get('profile', {}).get('display_name'),
                    'email': slack_user_info.get('profile', {}).get('email'),
                    'team_id': slack_user_info.get('team_id'),
                    'timezone': slack_user_info.get('tz'),
                    'profile_image': slack_user_info.get('profile', {}).get('image_192'),
                    'is_admin': slack_user_info.get('is_admin', False),
                    'is_bot': slack_user_info.get('is_bot', False),
                    'preferences': json.dumps(slack_user_info.get('profile', {})),
                    'created_at': now.isoformat(),
                    'updated_at': now.isoformat()
                }
                
                success = self.bq_client.insert_rows('users', [user_data])
                if success:
                    logger.info(f"✅ Usuario creado exitosamente: {slack_user_id}")
                    return User(**{k: v for k, v in user_data.items() if k not in ['created_at', 'updated_at']},
                               created_at=now, updated_at=now)
                else:
                    logger.error(f"❌ Error insertando usuario en BigQuery: {slack_user_id}")
                    raise MemoryManagerError("No se pudo insertar el usuario en la base de datos")
                
        except (MemoryValidationError, MemoryManagerError):
            raise
        except Exception as e:
            logger.error(f"❌ Error crítico creando/actualizando usuario: {e}")
            raise MemoryManagerError(f"Error procesando usuario: {e}")
    
    def get_user_by_slack_id(self, slack_user_id: str) -> Optional[Dict]:
        """Obtiene un usuario por su ID de Slack."""
        try:
            if not slack_user_id:
                logger.error("❌ ID de Slack no proporcionado para búsqueda")
                return None
                
            logger.debug(f"🔍 Buscando usuario por Slack ID: {slack_user_id}")
            
            query = f"""
            SELECT * FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.users`
            WHERE slack_user_id = @slack_user_id
            LIMIT 1
            """
            
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("slack_user_id", "STRING", slack_user_id)
                ]
            )
            
            query_job = self.bq_client.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                logger.debug(f"✅ Usuario encontrado: {slack_user_id}")
                return dict(results[0])
            else:
                logger.debug(f"ℹ️ Usuario no encontrado: {slack_user_id}")
                return None
             
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuario por Slack ID {slack_user_id}: {e}")
            return None

    # Métodos para conversaciones
    def create_conversation(self, user_id: str, slack_channel_id: Optional[str] = None, 
                          slack_thread_ts: Optional[str] = None, 
                          conversation_type: str = "dm") -> Optional[Conversation]:
        """Crea una nueva conversación."""
        try:
            if not user_id:
                logger.error("❌ ID de usuario requerido para crear conversación")
                raise MemoryValidationError("ID de usuario requerido")
                
            logger.info(f"💬 Creando nueva conversación para usuario: {user_id}")
            
            conversation_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            conversation_data = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'slack_channel_id': slack_channel_id,
                'slack_thread_ts': slack_thread_ts,
                'conversation_type': conversation_type,
                'title': None,
                'status': 'active',
                'created_at': now.isoformat(),
                'updated_at': now.isoformat(),
                'last_activity_at': now.isoformat()
            }
            
            success = self.bq_client.insert_rows('conversations', [conversation_data])
            if success:
                logger.info(f"✅ Conversación creada exitosamente: {conversation_id}")
                return Conversation(**{k: v for k, v in conversation_data.items() 
                                     if k not in ['created_at', 'updated_at', 'last_activity_at']},
                                   created_at=now, updated_at=now, last_activity_at=now)
            else:
                logger.error(f"❌ Error insertando conversación en BigQuery")
                raise MemoryManagerError("No se pudo crear la conversación en la base de datos")
            
        except (MemoryValidationError, MemoryManagerError):
            raise
        except Exception as e:
            logger.error(f"❌ Error crítico creando conversación: {e}")
            raise MemoryManagerError(f"Error creando conversación: {e}")
    
    def get_or_create_conversation(self, user_id: str, slack_channel_id: Optional[str] = None,
                                 slack_thread_ts: Optional[str] = None) -> Optional[Conversation]:
        """Obtiene una conversación existente o crea una nueva."""
        try:
            if not user_id:
                logger.error("❌ ID de usuario requerido para obtener/crear conversación")
                raise MemoryValidationError("ID de usuario requerido")
                
            logger.debug(f"🔍 Buscando conversación existente para usuario: {user_id}")
            
            # Buscar conversación existente
            query = f"""
            SELECT * FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.conversations`
            WHERE user_id = @user_id
            """
            
            params = [("user_id", "STRING", user_id)]
            
            if slack_channel_id:
                query += " AND slack_channel_id = @slack_channel_id"
                params.append(("slack_channel_id", "STRING", slack_channel_id))
            
            if slack_thread_ts:
                query += " AND slack_thread_ts = @slack_thread_ts"
                params.append(("slack_thread_ts", "STRING", slack_thread_ts))
            
            query += " AND status = 'active' ORDER BY last_activity_at DESC LIMIT 1"
            
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(name, type_, value) 
                    for name, type_, value in params
                ]
            )
            
            query_job = self.bq_client.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                logger.debug(f"✅ Conversación existente encontrada")
                result = dict(results[0])
                return Conversation(**{k: v for k, v in result.items() 
                                     if k not in ['created_at', 'updated_at', 'last_activity_at']},
                                   created_at=result['created_at'], 
                                   updated_at=result['updated_at'],
                                   last_activity_at=result['last_activity_at'])
            
            # Si no existe, crear nueva conversación
            logger.info(f"➕ No se encontró conversación existente, creando nueva")
            conversation_type = "channel" if slack_channel_id else "dm"
            if slack_thread_ts:
                conversation_type = "thread"
            
            return self.create_conversation(user_id, slack_channel_id, slack_thread_ts, conversation_type)
            
        except (MemoryValidationError, MemoryManagerError):
            raise
        except Exception as e:
            logger.error(f"❌ Error crítico obteniendo/creando conversación: {e}")
            raise MemoryManagerError(f"Error procesando conversación: {e}")
    
    # Métodos para mensajes
    def save_message(self, conversation_id: str, user_id: str, content: str,
                    message_type: str = "user", slack_message_ts: Optional[str] = None,
                    metadata: Optional[Dict] = None, tokens_used: Optional[int] = None,
                    model_used: Optional[str] = None, response_time_ms: Optional[int] = None) -> Optional[Message]:
        """Guarda un mensaje en la conversación."""
        try:
            # Validaciones
            if not conversation_id:
                logger.error("❌ ID de conversación requerido para guardar mensaje")
                raise MemoryValidationError("ID de conversación requerido")
            if not user_id:
                logger.error("❌ ID de usuario requerido para guardar mensaje")
                raise MemoryValidationError("ID de usuario requerido")
            if not content.strip():
                logger.error("❌ Contenido del mensaje no puede estar vacío")
                raise MemoryValidationError("Contenido del mensaje requerido")
                
            logger.debug(f"💾 Guardando mensaje tipo '{message_type}' en conversación: {conversation_id}")
            
            message_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            message_data = {
                'message_id': message_id,
                'conversation_id': conversation_id,
                'user_id': user_id,
                'slack_message_ts': slack_message_ts,
                'message_type': message_type,
                'content': content,
                'metadata': json.dumps(metadata) if metadata else None,
                'tokens_used': tokens_used,
                'model_used': model_used,
                'response_time_ms': response_time_ms,
                'created_at': now.isoformat()
            }
            
            # Debug: Log de los datos del mensaje antes de insertar
            logger.info(f"🔍 [DEBUG] Datos del mensaje a insertar: {message_data}")
            
            success = self.bq_client.insert_rows('messages', [message_data])
            if success:
                # Actualizar última actividad de la conversación
                self.update_conversation_activity(conversation_id)
                
                logger.info(f"✅ Mensaje guardado exitosamente: {message_id}")
                return Message(**{k: v for k, v in message_data.items() if k != 'created_at'},
                              created_at=now)
            else:
                logger.error(f"❌ Error insertando mensaje en BigQuery")
                raise MemoryManagerError("No se pudo guardar el mensaje en la base de datos")
            
        except (MemoryValidationError, MemoryManagerError):
            raise
        except Exception as e:
            logger.error(f"❌ Error crítico guardando mensaje: {e}")
            raise MemoryManagerError(f"Error guardando mensaje: {e}")

    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict]:
        """Obtiene el historial de mensajes de una conversación."""
        try:
            if not conversation_id:
                logger.error("❌ ID de conversación requerido para obtener historial")
                return []
                
            logger.debug(f"📜 Obteniendo historial de conversación: {conversation_id} (límite: {limit})")
            
            query = f"""
            SELECT * FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.messages`
            WHERE conversation_id = @conversation_id
            ORDER BY created_at DESC
            LIMIT @limit
            """
            
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("conversation_id", "STRING", conversation_id),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            query_job = self.bq_client.client.query(query, job_config=job_config)
            results = [dict(row) for row in query_job.result()]
            
            # Invertir para tener orden cronológico
            history = list(reversed(results))
            logger.debug(f"✅ Historial obtenido: {len(history)} mensajes")
            return history
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de conversación {conversation_id}: {e}")
            return []
    
    def update_conversation_activity(self, conversation_id: str):
        """Actualiza la última actividad de una conversación."""
        try:
            if not conversation_id:
                logger.error("❌ ID de conversación requerido para actualizar actividad")
                return
                
            logger.debug(f"🔄 Actualizando actividad de conversación: {conversation_id}")
            
            # Por ahora, omitir la actualización para evitar problemas con streaming buffer
            # TODO: Implementar una estrategia diferente para actualizar la actividad
            logger.debug(f"⚠️ Omitiendo actualización de actividad por streaming buffer: {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando actividad de conversación {conversation_id}: {e}")
    
    # Métodos para contexto
    def save_context(self, conversation_id: str, user_id: str, context_type: str,
                    context_data: Dict, relevance_score: Optional[float] = None,
                    expires_at: Optional[datetime] = None) -> Optional[Context]:
        """Guarda contexto para una conversación."""
        try:
            # Validaciones
            if not conversation_id:
                logger.error("❌ ID de conversación requerido para guardar contexto")
                raise MemoryValidationError("ID de conversación requerido")
            if not user_id:
                logger.error("❌ ID de usuario requerido para guardar contexto")
                raise MemoryValidationError("ID de usuario requerido")
            if not context_type:
                logger.error("❌ Tipo de contexto requerido")
                raise MemoryValidationError("Tipo de contexto requerido")
            if not context_data:
                logger.error("❌ Datos de contexto requeridos")
                raise MemoryValidationError("Datos de contexto requeridos")
                
            logger.debug(f"🧠 Guardando contexto tipo '{context_type}' para conversación: {conversation_id}")
            
            context_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            context_row = {
                'context_id': context_id,
                'conversation_id': conversation_id,
                'user_id': user_id,
                'context_type': context_type,
                'context_data': context_data,
                'relevance_score': relevance_score,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }
            
            success = self.bq_client.insert_rows('context', [context_row])
            if success:
                logger.info(f"✅ Contexto guardado exitosamente: {context_id}")
                return Context(**{k: v for k, v in context_row.items() 
                                if k not in ['created_at', 'updated_at', 'expires_at']},
                              created_at=now, updated_at=now, expires_at=expires_at)
            else:
                logger.error(f"❌ Error insertando contexto en BigQuery")
                raise MemoryManagerError("No se pudo guardar el contexto en la base de datos")
            
        except (MemoryValidationError, MemoryManagerError):
            raise
        except Exception as e:
            logger.error(f"❌ Error crítico guardando contexto: {e}")
            raise MemoryManagerError(f"Error guardando contexto: {e}")
    
    def get_user_context(self, user_id: str, context_types: Optional[List[str]] = None) -> List[Dict]:
        """Obtiene el contexto de un usuario."""
        try:
            if not user_id:
                logger.error("❌ ID de usuario requerido para obtener contexto")
                return []
                
            logger.debug(f"🔍 Obteniendo contexto para usuario: {user_id}")
            
            query = f"""
            SELECT * FROM `{self.bq_client.project_id}.{self.bq_client.dataset_id}.context`
            WHERE user_id = @user_id
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP())
            """
            
            params = [("user_id", "STRING", user_id)]
            
            if context_types:
                placeholders = ", ".join([f"@type_{i}" for i in range(len(context_types))])
                query += f" AND context_type IN ({placeholders})"
                for i, context_type in enumerate(context_types):
                    params.append((f"type_{i}", "STRING", context_type))
            
            query += " ORDER BY created_at DESC"
            
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(name, type_, value) 
                    for name, type_, value in params
                ]
            )
            
            query_job = self.bq_client.client.query(query, job_config=job_config)
            results = [dict(row) for row in query_job.result()]
            
            logger.debug(f"✅ Contexto obtenido: {len(results)} registros")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo contexto de usuario {user_id}: {e}")
            return []
    
    def get_conversation_summary(self, conversation_id: str) -> Optional[str]:
        """Genera un resumen de la conversación para contexto."""
        try:
            if not conversation_id:
                logger.error("❌ ID de conversación requerido para generar resumen")
                return None
                
            logger.debug(f"📊 Generando resumen de conversación: {conversation_id}")
            
            messages = self.get_conversation_history(conversation_id, limit=20)
            if not messages:
                logger.debug(f"ℹ️ No hay mensajes para generar resumen")
                return None
            
            # Crear resumen básico
            user_messages = [msg for msg in messages if msg['message_type'] == 'user']
            assistant_messages = [msg for msg in messages if msg['message_type'] == 'assistant']
            
            summary = {
                'total_messages': len(messages),
                'user_messages': len(user_messages),
                'assistant_messages': len(assistant_messages),
                'last_topics': [msg['content'][:100] + "..." if len(msg['content']) > 100 
                               else msg['content'] for msg in messages[-5:]],
                'conversation_start': messages[0]['created_at'] if messages else None,
                'last_activity': messages[-1]['created_at'] if messages else None
            }
            
            logger.debug(f"✅ Resumen generado: {len(messages)} mensajes procesados")
            return json.dumps(summary)
            
        except Exception as e:
            logger.error(f"❌ Error generando resumen de conversación {conversation_id}: {e}")
            return None

    def save_agent_metrics(self, slack_user_id: str, user_name: str, user_input: str, 
                          response_time_ms: int, tokens_used: int) -> bool:
        """
        Guarda métricas del agente en la tabla agentes_slack.
        
        Args:
            slack_user_id: ID de Slack del usuario
            user_name: Nombre real del usuario
            user_input: Consulta original del usuario
            response_time_ms: Tiempo de respuesta en milisegundos
            tokens_used: Tokens utilizados en la ejecución
            
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario
        """
        try:
            logger.info(f"📊 Guardando métricas del agente para usuario: {slack_user_id}")
            
            # Validar parámetros requeridos
            if not slack_user_id or not user_name or not user_input:
                logger.error("❌ Parámetros requeridos faltantes para guardar métricas")
                return False
            
            # Preparar datos para inserción
            current_time = datetime.now(timezone.utc)
            
            agent_data = {
                'Id_Slack': slack_user_id,
                'Nombre_Usuario': user_name,
                'Fecha': current_time.isoformat(),
                'Nombre_Agente': 'A-Anthropic',
                'Input_Usuario': user_input,
                'Velocidad_de_Respuesta': response_time_ms,
                'Tokens_Ejecucion': tokens_used
            }
            
            logger.debug(f"🔍 Datos a insertar: {agent_data}")
            
            # Construir query de inserción para la tabla específica
            query = """
            INSERT INTO `neto-cloud.metricas_agentes.agentes_slack` 
            (`Id Slack`, `Nombre Usuario`, `Fecha`, `Nombre Agente`, `Input Usuario`, `Velocidad de Respuesta`, `Tokens Ejecucion`)
            VALUES (@id_slack, @nombre_usuario, @fecha, @nombre_agente, @input_usuario, @velocidad_respuesta, @tokens_ejecucion)
            """
            
            # Configurar parámetros de la query
            from google.cloud import bigquery
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("id_slack", "STRING", slack_user_id),
                    bigquery.ScalarQueryParameter("nombre_usuario", "STRING", user_name),
                    bigquery.ScalarQueryParameter("fecha", "STRING", current_time.isoformat()),
                    bigquery.ScalarQueryParameter("nombre_agente", "STRING", "A-Anthropic"),
                    bigquery.ScalarQueryParameter("input_usuario", "STRING", user_input),
                    bigquery.ScalarQueryParameter("velocidad_respuesta", "INTEGER", response_time_ms),
                    bigquery.ScalarQueryParameter("tokens_ejecucion", "INTEGER", tokens_used)
                ]
            )
            
            # Ejecutar la inserción
            query_job = self.bq_client.client.query(query, job_config=job_config)
            query_job.result()  # Esperar a que termine
            
            logger.info(f"✅ Métricas del agente guardadas exitosamente para usuario: {slack_user_id}")
            logger.debug(f"📊 Tokens: {tokens_used}, Tiempo: {response_time_ms}ms")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando métricas del agente: {e}")
            logger.error(f"   - Usuario: {slack_user_id}")
            logger.error(f"   - Input: {user_input[:100]}...")
            return False