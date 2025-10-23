import os
import logging
from typing import Dict, Any, Optional
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.web import WebClient
from datetime import datetime, timezone
import json

# Importar el gestor de memoria persistente
from ..utils.memory_manager import MemoryManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackBot:
    """
    Bot de Slack que integra con Google ADK para proporcionar
    asistencia en programación usando Claude.
    """
    
    def __init__(self):
        """Inicializa el bot de Slack."""
        print("🔧 Inicializando bot de Slack...")
        
        # Obtener configuración de variables de entorno
        print("🔍 Verificando configuración de Slack...")
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        if not all([self.bot_token, self.app_token, self.signing_secret]):
            error_msg = "Faltan variables de configuración de Slack en .env"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        print("✅ Configuración de Slack validada")
        
        # Inicializar la aplicación Slack Bolt
        print("🔄 Inicializando aplicación Slack Bolt...")
        try:
            self.app = App(
                token=self.bot_token,
                signing_secret=self.signing_secret
            )
            print("✅ Aplicación Slack Bolt inicializada")
        except Exception as e:
            print(f"❌ Error inicializando Slack Bolt: {str(e)}")
            logger.error(f"Error inicializando Slack Bolt: {str(e)}")
            raise
        
        # Inicializar el gestor de memoria persistente
        print("🗄️ Inicializando gestor de memoria persistente...")
        try:
            self.memory_manager = MemoryManager()
            print("✅ MemoryManager inicializado correctamente")
            logger.info("MemoryManager inicializado correctamente")
        except Exception as e:
            print(f"⚠️ Error inicializando MemoryManager: {str(e)}")
            print("⚠️ Continuando sin memoria persistente...")
            logger.error(f"Error inicializando MemoryManager: {str(e)}")
            self.memory_manager = None
        
        # Configurar manejadores de eventos
        print("🔗 Configurando manejadores de eventos...")
        self.setup_event_handlers()
        print("✅ Manejadores de eventos configurados")
        
        print("✅ Bot de Slack inicializado correctamente")
        logger.info("Bot de Slack inicializado correctamente")
    
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
    
    def handle_mention(self, event: Dict[str, Any], say):
        """Maneja menciones del bot en canales."""
        user = event.get("user", "")
        text = event.get("text", "")
        channel = event.get("channel", "")
        ts = event.get("ts", "")
        
        # Remover la mención del bot del texto
        bot_id = self.app.client.auth_test()["user_id"]
        clean_text = text.replace(f"<@{bot_id}>", "").strip()
        
        logger.info(f"Mención recibida de {user} en canal {channel}: {clean_text}")
        
        # Obtener información del usuario
        user_info = self.get_user_info(user)
        
        # Crear o actualizar usuario en memoria persistente
        if self.memory_manager and user_info:
            try:
                # Preparar información del usuario en el formato esperado
                slack_user_info = {
                    'id': user,
                    'real_name': user_info.get("real_name", ""),
                    'profile': {
                        'display_name': user_info.get("display_name", ""),
                        'email': user_info.get("email", ""),
                        'image_192': user_info.get("image_192", "")
                    },
                    'team_id': user_info.get("team_id", ""),
                    'tz': user_info.get("tz", ""),
                    'is_admin': user_info.get("is_admin", False),
                    'is_bot': user_info.get("is_bot", False)
                }
                self.memory_manager.create_or_update_user(slack_user_info)
                logger.info(f"✅ Usuario {user} creado/actualizado en BigQuery")
            except Exception as e:
                logger.error(f"❌ Error creando/actualizando usuario {user}: {e}")
        
        # Obtener o crear conversación
        conversation_id = None
        if self.memory_manager:
            try:
                # Primero necesitamos obtener el user_id del usuario creado/actualizado
                user_obj = self.memory_manager.get_user_by_slack_id(user)
                if user_obj:
                    conversation = self.memory_manager.get_or_create_conversation(
                        user_id=user_obj['user_id'],
                        slack_channel_id=channel
                    )
                    if conversation:
                        conversation_id = conversation.conversation_id
                        logger.info(f"✅ Conversación {conversation_id} obtenida/creada para usuario {user}")
                    else:
                        logger.error(f"❌ No se pudo crear conversación para usuario {user}")
                else:
                    logger.error(f"❌ No se pudo obtener usuario {user} de BigQuery")
            except Exception as e:
                logger.error(f"❌ Error obteniendo/creando conversación para usuario {user}: {e}")
        
        # Procesar el mensaje
        response = self.process_programming_request(clean_text, user, conversation_id)
        
        # Guardar mensaje del usuario y respuesta en memoria
        if self.memory_manager and conversation_id:
            try:
                # Obtener el user_id correcto
                user_obj = self.memory_manager.get_user_by_slack_id(user)
                if user_obj:
                    user_id = user_obj['user_id']
                    
                    # Guardar mensaje del usuario
                    self.memory_manager.save_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        message_type="user",
                        content=clean_text,
                        slack_message_ts=ts
                    )
                    logger.info(f"✅ Mensaje del usuario {user} guardado en BigQuery (conversación: {conversation_id})")
                    
                    # Guardar respuesta del bot
                    self.memory_manager.save_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        message_type="assistant",
                        content=response["text"],
                        metadata={"blocks": response.get("blocks", [])}
                    )
                    logger.info(f"✅ Respuesta del bot guardada en BigQuery (conversación: {conversation_id})")
                else:
                    logger.error(f"❌ No se pudo obtener usuario {user} para guardar mensajes")
            except Exception as e:
                logger.error(f"❌ Error guardando mensajes para usuario {user}: {e}")
        elif self.memory_manager and not conversation_id:
            logger.error(f"❌ No se pudo guardar mensajes: conversación no disponible para usuario {user}")
        elif not self.memory_manager:
            logger.warning(f"⚠️ MemoryManager no disponible - mensajes no se guardarán para usuario {user}")
        
        # Enviar respuesta
        say({
            "text": response["text"],
            "blocks": response.get("blocks", [])
        })
    
    def handle_direct_message(self, event: Dict[str, Any], say):
        """Maneja mensajes directos al bot."""
        user = event.get("user", "")
        text = event.get("text", "")
        channel = event.get("channel", "")
        channel_type = event.get("channel_type", "")
        ts = event.get("ts", "")
        
        # Solo procesar mensajes directos, no mensajes de canal
        if channel_type != "im":
            return
        
        logger.info(f"Mensaje directo recibido de {user}: {text}")
        
        # Obtener información del usuario
        user_info = self.get_user_info(user)
        
        # Crear o actualizar usuario en memoria persistente
        if self.memory_manager and user_info:
            try:
                slack_user_info = {
                    'id': user,  # Cambiar 'slack_id' por 'id'
                    'real_name': user_info.get("real_name", ""),
                    'display_name': user_info.get("display_name", ""),
                    'email': user_info.get("email", ""),
                    'timezone': user_info.get("tz", ""),
                    'is_bot': user_info.get("is_bot", False)
                }
                self.memory_manager.create_or_update_user(slack_user_info)
                logger.info(f"✅ Usuario {user} creado/actualizado en BigQuery (DM)")
            except Exception as e:
                logger.error(f"❌ Error creando/actualizando usuario {user} (DM): {e}")
        
        # Obtener o crear conversación
        conversation_id = None
        if self.memory_manager:
            try:
                # Primero necesitamos obtener el user_id del usuario creado/actualizado
                user_obj = self.memory_manager.get_user_by_slack_id(user)
                if user_obj:
                    conversation = self.memory_manager.get_or_create_conversation(
                        user_id=user_obj['user_id'],
                        slack_channel_id=channel
                    )
                    if conversation:
                        conversation_id = conversation.conversation_id
                        logger.info(f"✅ Conversación {conversation_id} obtenida/creada para usuario {user} (DM)")
                    else:
                        logger.error(f"❌ No se pudo crear conversación para usuario {user} (DM)")
                else:
                    logger.error(f"❌ No se pudo obtener usuario {user} de BigQuery (DM)")
            except Exception as e:
                logger.error(f"❌ Error obteniendo/creando conversación para usuario {user} (DM): {e}")
        
        # Procesar el mensaje
        response = self.process_programming_request(text, user, conversation_id)
        
        # Guardar mensaje del usuario y respuesta en memoria
        if self.memory_manager and conversation_id:
            try:
                # Obtener el user_id correcto
                user_obj = self.memory_manager.get_user_by_slack_id(user)
                if user_obj:
                    user_id = user_obj['user_id']
                    
                    # Guardar mensaje del usuario
                    self.memory_manager.save_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        message_type="user",
                        content=text,
                        slack_message_ts=ts
                    )
                    logger.info(f"✅ Mensaje del usuario {user} guardado en BigQuery (DM)")
                    
                    # Guardar respuesta del bot
                    self.memory_manager.save_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        message_type="assistant",
                        content=response["text"],
                        metadata={"blocks": response.get("blocks", [])}
                    )
                    logger.info(f"✅ Respuesta del bot guardada en BigQuery para usuario {user} (DM)")
                else:
                    logger.error(f"❌ No se pudo obtener usuario {user} para guardar mensajes (DM)")
            except Exception as e:
                logger.error(f"❌ Error guardando mensajes para usuario {user} (DM): {e}")
        elif not self.memory_manager:
            logger.warning("⚠️ MemoryManager no inicializado - mensajes no guardados (DM)")
        elif not conversation_id:
            logger.warning(f"⚠️ No hay conversation_id para usuario {user} - mensajes no guardados (DM)")
        
        # Enviar respuesta
        say({
            "text": response["text"],
            "blocks": response.get("blocks", [])
        })
    
    def handle_code_generation(self, command: Dict[str, Any], say):
        """Maneja el comando /code para generación de código."""
        user = command.get("user_id", "")
        text = command.get("text", "")
        channel = command.get("channel_id", "")
        
        logger.info(f"Comando /code recibido de {user}: {text}")
        
        # Parsear el comando
        parts = text.split("\n", 1)
        if len(parts) < 2:
            say("Por favor proporciona el lenguaje y los requisitos. Ejemplo:\n`/code python\nCrea una función que calcule el factorial de un número`")
            return
        
        language = parts[0].strip()
        requirements = parts[1].strip()
        
        # Generar respuesta inicial
        say(f"Generando código en *{language}* según tus requisitos...")
        
        try:
            # Aquí se integraría con el agente ADK para generar código
            response = self.generate_code_with_adk(requirements, language, user)
            
            # Formatear y enviar respuesta
            formatted_response = self.format_code_response(response, language)
            say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error generando código: {str(e)}")
            say(f"Lo siento, hubo un error generando el código: {str(e)}")
    
    def handle_code_analysis(self, command: Dict[str, Any], say):
        """Maneja el comando /analyze para análisis de código."""
        user = command.get("user_id", "")
        text = command.get("text", "")
        
        logger.info(f"Comando /analyze recibido de {user}")
        
        # Parsear el comando
        parts = text.split("\n", 1)
        if len(parts) < 2:
            say("Por favor proporciona el lenguaje y el código a analizar. Ejemplo:\n`/analyze python\ndef funcion():\n    pass`")
            return
        
        language = parts[0].strip()
        code = parts[1].strip()
        
        say(f"Analizando código en *{language}*...")
        
        try:
            # Aquí se integraría con el agente ADK para analizar código
            response = self.analyze_code_with_adk(code, language, user)
            
            # Formatear y enviar respuesta
            formatted_response = self.format_analysis_response(response)
            say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error analizando código: {str(e)}")
            say(f"Lo siento, hubo un error analizando el código: {str(e)}")
    
    def handle_code_testing(self, command: Dict[str, Any], say):
        """Maneja el comando /test para pruebas de código."""
        user = command.get("user_id", "")
        text = command.get("text", "")
        
        logger.info(f"Comando /test recibido de {user}")
        
        # Parsear el comando
        parts = text.split("\n", 1)
        if len(parts) < 2:
            say("Por favor proporciona el lenguaje y el código a probar. Ejemplo:\n`/test python\ndef funcion():\n    return 42`")
            return
        
        language = parts[0].strip()
        code = parts[1].strip()
        
        say(f"Ejecutando pruebas para código en *{language}*...")
        
        try:
            # Aquí se integraría con el agente ADK para ejecutar pruebas
            response = self.test_code_with_adk(code, language, user)
            
            # Formatear y enviar respuesta
            formatted_response = self.format_test_response(response)
            say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error ejecutando pruebas: {str(e)}")
            say(f"Lo siento, hubo un error ejecutando las pruebas: {str(e)}")
    
    def handle_debugging(self, command: Dict[str, Any], say):
        """Maneja el comando /debug para debugging de código."""
        user = command.get("user_id", "")
        text = command.get("text", "")
        
        logger.info(f"Comando /debug recibido de {user}")
        
        # Parsear el comando
        parts = text.split("\n", 1)
        if len(parts) < 2:
            say("Por favor proporciona el lenguaje y el código con error. Ejemplo:\n`/debug python\ndef funcion():\n    raise Exception('error')`")
            return
        
        language = parts[0].strip()
        code = parts[1].strip()
        
        say(f"Depurando código en *{language}*...")
        
        try:
            # Aquí se integraría con el agente ADK para debugging
            response = self.debug_code_with_adk(code, language, user)
            
            # Formatear y enviar respuesta
            formatted_response = self.format_debug_response(response)
            say(formatted_response)
            
        except Exception as e:
            logger.error(f"Error en depuración: {str(e)}")
            say(f"Lo siento, hubo un error en la depuración: {str(e)}")
    
    def show_help(self, say):
        """Muestra la ayuda del bot."""
        help_text = """
🤖 *Claude Code Assistant* - Tu experto en programación

*Comandos disponibles:*

• `/code <lenguaje>\n<requisitos>` - Genera código
• `/analyze <lenguaje>\n<código>` - Analiza código
• `/test <lenguaje>\n<código>` - Ejecuta pruebas
• `/debug <lenguaje>\n<código>` - Ayuda a depurar

*También puedes:*
• Mencionarme en canales: `@Claude Assistant genera código python para...`
• Enviarme mensajes directos

*Ejemplos:*
`/code python
Crea una función que calcule el factorial`

`/analyze python
def hello():\n    print("Hello")`

`/test python
def add(a, b):\n    return a + b`

`/debug python
def divide(a, b):\n    return a / b`
        """
        
        say(help_text)
    
    def process_programming_request(self, text: str, user: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Procesa una solicitud de programación general."""
        # Obtener contexto de conversaciones anteriores si está disponible
        context = ""
        if self.memory_manager and conversation_id:
            try:
                # Obtener mensajes recientes de la conversación
                recent_messages = self.memory_manager.get_conversation_messages(
                    conversation_id=conversation_id,
                    limit=10
                )
                
                if recent_messages:
                    context_parts = []
                    for msg in recent_messages[-5:]:  # Últimos 5 mensajes para contexto
                        role = "Usuario" if msg.message_type == "user" else "Asistente"
                        context_parts.append(f"{role}: {msg.content}")
                    context = "\\n".join(context_parts)
                
                # Obtener contexto adicional del usuario
                user_context = self.memory_manager.get_user_context(user)
                if user_context:
                    context += f"\\n\\nContexto del usuario: {user_context}"
                    
            except Exception as e:
                logger.error(f"Error obteniendo contexto: {str(e)}")
        
        # Construir respuesta con contexto
        response_text = f"Hola <@{user}>! Entendí tu solicitud: '{text}'. Estoy procesando tu solicitud de programación..."
        
        if context:
            response_text += "\\n\\n*Considerando el contexto de nuestra conversación anterior.*"
        
        return {
            "text": response_text,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Solicitud recibida de <@{user}>*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{text}```"
                    }
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
    
    def generate_code_with_adk(self, requirements: str, language: str, user: str) -> Dict[str, Any]:
        """Genera código usando el agente ADK."""
        # Esta función se integraría con el agente ADK real
        # Por ahora, retorna una respuesta simulada
        
        return {
            "code": f"# Código generado para {language}\\n# Requisitos: {requirements}\\n\\ndef generated_function():\\n    return 'Hello World'",
            "language": language,
            "explanation": "Este código fue generado según tus requisitos",
            "best_practices": ["Usa nombres descriptivos", "Agrega documentación"]
        }
    
    def analyze_code_with_adk(self, code: str, language: str, user: str) -> Dict[str, Any]:
        """Analiza código usando el agente ADK."""
        # Esta función se integraría con el agente ADK real
        
        return {
            "analysis": "Código analizado exitosamente",
            "metrics": {
                "lines": len(code.splitlines()),
                "complexity": "baja",
                "quality": "buena"
            },
            "suggestions": ["Considera agregar más comentarios", "Verifica el manejo de errores"]
        }
    
    def test_code_with_adk(self, code: str, language: str, user: str) -> Dict[str, Any]:
        """Ejecuta pruebas usando el agente ADK."""
        # Esta función se integraría con el agente ADK real
        
        return {
            "test_results": "Pruebas ejecutadas",
            "passed": 3,
            "failed": 0,
            "coverage": "85%"
        }
    
    def debug_code_with_adk(self, code: str, language: str, user: str) -> Dict[str, Any]:
        """Depura código usando el agente ADK."""
        # Esta función se integraría con el agente ADK real
        
        return {
            "debug_analysis": "Código depurado",
            "issues_found": 1,
            "suggestions": ["Revisa la línea 5", "Verifica el tipo de dato"]
        }
    
    def format_code_response(self, response: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Formatea la respuesta de generación de código."""
        return {
            "text": f"✅ Código generado en *{language}*:",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Código generado en {language}:*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{language}\\n{response['code']}\\n```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"💡 {response.get('explanation', 'Código generado exitosamente')}"
                        }
                    ]
                }
            ]
        }
    
    def format_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea la respuesta de análisis de código."""
        metrics = response.get("metrics", {})
        suggestions = response.get("suggestions", [])
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 Análisis de Código:*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Líneas:* {metrics.get('lines', 'N/A')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Complejidad:* {metrics.get('complexity', 'N/A')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Calidad:* {metrics.get('quality', 'N/A')}"
                    }
                ]
            }
        ]
        
        if suggestions:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💡 Sugerencias:*"
                }
            })
            for suggestion in suggestions:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• {suggestion}"
                    }
                })
        
        return {
            "text": "Análisis completado",
            "blocks": blocks
        }
    
    def format_test_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea la respuesta de pruebas."""
        passed = response.get("passed", 0)
        failed = response.get("failed", 0)
        total = passed + failed
        
        return {
            "text": "Pruebas ejecutadas",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🧪 Resultados de Pruebas:*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Total:* {total}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*✅ Pasadas:* {passed}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*❌ Fallidas:* {failed}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*📈 Cobertura:* {response.get('coverage', 'N/A')}"
                        }
                    ]
                }
            ]
        }
    
    def format_debug_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Formatea la respuesta de depuración."""
        issues = response.get("issues_found", 0)
        suggestions = response.get("suggestions", [])
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔍 Resultados de Depuración:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Problemas encontrados:* {issues}"
                }
            }
        ]
        
        if suggestions:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*💡 Sugerencias:*"
                }
            })
            for suggestion in suggestions:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• {suggestion}"
                    }
                })
        
        return {
            "text": "Depuración completada",
            "blocks": blocks
        }
    
    def start(self):
        """Inicia el bot en modo socket."""
        logger.info("Iniciando bot de Slack en modo Socket...")
        handler = SocketModeHandler(self.app, self.app_token)
        handler.start()

# Función auxiliar para enviar mensajes de Slack
def send_slack_message(message: str, channel: str) -> Dict[str, Any]:
    """
    Envía un mensaje a un canal de Slack.
    
    Args:
        message: Mensaje a enviar
        channel: Canal de Slack (ej: #general o @username)
    
    Returns:
        Dict con el resultado del envío
    """
    try:
        # Obtener el cliente de Slack
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not bot_token:
            return {"status": "error", "message": "No se encontró SLACK_BOT_TOKEN"}
        
        client = WebClient(token=bot_token)
        
        # Enviar mensaje
        response = client.chat_postMessage(
            channel=channel,
            text=message
        )
        
        return {
            "status": "success",
            "message": f"Mensaje enviado a {channel}",
            "timestamp": response.get("ts"),
            "channel": response.get("channel")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error enviando mensaje: {str(e)}"
        }

@tool
def get_slack_channels(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Obtiene la lista de canales de Slack disponibles.
    
    Args:
        tool_context: Contexto de la herramienta
    
    Returns:
        Dict con la lista de canales
    """
    try:
        bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not bot_token:
            return {"status": "error", "message": "No se encontró SLACK_BOT_TOKEN"}
        
        client = WebClient(token=bot_token)
        
        # Obtener canales
        response = client.conversations_list(types="public_channel,private_channel")
        
        channels = []
        for channel in response.get("channels", []):
            channels.append({
                "id": channel.get("id"),
                "name": channel.get("name"),
                "is_private": channel.get("is_private", False),
                "member_count": channel.get("num_members", 0)
            })
        
        return {
            "status": "success",
            "channels": channels,
            "total": len(channels)
        }
        
    except Exception as e:
        return {
             "status": "error",
             "message": f"Error obteniendo canales: {str(e)}"
         }

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada del usuario desde Slack."""
        try:
            client = WebClient(token=self.bot_token)
            response = client.users_info(user=user_id)
            
            if response.get("ok"):
                user_data = response.get("user", {})
                profile = user_data.get("profile", {})
                
                return {
                    "id": user_data.get("id"),
                    "real_name": user_data.get("real_name", ""),
                    "display_name": profile.get("display_name", ""),
                    "email": profile.get("email", ""),
                    "tz": user_data.get("tz", ""),
                    "is_bot": user_data.get("is_bot", False),
                    "is_admin": user_data.get("is_admin", False),
                    "is_owner": user_data.get("is_owner", False)
                }
            else:
                logger.error(f"Error obteniendo info del usuario {user_id}: {response.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción obteniendo info del usuario {user_id}: {str(e)}")
            return None

    def start(self):
        """Inicia el bot en modo socket."""
        logger.info("Iniciando bot de Slack en modo Socket...")
        handler = SocketModeHandler(self.app, self.app_token)
        handler.start()