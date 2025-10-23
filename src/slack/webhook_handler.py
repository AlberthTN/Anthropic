"""
Manejador HTTP alternativo para webhooks de Slack.
Solo usar si se prefiere HTTP webhooks sobre Socket Mode.
"""

import os
import logging
import re
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Importar el validador de seguridad, el divisor de mensajes y el memory manager
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.utils.security_validator import security_validator
from src.utils.message_splitter import MessageSplitter
from src.utils.memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class SlackWebhookHandler:
    """
    Manejador HTTP para webhooks de Slack usando Flask.
    Alternativa a Socket Mode.
    """
    
    def __init__(self, agent):
        """Inicializa el manejador HTTP de webhooks."""
        self.agent = agent
        
        # Inicializar el divisor de mensajes
        self.message_splitter = MessageSplitter()
        
        # Inicializar MemoryManager para operaciones de BigQuery
        try:
            self.memory_manager = MemoryManager()
            logger.info("✅ MemoryManager inicializado correctamente en webhook_handler")
        except Exception as e:
            logger.error(f"❌ Error inicializando MemoryManager en webhook_handler: {str(e)}")
            self.memory_manager = None
        
        # Obtener configuración de variables de entorno
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        if not all([self.bot_token, self.signing_secret]):
            raise ValueError("Faltan variables de configuración de Slack en .env")
        
        # Inicializar la aplicación Slack Bolt (sin Socket Mode)
        self.app = App(
            token=self.bot_token,
            signing_secret=self.signing_secret
        )
        
        # Configurar manejadores de eventos
        self.setup_event_handlers()
        
        # Crear Flask app y handler
        self.flask_app = Flask(__name__)
        self.handler = SlackRequestHandler(self.app)
        
        # Configurar rutas
        self.setup_routes()
        
        logger.info("Manejador HTTP de webhooks de Slack inicializado correctamente")
    


    def setup_event_handlers(self):
        """Configura los manejadores de eventos de Slack."""
        
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            """Maneja menciones del bot."""
            self.handle_mention(event, say)
        
        @self.app.event("message")
        def handle_message(event, say):
            """Maneja mensajes directos."""
            if event.get("channel_type") == "im":
                self.handle_direct_message(event, say)
        
        @self.app.command("/code")
        def handle_code_command(ack, say, command):
            """Maneja el comando /code."""
            ack()
            self.handle_code_generation(command, say)
        
        @self.app.command("/help")
        def handle_help_command(ack, say):
            """Maneja el comando /help."""
            ack()
            self.show_help(say)
    
    def setup_routes(self):
        """Configura las rutas HTTP."""
        
        @self.flask_app.route("/slack/events", methods=["POST"])
        def slack_events():
            """Endpoint para eventos de Slack."""
            logger.info(f"📨 Evento recibido en /slack/events")
            logger.info(f"📋 Headers: {dict(request.headers)}")
            logger.info(f"📄 Body: {request.get_data(as_text=True)}")
            
            try:
                result = self.handler.handle(request)
                logger.info(f"✅ Evento procesado correctamente")
                return result
            except Exception as e:
                logger.error(f"❌ Error procesando evento: {str(e)}", exc_info=True)
                return jsonify({"error": "Internal server error"}), 500
        
        @self.flask_app.route("/health", methods=["GET"])
        def health_check():
            """Endpoint de salud."""
            return jsonify({"status": "healthy", "mode": "http_webhook"})
    
    def send_split_message(self, say, message, channel_id=None, timestamp=None):
        """
        Envía un mensaje dividido en partes si es necesario.
        
        Args:
            say: Función de Slack para enviar mensajes
            message: Mensaje a enviar (puede ser largo)
            channel_id: ID del canal (opcional, para reacciones)
            timestamp: Timestamp del mensaje original (opcional, para reacciones)
        """
        try:
            # Dividir el mensaje si es necesario
            parts = self.message_splitter.split_message(message)
            
            if len(parts) == 1:
                # Mensaje no necesita división
                say(parts[0])
                logger.info("📤 Mensaje enviado sin división")
            else:
                # Mensaje necesita división
                logger.info(f"📤 Enviando mensaje dividido en {len(parts)} partes")
                
                for i, part in enumerate(parts, 1):
                    if i == 1:
                        # Primera parte con encabezado
                        header = f"📝 *Respuesta completa (Parte {i}/{len(parts)}):*\n\n"
                        say(header + part)
                    else:
                        # Partes siguientes
                        header = f"📝 *Continuación (Parte {i}/{len(parts)}):*\n\n"
                        say(header + part)
                    
                    logger.info(f"✅ Enviada parte {i}/{len(parts)}")
                
                # Mensaje final de confirmación
                if len(parts) > 1:
                    say(f"✅ *Respuesta completa enviada en {len(parts)} partes.*")
                    
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje dividido: {str(e)}")
            # Fallback: enviar mensaje original sin dividir
            try:
                say(message)
                logger.info("📤 Mensaje enviado sin división (fallback)")
            except Exception as fallback_error:
                logger.error(f"❌ Error en fallback: {str(fallback_error)}")
                say("❌ Error enviando la respuesta. Por favor intenta de nuevo.")
    
    def handle_mention(self, event, say):
        """Maneja menciones del bot."""
        try:
            logger.info(f"🔔 Procesando mención: {event}")
            user_id = event.get("user")
            channel_id = event.get("channel")
            timestamp = event.get("ts")
            text = event.get("text", "").replace(f"<@{self.app.client.auth_test()['user_id']}>", "").strip()
            
            logger.info(f"👤 Usuario: {user_id}, Texto: '{text}'")
            
            # Obtener información del usuario para BigQuery
            user_info = None
            if self.memory_manager:
                try:
                    user_info = self.app.client.users_info(user=user_id)["user"]
                    logger.info(f"📋 Información del usuario obtenida: {user_info.get('name', 'N/A')}")
                    
                    # Crear o actualizar usuario en BigQuery
                    slack_user_info = {
                        "id": user_id,
                        "name": user_info.get("name", ""),
                        "real_name": user_info.get("real_name", ""),
                        "email": user_info.get("profile", {}).get("email", ""),
                        "is_bot": user_info.get("is_bot", False)
                    }
                    
                    self.memory_manager.create_or_update_user(slack_user_info)
                    logger.info(f"✅ [BigQuery] Usuario creado/actualizado exitosamente: {user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ [BigQuery] Error creando/actualizando usuario {user_id}: {str(e)}")
            else:
                logger.warning(f"⚠️ MemoryManager no disponible - usuario {user_id} no se guardará")
            
            # Obtener o crear conversación en BigQuery
            conversation_id = None
            if self.memory_manager:
                try:
                    user_obj = self.memory_manager.get_user_by_slack_id(user_id)
                    if user_obj:
                        conversation = self.memory_manager.get_or_create_conversation(
                            user_obj["user_id"], f"Slack Channel: {channel_id}"
                        )
                        conversation_id = conversation.conversation_id if conversation else None
                        logger.info(f"✅ [BigQuery] Conversación obtenida/creada: {conversation_id}")
                    else:
                        logger.warning(f"⚠️ [BigQuery] Usuario no encontrado en BD: {user_id}")
                except Exception as e:
                    logger.error(f"❌ [BigQuery] Error obteniendo/creando conversación para {user_id}: {str(e)}")
            
            # Reaccionar con ojitos para indicar que se recibió el mensaje
            try:
                self.app.client.reactions_add(
                    channel=channel_id,
                    timestamp=timestamp,
                    name="eyes"
                )
                logger.info("👀 Reacción de ojitos agregada")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo agregar reacción de ojitos: {str(e)}")
            
            if not text:
                logger.info("📝 Enviando saludo por defecto")
                try:
                    self.send_split_message(say, "¡Hola! ¿En qué puedo ayudarte con programación?", channel_id, timestamp)
                    # Cambiar reacción a check verde
                    self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                    self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="white_check_mark")
                    logger.info("✅ Reacción cambiada a check verde")
                except Exception as e:
                    logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
                return
            
            # Procesar con el agente
            if self.agent:
                logger.info("🤖 Procesando con agente Claude...")
                
                # VALIDACIÓN DE SEGURIDAD ANTES DE PROCESAR
                logger.info("🔒 Iniciando validación de seguridad...")
                security_result = security_validator.validate_query(text)
                
                if not security_result.get("is_safe", True):
                    logger.warning(f"🚨 Consulta bloqueada por seguridad: {security_result.get('message', 'Consulta no segura')}")
                    try:
                        self.send_split_message(say, "❌ Lo siento, no puedo procesar esta consulta por razones de seguridad.", channel_id, timestamp)
                        # Cambiar reacción a X roja por bloqueo de seguridad
                        self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                        self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                        logger.info("❌ Reacción cambiada a X roja por bloqueo de seguridad")
                    except Exception as e:
                        logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
                    return
                
                logger.info(f"✅ Validación de seguridad exitosa: {security_result.get('message', 'Consulta segura')}")
                
                # Detectar si es un mensaje simple o técnico
                context = {
                    "text": text,
                    "user": user_id,
                    "channel": channel_id,
                    "event_type": "app_mention"
                }
                response = self.agent.process_request(context)
                logger.info(f"✅ Respuesta del agente: {response}")
                
                # Guardar mensaje del usuario y respuesta del bot en BigQuery
                if self.memory_manager and conversation_id:
                    try:
                        # Guardar mensaje del usuario
                        user_obj = self.memory_manager.get_user_by_slack_id(user_id)
                        if user_obj:
                            self.memory_manager.save_message(
                                conversation_id, user_obj["user_id"], text, "user"
                            )
                            logger.info(f"✅ [BigQuery] Mensaje del usuario guardado - Conv: {conversation_id}")
                            
                            # Guardar respuesta del bot con métricas de API
                            bot_response = response.get("text", "Error procesando solicitud") if response else "Error procesando solicitud"
                            
                            # Extraer métricas de API si están disponibles
                            api_metrics = response.get("api_metrics", {}) if response else {}
                            tokens_used = api_metrics.get("tokens_used")
                            model_used = api_metrics.get("model_used")
                            response_time_ms = api_metrics.get("response_time_ms")
                            
                            # Debug: Log de las métricas extraídas
                            logger.info(f"🔍 [DEBUG] API Metrics extraídas: tokens_used={tokens_used}, model_used={model_used}, response_time_ms={response_time_ms}")
                            logger.info(f"🔍 [DEBUG] Response completo: {response}")
                            
                            self.memory_manager.save_message(
                                conversation_id, 
                                user_obj["user_id"], 
                                bot_response, 
                                "assistant",
                                tokens_used=tokens_used,
                                model_used=model_used,
                                response_time_ms=response_time_ms
                            )
                            logger.info(f"✅ [BigQuery] Respuesta del bot guardada - Conv: {conversation_id}")
                            
                            # Guardar métricas del agente en tabla agentes_slack
                            if tokens_used and response_time_ms and user_info:
                                try:
                                    user_real_name = user_info.get("real_name", user_info.get("name", "Usuario desconocido"))
                                    success = self.memory_manager.save_agent_metrics(
                                        slack_user_id=user_id,
                                        user_name=user_real_name,
                                        user_input=text,
                                        response_time_ms=response_time_ms,
                                        tokens_used=tokens_used
                                    )
                                    if success:
                                        logger.info(f"✅ [BigQuery] Métricas del agente guardadas - Usuario: {user_id}")
                                    else:
                                        logger.warning(f"⚠️ [BigQuery] No se pudieron guardar las métricas del agente - Usuario: {user_id}")
                                except Exception as metrics_error:
                                    logger.error(f"❌ [BigQuery] Error guardando métricas del agente: {str(metrics_error)}")
                            else:
                                logger.warning(f"⚠️ [BigQuery] Datos insuficientes para guardar métricas del agente - tokens: {tokens_used}, tiempo: {response_time_ms}, user_info: {bool(user_info)}")
                        else:
                            logger.warning(f"⚠️ [BigQuery] Usuario no encontrado para guardar mensajes: {user_id}")
                    except Exception as e:
                        logger.error(f"❌ [BigQuery] Error guardando mensajes - Conv: {conversation_id}: {str(e)}")
                elif self.memory_manager and not conversation_id:
                    logger.warning(f"⚠️ [BigQuery] Conversación no disponible - mensajes no guardados para usuario {user_id}")
                elif not self.memory_manager:
                    logger.warning(f"⚠️ MemoryManager no disponible - mensajes no se guardarán para usuario {user_id}")
                
                try:
                    if response:
                        self.send_split_message(say, response.get("text", "Error procesando solicitud"), channel_id, timestamp)
                        # Cambiar reacción a check verde por respuesta exitosa
                        self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                        self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="white_check_mark")
                        logger.info("✅ Reacción cambiada a check verde")
                    else:
                        self.send_split_message(say, "Error procesando solicitud", channel_id, timestamp)
                        # Cambiar reacción a X roja por error
                        self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                        self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                        logger.info("❌ Reacción cambiada a X roja")
                except Exception as e:
                    logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
            else:
                logger.warning("⚠️ Agente no disponible")
                try:
                    self.send_split_message(say, "El agente no está disponible en este momento.", channel_id, timestamp)
                    # Cambiar reacción a X roja por error
                    self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                    self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                    logger.info("❌ Reacción cambiada a X roja")
                except Exception as e:
                    logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ Error en handle_mention: {str(e)}", exc_info=True)
            try:
                self.send_split_message(say, "Ocurrió un error procesando tu mensaje.", 
                                      channel_id if 'channel_id' in locals() else None, 
                                      timestamp if 'timestamp' in locals() else None)
                # Cambiar reacción a X roja por error
                if 'channel_id' in locals() and 'timestamp' in locals():
                    self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                    self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                    logger.info("❌ Reacción cambiada a X roja por excepción")
            except Exception as reaction_error:
                logger.warning(f"⚠️ Error cambiando reacción en excepción: {str(reaction_error)}")
    
    def handle_direct_message(self, event, say):
        """Maneja mensajes directos."""
        try:
            logger.info(f"💬 Procesando mensaje directo: {event}")
            user_id = event.get("user")
            channel_id = event.get("channel")
            timestamp = event.get("ts")
            text = event.get("text", "")
            
            logger.info(f"👤 Usuario: {user_id}, Texto: '{text}'")
            
            # Obtener información del usuario para BigQuery
            user_info = None
            if self.memory_manager:
                try:
                    user_info = self.app.client.users_info(user=user_id)["user"]
                    logger.info(f"📋 Información del usuario obtenida: {user_info.get('name', 'N/A')}")
                    
                    # Crear o actualizar usuario en BigQuery
                    slack_user_info = {
                        "id": user_id,
                        "name": user_info.get("name", ""),
                        "real_name": user_info.get("real_name", ""),
                        "email": user_info.get("profile", {}).get("email", ""),
                        "is_bot": user_info.get("is_bot", False)
                    }
                    
                    self.memory_manager.create_or_update_user(slack_user_info)
                    logger.info(f"✅ [BigQuery] Usuario creado/actualizado exitosamente: {user_id}")
                    
                except Exception as e:
                    logger.error(f"❌ [BigQuery] Error creando/actualizando usuario {user_id}: {str(e)}")
            else:
                logger.warning(f"⚠️ MemoryManager no disponible - usuario {user_id} no se guardará")
            
            # Obtener o crear conversación en BigQuery
            conversation_id = None
            if self.memory_manager:
                try:
                    user_obj = self.memory_manager.get_user_by_slack_id(user_id)
                    if user_obj:
                        conversation = self.memory_manager.get_or_create_conversation(
                            user_obj["user_id"], f"Slack DM: {channel_id}"
                        )
                        conversation_id = conversation.conversation_id if conversation else None
                        logger.info(f"✅ [BigQuery] Conversación obtenida/creada: {conversation_id}")
                    else:
                        logger.warning(f"⚠️ [BigQuery] Usuario no encontrado en BD: {user_id}")
                except Exception as e:
                    logger.error(f"❌ [BigQuery] Error obteniendo/creando conversación para {user_id}: {str(e)}")
            
            # Reaccionar con ojitos para indicar que se recibió el mensaje
            try:
                self.app.client.reactions_add(
                    channel=channel_id,
                    timestamp=timestamp,
                    name="eyes"
                )
                logger.info("👀 Reacción de ojitos agregada")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo agregar reacción de ojitos: {str(e)}")
            
            if not text:
                logger.info("📝 Mensaje vacío, ignorando")
                return
            
            # Procesar con el agente
            if self.agent:
                logger.info("🤖 Procesando con agente Claude...")
                
                # VALIDACIÓN DE SEGURIDAD ANTES DE PROCESAR
                logger.info("🔒 Iniciando validación de seguridad...")
                security_result = security_validator.validate_query(text)
                
                if not security_result.get("is_safe", True):
                    logger.warning(f"🚨 Consulta bloqueada por seguridad: {security_result.get('message', 'Consulta no segura')}")
                    try:
                        self.send_split_message(say, "❌ Lo siento, no puedo procesar esta consulta por razones de seguridad.", channel_id, timestamp)
                        # Cambiar reacción a X roja por bloqueo de seguridad
                        self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                        self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                        logger.info("❌ Reacción cambiada a X roja por bloqueo de seguridad")
                    except Exception as e:
                        logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
                    return
                
                logger.info(f"✅ Validación de seguridad exitosa: {security_result.get('message', 'Consulta segura')}")
                
                # Procesar con el agente
                context = {
                    "text": text,
                    "user": user_id,
                    "channel": channel_id,
                    "event_type": "direct_message"
                }
                response = self.agent.process_request(context)
                logger.info(f"✅ Respuesta del agente: {response}")
                
                # Guardar mensaje del usuario y respuesta del bot en BigQuery
                if self.memory_manager and conversation_id:
                    try:
                        # Guardar mensaje del usuario
                        user_obj = self.memory_manager.get_user_by_slack_id(user_id)
                        if user_obj:
                            self.memory_manager.save_message(
                                conversation_id, user_obj["user_id"], text, "user"
                            )
                            logger.info(f"✅ [BigQuery] Mensaje del usuario guardado - Conv: {conversation_id}")
                            
                            # Guardar respuesta del bot con métricas de API
                            bot_response = response.get("text", "Error procesando solicitud") if response else "Error procesando solicitud"
                            
                            # Extraer métricas de API si están disponibles
                            api_metrics = response.get("api_metrics", {}) if response else {}
                            tokens_used = api_metrics.get("tokens_used")
                            model_used = api_metrics.get("model_used")
                            response_time_ms = api_metrics.get("response_time_ms")
                            
                            # Debug: Log de las métricas extraídas
                            logger.info(f"🔍 [DEBUG] API Metrics extraídas: tokens_used={tokens_used}, model_used={model_used}, response_time_ms={response_time_ms}")
                            logger.info(f"🔍 [DEBUG] Response completo: {response}")
                            
                            self.memory_manager.save_message(
                                conversation_id, 
                                user_obj["user_id"], 
                                bot_response, 
                                "assistant",
                                tokens_used=tokens_used,
                                model_used=model_used,
                                response_time_ms=response_time_ms
                            )
                            logger.info(f"✅ [BigQuery] Respuesta del bot guardada - Conv: {conversation_id}")
                            
                            # Guardar métricas del agente en la tabla agentes_slack
                            try:
                                user_real_name = user_info.get("real_name", "") if user_info else ""
                                if user_real_name and tokens_used is not None and response_time_ms is not None:
                                    self.memory_manager.save_agent_metrics(
                                        slack_user_id=user_id,
                                        user_name=user_real_name,
                                        user_input=text,
                                        response_time_ms=response_time_ms,
                                        tokens_used=tokens_used
                                    )
                                    logger.info(f"✅ [BigQuery] Métricas del agente guardadas en agentes_slack para usuario: {user_id}")
                                else:
                                    logger.warning(f"⚠️ [BigQuery] Datos insuficientes para guardar métricas del agente: user_real_name={user_real_name}, tokens_used={tokens_used}, response_time_ms={response_time_ms}")
                            except Exception as metrics_error:
                                logger.error(f"❌ [BigQuery] Error guardando métricas del agente: {str(metrics_error)}")
                        else:
                            logger.warning(f"⚠️ [BigQuery] Usuario no encontrado para guardar mensajes: {user_id}")
                    except Exception as e:
                        logger.error(f"❌ [BigQuery] Error guardando mensajes - Conv: {conversation_id}: {str(e)}")
                elif self.memory_manager and not conversation_id:
                    logger.warning(f"⚠️ [BigQuery] Conversación no disponible - mensajes no guardados para usuario {user_id}")
                elif not self.memory_manager:
                    logger.warning(f"⚠️ MemoryManager no disponible - mensajes no se guardarán para usuario {user_id}")
                
                try:
                    if response:
                        self.send_split_message(say, response.get("text", "Error procesando solicitud"), channel_id, timestamp)
                        # Cambiar reacción a check verde por respuesta exitosa
                        self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                        self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="white_check_mark")
                        logger.info("✅ Reacción cambiada a check verde")
                    else:
                        self.send_split_message(say, "Error procesando solicitud", channel_id, timestamp)
                        # Cambiar reacción a X roja por error
                        self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                        self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                        logger.info("❌ Reacción cambiada a X roja")
                except Exception as e:
                    logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
            else:
                logger.warning("⚠️ Agente no disponible")
                try:
                    self.send_split_message(say, "El agente no está disponible en este momento.", channel_id, timestamp)
                    # Cambiar reacción a X roja por error
                    self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                    self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                    logger.info("❌ Reacción cambiada a X roja")
                except Exception as e:
                    logger.warning(f"⚠️ Error cambiando reacción: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ Error en handle_direct_message: {str(e)}", exc_info=True)
            try:
                self.send_split_message(say, "Ocurrió un error procesando tu mensaje.",
                                      channel_id if 'channel_id' in locals() else None,
                                      timestamp if 'timestamp' in locals() else None)
                # Cambiar reacción a X roja por error
                if 'channel_id' in locals() and 'timestamp' in locals():
                    self.app.client.reactions_remove(channel=channel_id, timestamp=timestamp, name="eyes")
                    self.app.client.reactions_add(channel=channel_id, timestamp=timestamp, name="x")
                    logger.info("❌ Reacción cambiada a X roja por excepción")
            except Exception as reaction_error:
                logger.warning(f"⚠️ Error cambiando reacción en excepción: {str(reaction_error)}")
    
    def handle_code_generation(self, command, say):
        """Maneja solicitudes de generación de código."""
        try:
            user_id = command.get("user_id")
            text = command.get("text", "")
            
            if not text:
                self.send_split_message(say, "Por favor proporciona los requisitos para generar código.")
                return
            
            # VALIDACIÓN DE SEGURIDAD ANTES DE PROCESAR
            logger.info("🔒 Iniciando validación de seguridad para generación de código...")
            security_result = security_validator.validate_query(text)
            
            if not security_result.get("is_safe", True):
                logger.warning(f"🚨 Solicitud de código bloqueada por seguridad: {security_result.get('message', 'Consulta no segura')}")
                self.send_split_message(say, "❌ Lo siento, no puedo procesar esta solicitud de código por razones de seguridad.")
                return
            
            logger.info(f"✅ Validación de seguridad exitosa para código: {security_result.get('message', 'Consulta segura')}")
            
            # Procesar con el agente
            if self.agent:
                context = {
                    "text": text,
                    "user": user_id,
                    "language": "python",  # default
                    "requirements": text
                }
                response = self.agent.generate_code(context)
                if response:
                    self.send_split_message(say, response.get("text", "Error generando código"))
                else:
                    self.send_split_message(say, "Error generando código")
            else:
                self.send_split_message(say, "El servicio de generación de código no está disponible.")
                
        except Exception as e:
            logger.error(f"Error en handle_code_generation: {str(e)}")
            self.send_split_message(say, "Ocurrió un error generando el código.")
    
    def show_help(self, say):
        """Muestra información de ayuda."""
        help_text = """
🤖 *Claude Programming Agent - Ayuda*

*Comandos disponibles:*
• `/code [requisitos]` - Generar código
• `/help` - Mostrar esta ayuda

*Uso directo:*
• Menciona al bot (@claude) en cualquier canal
• Envía mensajes directos para consultas privadas

*Ejemplos:*
• `/code crear una función que calcule fibonacci`
• `@claude explica este error de Python`
        """
        self.send_split_message(say, help_text)
    
    def start(self, host="0.0.0.0", port=8080):
        """Inicia el servidor HTTP."""
        logger.info(f"🚀 Iniciando servidor HTTP en {host}:{port}")
        self.flask_app.run(host=host, port=port, debug=False)