import os
import logging
from typing import Dict, Any, Optional
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web import WebClient
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utilidades
sys.path.append(str(Path(__file__).parent.parent))

from utils.error_handler import (
    retry_on_failure, 
    safe_execute, 
    log_error_with_context,
    create_error_response,
    APIError,
    ValidationError,
    ProcessingError
)
from utils.logging_config import log_user_operation, log_api_call, log_metrics

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackEventHandler:
    """
    Manejador de eventos de Slack que integra con el Claude Programming Agent.
    """
    
    def __init__(self, agent):
        """Inicializa el manejador de eventos de Slack."""
        self.agent = agent
        
        # Obtener configuración de variables de entorno
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        if not all([self.bot_token, self.app_token, self.signing_secret]):
            raise ValueError("Faltan variables de configuración de Slack en .env")
        
        # Inicializar la aplicación Slack Bolt
        self.app = App(
            token=self.bot_token,
            signing_secret=self.signing_secret
        )
        
        # Configurar manejadores de eventos
        self.setup_event_handlers()
        
        logger.info("Manejador de eventos de Slack inicializado correctamente")
    
    def setup_event_handlers(self):
        """Configura los manejadores de eventos de Slack."""
        
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            """Maneja menciones del bot."""
            self.handle_mention(event, say)
        
        @self.app.event("message")
        def handle_message(event, say):
            """Maneja mensajes directos."""
            self.handle_direct_message(event, say)
        
        @self.app.command("/code")
        def handle_code_command(ack, say, command):
            """Maneja el comando /code."""
            ack()
            self.handle_code_generation(command, say)
        
        @self.app.command("/analyze")
        def handle_analyze_command(ack, say, command):
            """Maneja el comando /analyze."""
            ack()
            self.handle_code_analysis(command, say)
        
        @self.app.command("/test")
        def handle_test_command(ack, say, command):
            """Maneja el comando /test."""
            ack()
            self.handle_code_testing(command, say)
        
        @self.app.command("/debug")
        def handle_debug_command(ack, say, command):
            """Maneja el comando /debug."""
            ack()
            self.handle_debugging(command, say)
        
        @self.app.command("/help")
        def handle_help_command(ack, say):
            """Maneja el comando /help."""
            ack()
            self.show_help(say)
    
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="handle_mention", log_errors=True)
    def handle_mention(self, event: Dict[str, Any], say):
        """Maneja menciones del bot en canales."""
        try:
            user = event.get("user", "")
            text = event.get("text", "")
            channel = event.get("channel", "")
            
            # Validar entrada
            if not text.strip():
                raise ValidationError("Mención vacía recibida")
            
            # Log de la operación
            log_user_operation("handle_mention", user, {
                "text_length": len(text),
                "channel": channel
            })
            
            # Remover la mención del bot del texto
            bot_id = self.app.client.auth_test()["user_id"]
            clean_text = text.replace(f"<@{bot_id}>", "").strip()
            
            logger.info(f"Mención recibida de {user} en canal {channel}: {clean_text}")
            
            import time
            start_time = time.time()
            
            # Procesar el mensaje
            response = self.process_programming_request(clean_text, user)
            
            duration = time.time() - start_time
            log_metrics("mention_processing_duration", duration, {"user": user, "channel": channel})
            
            # Enviar respuesta
            say({
                "text": response["text"],
                "blocks": response.get("blocks", [])
            })
            
            log_user_operation("handle_mention", user, success=True)
            
        except ValidationError as e:
            error_msg = create_error_response(str(e), "validation", user)
            say(error_msg)
            log_user_operation("handle_mention", user, success=False)
            
        except APIError as e:
            error_msg = create_error_response(str(e), "api", user)
            say(error_msg)
            log_user_operation("handle_mention", user, success=False)
            
        except Exception as e:
            log_error_with_context(e, event, "handle_mention", user)
            error_msg = create_error_response(
                "Error interno del sistema", 
                "system", 
                user
            )
            say(error_msg)
            log_user_operation("handle_mention", user, success=False)
    
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="handle_direct_message", log_errors=True)
    def handle_direct_message(self, event: Dict[str, Any], say):
        """Maneja mensajes directos al bot."""
        try:
            user_id = event.get("user", "unknown")
            text = event.get("text", "")
            channel = event.get("channel", "")
            channel_type = event.get("channel_type", "")
            
            # Solo procesar mensajes directos, no mensajes de canal
            if channel_type != "im":
                return
            
            # Log de la operación
            log_user_operation("handle_direct_message", user_id, {
                "text_length": len(text),
                "channel": channel
            })
            
            # Validar entrada
            if not text.strip():
                raise ValidationError("Mensaje vacío recibido")
            
            logger.info(f"Mensaje directo recibido de {user_id}: {text}")
            
            import time
            start_time = time.time()
            
            # Procesar el mensaje
            response = self.process_programming_request(text, user_id)
            
            duration = time.time() - start_time
            log_metrics("direct_message_processing_duration", duration, {"user_id": user_id})
            
            # Enviar respuesta
            say({
                "text": response["text"],
                "blocks": response.get("blocks", [])
            })
            
            log_user_operation("handle_direct_message", user_id, success=True)
            
        except ValidationError as e:
            error_msg = create_error_response(str(e), "validation", user_id)
            say(error_msg)
            log_user_operation("handle_direct_message", user_id, success=False)
            
        except APIError as e:
            error_msg = create_error_response(str(e), "api", user_id)
            say(error_msg)
            log_user_operation("handle_direct_message", user_id, success=False)
            
        except Exception as e:
            log_error_with_context(e, event, "handle_direct_message", user_id)
            error_msg = create_error_response(
                "Error interno del sistema", 
                "system", 
                user_id
            )
            say(error_msg)
            log_user_operation("handle_direct_message", user_id, success=False)
    
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="handle_code_generation", log_errors=True)
    def handle_code_generation(self, command: Dict[str, Any], say):
        """Maneja el comando /code para generación de código."""
        try:
            user = command.get("user_id", "")
            text = command.get("text", "")
            
            # Log de la operación
            log_user_operation("handle_code_generation", user, {
                "text_length": len(text)
            })
            
            logger.info(f"Comando /code recibido de {user}: {text}")
            
            # Parsear el comando
            parts = text.split("\n", 1)
            if len(parts) < 2:
                raise ValidationError("Formato de comando incorrecto. Proporciona el lenguaje y los requisitos.")
            
            language = parts[0].strip()
            requirements = parts[1].strip()
            
            if not language or not requirements:
                raise ValidationError("Lenguaje y requisitos son obligatorios")
            
            # Generar respuesta inicial
            say(f"Generando código en *{language}* según tus requisitos...")
            
            import time
            start_time = time.time()
            
            # Usar el agente para generar código
            context = {
                "language": language,
                "requirements": requirements,
                "user": user
            }
            
            response = self.agent.generate_code(context)
            
            duration = time.time() - start_time
            log_metrics("code_generation_duration", duration, {"user": user, "language": language})
            
            # Formatear y enviar respuesta
            formatted_response = self.format_code_response(response, language)
            say(formatted_response)
            
            log_user_operation("handle_code_generation", user, success=True)
            
        except ValidationError as e:
            error_msg = create_error_response(str(e), "validation", user)
            say(error_msg)
            log_user_operation("handle_code_generation", user, success=False)
            
        except APIError as e:
            error_msg = create_error_response(str(e), "api", user)
            say(error_msg)
            log_user_operation("handle_code_generation", user, success=False)
            
        except Exception as e:
            log_error_with_context(e, command, "handle_code_generation", user)
            error_msg = create_error_response(
                "Error generando código", 
                "system", 
                user
            )
            say(error_msg)
            log_user_operation("handle_code_generation", user, success=False)
    
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="handle_code_analysis", log_errors=True)
    def handle_code_analysis(self, command: Dict[str, Any], say):
        """Maneja el comando /analyze para análisis de código."""
        try:
            user = command.get("user_id", "")
            text = command.get("text", "")
            
            # Log de la operación
            log_user_operation("handle_code_analysis", user, {
                "text_length": len(text)
            })
            
            logger.info(f"Comando /analyze recibido de {user}")
            
            # Parsear el comando
            parts = text.split("\n", 1)
            if len(parts) < 2:
                raise ValidationError("Formato de comando incorrecto. Proporciona el lenguaje y el código a analizar.")
            
            language = parts[0].strip()
            code = parts[1].strip()
            
            if not language or not code:
                raise ValidationError("Lenguaje y código son obligatorios")
            
            say(f"Analizando código en *{language}*...")
            
            import time
            start_time = time.time()
            
            # Usar el agente para analizar código
            context = {
                "language": language,
                "code": code,
                "user": user
            }
            
            response = self.agent.analyze_code(context)
            
            duration = time.time() - start_time
            log_metrics("code_analysis_duration", duration, {"user": user, "language": language})
            
            # Formatear y enviar respuesta
            formatted_response = self.format_analysis_response(response)
            say(formatted_response)
            
            log_user_operation("handle_code_analysis", user, success=True)
            
        except ValidationError as e:
            error_msg = create_error_response(str(e), "validation", user)
            say(error_msg)
            log_user_operation("handle_code_analysis", user, success=False)
            
        except APIError as e:
            error_msg = create_error_response(str(e), "api", user)
            say(error_msg)
            log_user_operation("handle_code_analysis", user, success=False)
            
        except Exception as e:
            log_error_with_context(e, command, "handle_code_analysis", user)
            error_msg = create_error_response(
                "Error analizando código", 
                "system", 
                user
            )
            say(error_msg)
            log_user_operation("handle_code_analysis", user, success=False)
    
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="handle_code_testing", log_errors=True)
    def handle_code_testing(self, command: Dict[str, Any], say):
        """Maneja el comando /test para pruebas de código."""
        try:
            user = command.get("user_id", "")
            text = command.get("text", "")
            
            # Log de la operación
            log_user_operation("handle_code_testing", user, {
                "text_length": len(text)
            })
            
            logger.info(f"Comando /test recibido de {user}")
            
            # Parsear el comando
            parts = text.split("\n", 1)
            if len(parts) < 2:
                raise ValidationError("Formato de comando incorrecto. Proporciona el lenguaje y el código a probar.")
            
            language = parts[0].strip()
            code = parts[1].strip()
            
            if not language or not code:
                raise ValidationError("Lenguaje y código son obligatorios")
            
            say(f"Ejecutando pruebas para código en *{language}*...")
            
            import time
            start_time = time.time()
            
            # Usar el agente para ejecutar pruebas
            context = {
                "language": language,
                "code": code,
                "user": user
            }
            
            response = self.agent.test_code(context)
            
            duration = time.time() - start_time
            log_metrics("code_testing_duration", duration, {"user": user, "language": language})
            
            # Formatear y enviar respuesta
            formatted_response = self.format_test_response(response)
            say(formatted_response)
            
            log_user_operation("handle_code_testing", user, success=True)
            
        except ValidationError as e:
            error_msg = create_error_response(str(e), "validation", user)
            say(error_msg)
            log_user_operation("handle_code_testing", user, success=False)
            
        except APIError as e:
            error_msg = create_error_response(str(e), "api", user)
            say(error_msg)
            log_user_operation("handle_code_testing", user, success=False)
            
        except Exception as e:
            log_error_with_context(e, command, "handle_code_testing", user)
            error_msg = create_error_response(
                "Error ejecutando pruebas", 
                "system", 
                user
            )
            say(error_msg)
            log_user_operation("handle_code_testing", user, success=False)
    
    @retry_on_failure(max_attempts=3, delay=2.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="handle_debugging", log_errors=True)
    def handle_debugging(self, command: Dict[str, Any], say):
        """Maneja el comando /debug para depuración de código."""
        try:
            user = command.get("user_id", "")
            text = command.get("text", "")
            
            # Log de la operación
            log_user_operation("handle_debugging", user, {
                "text_length": len(text)
            })
            
            logger.info(f"Comando /debug recibido de {user}")
            
            # Parsear el comando
            parts = text.split("\n", 1)
            if len(parts) < 2:
                raise ValidationError("Formato de comando incorrecto. Proporciona el lenguaje y el código a depurar.")
            
            language = parts[0].strip()
            code = parts[1].strip()
            
            if not language or not code:
                raise ValidationError("Lenguaje y código son obligatorios")
            
            say(f"Depurando código en *{language}*...")
            
            import time
            start_time = time.time()
            
            # Usar el agente para depurar código
            context = {
                "language": language,
                "code": code,
                "user": user
            }
            
            response = self.agent.debug_code(context)
            
            duration = time.time() - start_time
            log_metrics("code_debugging_duration", duration, {"user": user, "language": language})
            
            # Formatear y enviar respuesta
            formatted_response = self.format_debug_response(response)
            say(formatted_response)
            
            log_user_operation("handle_debugging", user, success=True)
            
        except ValidationError as e:
            error_msg = create_error_response(str(e), "validation", user)
            say(error_msg)
            log_user_operation("handle_debugging", user, success=False)
            
        except APIError as e:
            error_msg = create_error_response(str(e), "api", user)
            say(error_msg)
            log_user_operation("handle_debugging", user, success=False)
            
        except Exception as e:
            log_error_with_context(e, command, "handle_debugging", user)
            error_msg = create_error_response(
                "Error depurando código", 
                "system", 
                user
            )
            say(error_msg)
            log_user_operation("handle_debugging", user, success=False)

    @safe_execute(operation="process_programming_request", log_errors=True)
    def process_programming_request(self, text: str, user: str) -> Dict[str, Any]:
        """Procesa una solicitud de programación general."""
        try:
            # Log de la operación
            log_user_operation("process_programming_request", user, {
                "text_length": len(text)
            })
            
            # Validar entrada
            if not text.strip():
                raise ValidationError("Solicitud vacía recibida")
            
            # Por ahora, devolver un mensaje de ayuda
            return {
                "text": "Hola! Soy Claude Programming Agent. Usa los comandos slash para interactuar conmigo.\nUsa `/help` para ver todos los comandos disponibles.",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "👋 *¡Hola! Soy Claude Programming Agent*\n\nEstoy aquí para ayudarte con tareas de programación. Puedo:\n• Generar código\n• Analizar código\n• Ejecutar pruebas\n• Depurar errores\n\n💡 *Usa los comandos slash para interactuar conmigo:*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*/code* - Generar código"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*/analyze* - Analizar código"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*/test* - Ejecutar pruebas"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*/debug* - Depurar código"
                            }
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "💡 Usa `/help` para ver todos los comandos disponibles"
                            }
                        ]
                    }
                ]
            }
            
        except ValidationError as e:
            return create_error_response(str(e), "validation", user)
        except Exception as e:
            log_error_with_context(e, {"text": text}, "process_programming_request", user)
            return create_error_response(
                "Error procesando solicitud", 
                "system", 
                user
            )

    def format_code_response(self, response: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Formatea la respuesta de generación de código."""
        return {
            "text": response.get("text", "Código generado"),
            "blocks": response.get("blocks", [])
        }
    
    def format_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea la respuesta de análisis de código."""
        return {
            "text": response.get("text", "Análisis completado"),
            "blocks": response.get("blocks", [])
        }
    
    def format_test_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea la respuesta de pruebas."""
        return {
            "text": response.get("text", "Pruebas ejecutadas"),
            "blocks": response.get("blocks", [])
        }
    
    def format_debug_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea la respuesta de depuración."""
        return {
            "text": response.get("text", "Depuración completada"),
            "blocks": response.get("blocks", [])
        }
    
    def start(self):
        """Inicia el manejador de eventos."""
        logger.info("🚀 Iniciando manejador de eventos de Slack...")
        handler = SocketModeHandler(self.app, self.app_token)
        handler.start()