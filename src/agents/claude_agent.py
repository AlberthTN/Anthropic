import os
import json
import re
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from anthropic import Anthropic
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar utilidades
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.error_handler import (
    retry_on_failure, 
    safe_execute, 
    log_error_with_context,
    create_error_response,
    APIError,
    ValidationError,
    ProcessingError,
    ErrorCollector
)
from src.utils.logging_config import log_user_operation, log_api_call, log_metrics
from src.utils.health_monitor import health_monitor
from src.utils.graceful_degradation import degradation_manager, with_graceful_degradation
from src.tools.code_analyzer import CodeAnalyzer
from src.tools.code_generator import CodeGenerator
from src.tools.testing_debugging import TestingDebugger

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeProgrammingAgent:
    """
    Agente principal de programación usando Claude 4.0 con manejo robusto de errores,
    monitoreo de salud y degradación elegante.
    """
    
    def __init__(self):
        """Inicializa el agente de programación con sistemas de monitoreo integrados."""
        try:
            # Inicializar colector de errores
            self.error_collector = ErrorCollector()
            
            # Configurar cliente de Anthropic
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not self.anthropic_api_key:
                error = ValidationError("ANTHROPIC_API_KEY no encontrado en variables de entorno", "api_key")
                self.error_collector.add_error(error, {"component": "initialization"})
                raise error
            
            self.client = Anthropic(api_key=self.anthropic_api_key)
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            
            # Inicializar herramientas con manejo de errores
            try:
                self.code_analyzer = CodeAnalyzer()
                self.code_generator = CodeGenerator()
                self.testing_debugger = TestingDebugger()
                logger.info("✅ Herramientas inicializadas correctamente")
            except Exception as e:
                log_error_with_context(e, {"component": "tools_initialization"}, "tool_init", "system")
                # Continuar con herramientas limitadas
                self.code_analyzer = None
                self.code_generator = None
                self.testing_debugger = None
                logger.warning("⚠️ Herramientas no disponibles, funcionando en modo degradado")
            
            # Registrar herramientas disponibles
            self.available_tools = {}
            if self.code_analyzer:
                self.available_tools["analyze_code"] = self.code_analyzer.analyze_code
            if self.code_generator:
                self.available_tools["generate_code"] = self.code_generator.generate_code
            if self.testing_debugger:
                self.available_tools["run_unit_tests"] = self.testing_debugger.run_unit_tests
                self.available_tools["debug_code"] = self.testing_debugger.debug_code
            
            # Configuración del agente
            self.name = "ClaudeProgrammingAgent"
            self.description = "Experto en programación con Claude 4.0"
            self.instructions = self._get_system_instructions()
            
            # Registrar métricas de inicialización
            log_metrics("agent_initialization", 1, {"status": "success", "tools_count": len(self.available_tools)})
            logger.info(f"✅ Agente {self.name} inicializado con modelo {self.model}")
            
        except Exception as e:
            log_error_with_context(e, {"component": "agent_initialization"}, "init", "system")
            log_metrics("agent_initialization", 0, {"status": "failed", "error": str(e)})
            raise ProcessingError(f"Error inicializando agente: {str(e)}", "initialization")
    
    @with_graceful_degradation("anthropic_api")
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecuta una herramienta específica con manejo de errores."""
        try:
            if tool_name in self.available_tools:
                result = self.available_tools[tool_name](**kwargs)
                log_metrics("tool_execution", 1, {"tool": tool_name, "status": "success"})
                return result
            else:
                error_msg = f"Herramienta '{tool_name}' no encontrada"
                log_error_with_context(
                    ValidationError(error_msg, "tool_name"), 
                    {"tool_name": tool_name, "available_tools": list(self.available_tools.keys())}, 
                    "tool_execution", 
                    "system"
                )
                return {"status": "error", "message": error_msg}
        except Exception as e:
            log_error_with_context(e, {"tool_name": tool_name, "kwargs": kwargs}, "tool_execution", "system")
            log_metrics("tool_execution", 0, {"tool": tool_name, "status": "failed"})
            return create_error_response(e, "tool_execution")

    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(APIError, ConnectionError))
    @safe_execute(operation="analyze_request", log_errors=True)
    @with_graceful_degradation("anthropic_api")
    def analyze_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza una solicitud de programación usando Claude con manejo robusto de errores.
        
        Args:
            context: Contexto con información del usuario y solicitud
            
        Returns:
            Dict con la respuesta formateada
        """
        user_id = context.get("user", "unknown")
        text = context.get("text", "")
        
        # Validar entrada
        if not text.strip():
            error = ValidationError("Texto de solicitud vacío", "text")
            self.error_collector.add_error(error, {"user_id": user_id})
            return create_error_response(error, "analyze_request")
        
        # Log de la operación
        log_user_operation("analyze_request", user_id, {"text_length": len(text)})
        
        try:
            start_time = time.time()
            
            # Analizar la solicitud con Claude
            prompt = f"""Analiza esta solicitud de programación: {text}

IMPORTANTE: Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin explicaciones, sin formato markdown.

Identifica:
1. El tipo de solicitud (generación, análisis, debugging, etc.)
2. El lenguaje de programación involucrado
3. Los requisitos específicos
4. Cualquier contexto adicional relevante

Responde SOLO con este JSON:
{{
    "type": "tipo de solicitud",
    "language": "lenguaje de programación",
    "requirements": "requisitos detallados",
    "priority": "alta/media/baja",
    "estimated_complexity": "complejidad estimada"
}}"""

            import time
            start_time = time.time()
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            duration = time.time() - start_time
            log_api_call("anthropic", "analyze_request", duration)
            health_monitor.record_api_call("anthropic", True, duration)
            
            # Procesar respuesta
            analysis_text = response.content[0].text
            
            # Log de métricas
            log_metrics("request_analysis_duration", duration, {"user_id": user_id})
            log_user_operation("analyze_request", user_id, success=True)
            
            return {
                "text": f"📊 *Análisis de Solicitud*\n\n{analysis_text}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"📊 *Análisis completado para* <@{user_id}>"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": analysis_text
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
            
            # Registrar métricas de salud exitosas
            health_monitor.record_api_call("anthropic", True, time.time() - start_time)
                
        except Exception as e:
            health_monitor.record_api_call("anthropic", False, time.time() - start_time, str(e))
            log_error_with_context(e, context, "analyze_request", user_id)
            log_user_operation("analyze_request", user_id, success=False)
            self.error_collector.add_error(e, {"user_id": user_id, "operation": "analyze_request"})
            
            if isinstance(e, APIError):
                raise e
            else:
                raise APIError(f"Error en análisis de solicitud: {str(e)}", "anthropic")
        
        # Configuración del agente
        self.name = "ClaudeProgrammingAgent"
        self.description = "Experto en programación con Claude 4.0"
        self.instructions = self._get_system_instructions()
        
        logger.info(f"Agente {self.name} inicializado con modelo {self.model}")
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrae JSON de un texto que puede contener contenido adicional.
        
        Args:
            text: Texto que puede contener JSON
            
        Returns:
            Dict con el JSON parseado o None si no se encuentra
        """
        try:
             # Buscar bloques de código JSON
             json_patterns = [
                 r'```json\s*(\{.*?\})\s*```',  # JSON en bloque de código
                 r'```\s*(\{.*?\})\s*```',      # JSON en bloque de código sin especificar lenguaje
             ]
             
             for pattern in json_patterns:
                 matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
                 for match in matches:
                     try:
                         # Limpiar el match
                         clean_match = match.strip()
                         if clean_match.startswith('{') and clean_match.endswith('}'):
                             parsed = json.loads(clean_match)
                             logger.info(f"🎯 DEBUG - JSON encontrado con patrón: {pattern}")
                             return parsed
                     except json.JSONDecodeError:
                         continue
             
             # Si no se encuentra en bloques, buscar el primer JSON válido usando balanceo de llaves
             start_idx = text.find('{')
             if start_idx != -1:
                 # Encontrar el JSON balanceado manejando strings correctamente
                 brace_count = 0
                 in_string = False
                 escape_next = False
                 
                 for i, char in enumerate(text[start_idx:], start_idx):
                     if escape_next:
                         escape_next = False
                         continue
                         
                     if char == '\\' and in_string:
                         escape_next = True
                         continue
                         
                     if char == '"' and not escape_next:
                         in_string = not in_string
                         continue
                         
                     if not in_string:
                         if char == '{':
                             brace_count += 1
                         elif char == '}':
                             brace_count -= 1
                             if brace_count == 0:
                                 json_candidate = text[start_idx:i+1]
                                 try:
                                     parsed = json.loads(json_candidate)
                                     logger.info(f"🎯 DEBUG - JSON encontrado por balanceo de llaves")
                                     return parsed
                                 except json.JSONDecodeError:
                                     break
             
             logger.warning(f"⚠️ DEBUG - No se pudo extraer JSON válido del texto")
             return None
            
        except Exception as e:
            logger.error(f"❌ DEBUG - Error en extracción de JSON: {e}")
            return None
    
    def _get_system_instructions(self) -> str:
        """Obtiene las instrucciones del sistema para el agente."""
        return """Eres Claude, un experto en programación con conocimiento profundo en todos los lenguajes de programación existentes.

Tus capacidades incluyen:

1. **Generación de Código Inteligente**
   - Crea código eficiente y bien documentado
   - Aplica las mejores prácticas del lenguaje
   - Considera patrones de diseño y arquitectura
   - Implementa manejo de errores robusto

2. **Análisis de Código**
   - Evalúa la calidad y complejidad del código
   - Identifica problemas de rendimiento
   - Detecta vulnerabilidades de seguridad
   - Sugiere mejoras y optimizaciones

3. **Pruebas Unitarias**
   - Genera pruebas automatizadas completas
   - Asegura alta cobertura de código
   - Implementa pruebas edge cases
   - Usa frameworks de testing apropiados

4. **Debugging y Resolución de Errores**
   - Analiza errores y excepciones
   - Proporciona soluciones detalladas
   - Genera código de debugging
   - Explica la causa raíz de los problemas

5. **Desarrollo Full-Stack**
   - Frontend: HTML, CSS, JavaScript, React, Vue, Angular
   - Backend: Python, Node.js, Java, Go, Rust
   - Bases de datos: SQL, NoSQL, GraphQL
   - DevOps: Docker, Kubernetes, CI/CD

6. **Mejores Prácticas**
   - Principios SOLID y clean code
   - Patrones de diseño
   - Documentación clara
   - Código mantenible y escalable

REGLAS IMPORTANTES:
- Siempre explica tu razonamiento
- Proporciona ejemplos de uso
- Incluye documentación
- Considera casos edge
- Valida la seguridad del código
- Optimiza para rendimiento cuando sea relevante

Cuando generes código, incluye:
1. Documentación clara
2. Ejemplos de uso
3. Manejo de errores
4. Pruebas unitarias cuando sea apropiado
5. Consideraciones de rendimiento"""
    
    @retry_on_failure(max_attempts=2, delay=0.5)
    @safe_execute(operation="process_request", log_errors=True)
    @with_graceful_degradation("anthropic_api")
    def process_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud general de programación con manejo robusto de errores.
        
        Args:
            context: Contexto de la solicitud
            
        Returns:
            Dict con la respuesta formateada
        """
        user_id = context.get("user", "unknown")
        text = context.get("text", "")
        
        # Validar entrada
        if not text.strip():
            error = ValidationError("Texto de solicitud vacío", "text")
            self.error_collector.add_error(error, {"user_id": user_id})
            return create_error_response(error, "process_request")
        
        try:
            start_time = time.time()
            log_user_operation("process_request", user_id, {"text_length": len(text)})
            
            # Analizar la solicitud con Claude
            prompt = f"""Analiza esta solicitud de programación: {text}

Identifica:
1. El tipo de solicitud (generación, análisis, debugging, etc.)
2. El lenguaje de programación involucrado
3. Los requisitos específicos
4. Cualquier contexto adicional relevante

Proporciona una respuesta JSON con:
- type: tipo de solicitud
- language: lenguaje de programación
- requirements: requisitos detallados
- priority: prioridad (alta, media, baja)
- estimated_complexity: complejidad estimada"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                system=self.instructions,
                messages=[{"role": "user", "content": prompt}]
            )
            
            duration = time.time() - start_time
            response_time_ms = int(duration * 1000)  # Convert to milliseconds
            
            # Extract token usage from response
            tokens_used = None
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'input_tokens', 0)
                output_tokens = getattr(response.usage, 'output_tokens', 0)
                tokens_used = input_tokens + output_tokens
            
            log_api_call("anthropic", "process_request", duration)
            health_monitor.record_api_call("anthropic", True, duration)
            
            try:
                # Verificar que la respuesta tenga contenido
                if not response.content or len(response.content) == 0:
                    log_error_with_context(
                        Exception("Respuesta vacía de la API"), 
                        {"response": str(response)}, 
                        "empty_api_response", 
                        user_id
                    )
                    analysis = {"type": "general"}
                else:
                    response_text = response.content[0].text.strip()
                    
                    # DEBUG: Log completo de la respuesta para diagnosticar
                    logger.info(f"🔍 DEBUG - Respuesta completa de API: '{response_text}'")
                    logger.info(f"🔍 DEBUG - Longitud de respuesta: {len(response_text)}")
                    logger.info(f"🔍 DEBUG - Tipo de respuesta: {type(response_text)}")
                    
                    if not response_text:
                        log_error_with_context(
                            Exception("Texto de respuesta vacío"), 
                            {"response_content": response.content}, 
                            "empty_response_text", 
                            user_id
                        )
                        analysis = {"type": "general"}
                    else:
                        try:
                            # Intentar parsear directamente primero
                            analysis = json.loads(response_text)
                            logger.info(f"✅ DEBUG - JSON parseado exitosamente: {analysis}")
                        except json.JSONDecodeError as e:
                            # Si falla, intentar extraer JSON del texto
                            logger.info(f"🔍 DEBUG - Intentando extraer JSON del texto...")
                            analysis = self._extract_json_from_text(response_text)
                            
                            if analysis:
                                logger.info(f"✅ DEBUG - JSON extraído exitosamente: {analysis}")
                            else:
                                log_error_with_context(
                                    e, 
                                    {
                                        "response_text": response_text,
                                        "response_length": len(response_text),
                                        "first_100_chars": response_text[:100],
                                        "response_repr": repr(response_text)
                                    }, 
                                    "json_parse", 
                                    user_id
                                )
                                logger.error(f"❌ DEBUG - Error JSON: {e}")
                                logger.error(f"❌ DEBUG - Texto problemático: {repr(response_text)}")
                                # Fallback a respuesta general
                                analysis = {"type": "general"}
            except Exception as e:
                log_error_with_context(e, {"response": str(response)}, "api_response_processing", user_id)
                analysis = {"type": "general"}
            
            # Procesar según el tipo de solicitud
            request_type = analysis.get("type", "general")
            
            if request_type == "code_generation":
                return self.generate_code({
                    **context,
                    "language": analysis.get("language", "python"),
                    "requirements": analysis.get("requirements", text)
                })
            elif request_type == "code_analysis":
                return self.analyze_code({
                    **context,
                    "language": analysis.get("language", "python"),
                    "code": text
                })
            elif request_type == "debugging":
                return self.debug_code({
                    **context,
                    "language": analysis.get("language", "python"),
                    "code": text
                })
            else:
                # Usar Claude para generar una respuesta inteligente
                intelligent_prompt = f"""Como un asistente de programación experto, responde de manera útil y específica a esta consulta del usuario:

"{text}"

Proporciona una respuesta clara, práctica y directa. Si es una pregunta técnica, explica conceptos. Si necesita código, proporciona ejemplos. Si es una consulta general, ofrece orientación específica sobre programación.

Responde de manera conversacional y útil, como si fueras un programador senior ayudando a un colega."""

                # Medir tiempo para la respuesta inteligente
                intelligent_start_time = time.time()
                intelligent_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.7,
                    system=self.instructions,
                    messages=[{"role": "user", "content": intelligent_prompt}]
                )
                
                # Calcular métricas para la respuesta inteligente
                intelligent_duration = time.time() - intelligent_start_time
                intelligent_response_time_ms = int(intelligent_duration * 1000)
                
                # Extraer tokens de la respuesta inteligente
                intelligent_tokens_used = None
                if hasattr(intelligent_response, 'usage') and intelligent_response.usage:
                    input_tokens = getattr(intelligent_response.usage, 'input_tokens', 0)
                    output_tokens = getattr(intelligent_response.usage, 'output_tokens', 0)
                    intelligent_tokens_used = input_tokens + output_tokens
                
                response_text = intelligent_response.content[0].text
                
                response_data = {
                    "text": response_text,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": response_text
                            }
                        }
                    ],
                    "api_metrics": {
                        "tokens_used": intelligent_tokens_used,
                        "model_used": self.model,
                        "response_time_ms": intelligent_response_time_ms
                    }
                }
                
                # Registrar métricas de salud exitosas
                health_monitor.record_api_call("anthropic", True, intelligent_duration)
                return response_data
                
        except Exception as e:
            health_monitor.record_api_call("anthropic", False, time.time() - start_time, str(e))
            log_error_with_context(e, context, "process_request", user_id)
            log_user_operation("process_request", user_id, success=False)
            self.error_collector.add_error(e, {"user_id": user_id, "operation": "process_request"})
            return create_error_response(e, "process_request")
    
    @safe_execute(operation="generate_code", log_errors=True)
    @with_graceful_degradation("code_generator")
    def generate_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera código basado en requisitos con manejo robusto de errores.
        
        Args:
            context: Contexto con lenguaje y requisitos
            
        Returns:
            Dict con el código generado
        """
        user_id = context.get("user", "unknown")
        language = context.get("language", "python")
        requirements = context.get("requirements", "")
        
        # Validar entrada
        if not requirements.strip():
            error = ValidationError("Requisitos de código vacíos", "requirements")
            self.error_collector.add_error(error, {"user_id": user_id, "language": language})
            return create_error_response(error, "generate_code")
        
        try:
            log_user_operation("generate_code", user_id, {"language": language, "requirements_length": len(requirements)})
            logger.info(f"Generando código en {language} para {user_id}")
            
            # Verificar disponibilidad de herramientas
            if not self.code_generator:
                # Modo degradado: usar Claude directamente
                logger.warning("CodeGenerator no disponible, usando Claude directamente")
                generated_code = self._generate_code_fallback(requirements, language)
            else:
                # Usar la herramienta de generación de código
                generated_code = self.code_generator.generate_code(requirements, language)
            
            # Registrar métricas
            log_metrics("code_generation", 1, {"language": language, "user_id": user_id})
            log_user_operation("generate_code", user_id, success=True)
            
            # Crear respuesta formateada
            return {
                "text": f"✅ Código generado en *{language}*:",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Código generado en {language} para <@{user_id}>: *"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{language}\\n{generated_code.get('code', 'No se generó código')}\\n```"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"💡 {generated_code.get('explanation', 'Código generado exitosamente')}"
                            }
                        ]
                    }
                ],
                "code": generated_code.get('code', ''),
                "language": language,
                "explanation": generated_code.get('explanation', ''),
                "best_practices": generated_code.get('best_practices', [])
            }
            
        except Exception as e:
            log_error_with_context(e, context, "generate_code", user_id)
            log_user_operation("generate_code", user_id, success=False)
            log_metrics("code_generation", 0, {"language": language, "user_id": user_id, "error": str(e)})
            self.error_collector.add_error(e, {"user_id": user_id, "language": language, "operation": "generate_code"})
            return create_error_response(e, "generate_code")
    
    @safe_execute(operation="analyze_code", log_errors=True)
    @with_graceful_degradation("code_analyzer")
    def analyze_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza código proporcionado con manejo robusto de errores.
        
        Args:
            context: Contexto con lenguaje y código
            
        Returns:
            Dict con el análisis
        """
        user_id = context.get("user", "unknown")
        language = context.get("language", "python")
        code = context.get("code", "")
        
        # Validar entrada
        if not code.strip():
            error = ValidationError("Código para análisis vacío", "code")
            self.error_collector.add_error(error, {"user_id": user_id, "language": language})
            return create_error_response(error, "analyze_code")
        
        try:
            log_user_operation("analyze_code", user_id, {"language": language, "code_length": len(code)})
            logger.info(f"Analizando código en {language} para {user_id}")
            
            # Verificar disponibilidad de herramientas
            if not self.code_analyzer:
                # Modo degradado: análisis básico
                logger.warning("CodeAnalyzer no disponible, usando análisis básico")
                analysis = self._analyze_code_fallback(code, language)
            else:
                # Usar la herramienta de análisis de código
                analysis = self.code_analyzer.analyze_code(code, language)
            
            # Formatear respuesta
            metrics = analysis.get("metrics", {})
            suggestions = analysis.get("suggestions", [])
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*📊 Análisis de Código para <@{user_id}>*"
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
                        "text": "*💡 Sugerencias de mejora:*"
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
            
            # Registrar métricas
            log_metrics("code_analysis", 1, {"language": language, "user_id": user_id})
            log_user_operation("analyze_code", user_id, success=True)
            
            return {
                "text": "Análisis completado",
                "blocks": blocks,
                "analysis": analysis.get("analysis", ""),
                "metrics": metrics,
                "suggestions": suggestions
            }
            
        except Exception as e:
            log_error_with_context(e, context, "analyze_code", user_id)
            log_user_operation("analyze_code", user_id, success=False)
            log_metrics("code_analysis", 0, {"language": language, "user_id": user_id, "error": str(e)})
            self.error_collector.add_error(e, {"user_id": user_id, "language": language, "operation": "analyze_code"})
            return create_error_response(e, "analyze_code")

    def test_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta pruebas de código.
        
        Args:
            context: Contexto con lenguaje y código
            
        Returns:
            Dict con los resultados de las pruebas
        """
        try:
            language = context.get("language", "python")
            code = context.get("code", "")
            user = context.get("user", "")
            
            logger.info(f"Ejecutando pruebas para código en {language} para {user}")
            
            # Usar la herramienta de testing
            test_results = self.testing_debugger.run_tests(code, language)
            
            passed = test_results.get("passed", 0)
            failed = test_results.get("failed", 0)
            total = passed + failed
            
            return {
                "text": "Pruebas ejecutadas",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🧪 Resultados de Pruebas para <@{user}>*"
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
                                "text": f"*📈 Cobertura:* {test_results.get('coverage', 'N/A')}"
                            }
                        ]
                    }
                ],
                "test_results": test_results.get("results", []),
                "passed": passed,
                "failed": failed,
                "coverage": test_results.get("coverage", "0%")
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando pruebas: {str(e)}")
            return {
                "text": f"Lo siento, hubo un error ejecutando las pruebas: {str(e)}"
            }
    
    def debug_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Depura código con errores.
        
        Args:
            context: Contexto con lenguaje y código
            
        Returns:
            Dict con los resultados de la depuración
        """
        try:
            language = context.get("language", "python")
            code = context.get("code", "")
            user = context.get("user", "")
            
            logger.info(f"Depurando código en {language} para {user}")
            
            # Usar la herramienta de debugging
            debug_results = self.testing_debugger.debug_code(code, language)
            
            issues = debug_results.get("issues_found", 0)
            suggestions = debug_results.get("suggestions", [])
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔍 Resultados de Depuración para <@{user}>*"
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
                        "text": "*💡 Sugerencias de solución:*"
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
                "blocks": blocks,
                "debug_analysis": debug_results.get("debug_analysis", ""),
                "issues_found": issues,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error en depuración: {str(e)}")
            return {
                "text": f"Lo siento, hubo un error en la depuración: {str(e)}"
            }
    
    def deploy_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Despliega código como aplicación web.
        
        Args:
            context: Contexto con tipo de deployment y código
            
        Returns:
            Dict con los resultados del deployment
        """
        try:
            deployment_type = context.get("deployment_type", "webapp")
            code = context.get("code", "")
            user = context.get("user", "")
            
            logger.info(f"Preparando deployment tipo {deployment_type} para {user}")
            
            # Analizar el código y preparar para deployment
            prompt = f"""Analiza este código para deployment como {deployment_type}:

{code}

Proporciona:
1. Requisitos de deployment
2. Configuración necesaria
3. Pasos de deployment
4. URL esperada o instrucciones

Responde en formato JSON."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.1,
                system=self.instructions,
                messages=[{"role": "user", "content": prompt}]
            )
            
            deployment_info = json.loads(response.content[0].text)
            
            # Simular deployment (en producción esto se conectaría a servicios reales)
            return {
                "text": f"✅ Deployment tipo {deployment_type} preparado para <@{user}>",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🚀 Deployment tipo {deployment_type} preparado:*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Estado:* Listo para deployment"
                        }
                    }
                ],
                "status": "ready",
                "deployment_type": deployment_type,
                "instructions": deployment_info
            }
            
        except Exception as e:
            logger.error(f"Error en deployment: {str(e)}")
            return {
                "text": f"Lo siento, hubo un error en el deployment: {str(e)}"
            }
    
    def review_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revisa código para calidad y mejores prácticas.
        
        Args:
            context: Contexto con lenguaje y código
            
        Returns:
            Dict con la revisión del código
        """
        try:
            language = context.get("language", "python")
            code = context.get("code", "")
            user = context.get("user", "")
            
            logger.info(f"Revisando código en {language} para {user}")
            
            # Usar Claude para revisión detallada
            prompt = f"""Revisa este código {language} para calidad y mejores prácticas:

{code}

Proporciona:
1. Calificación del 1-10
2. Lista de problemas encontrados
3. Sugerencias de mejora
4. Comentarios sobre legibilidad, mantenibilidad, rendimiento
5. Verificación de seguridad

Responde en formato JSON."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.1,
                system=self.instructions,
                messages=[{"role": "user", "content": prompt}]
            )
            
            review_info = json.loads(response.content[0].text)
            
            return {
                "text": f"👀 Revisión de código completada para <@{user}>",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*👀 Revisión de Código:*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Calificación:* {review_info.get('rating', 'N/A')}/10"
                        }
                    }
                ],
                "rating": review_info.get("rating", 0),
                "comments": review_info.get("comments", []),
                "issues": review_info.get("issues", []),
                "security_check": review_info.get("security", "")
            }
            
        except Exception as e:
            logger.error(f"Error en revisión: {str(e)}")
            return {
                "text": f"Lo siento, hubo un error en la revisión: {str(e)}"
            }
    
    def process_shared_file(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa archivos compartidos de código.
        
        Args:
            context: Contexto con información del archivo
            
        Returns:
            Dict con el análisis del archivo
        """
        try:
            user = context.get("user", "")
            file_name = context.get("file_name", "")
            file_type = context.get("file_type", "")
            
            logger.info(f"Procesando archivo compartido: {file_name} para {user}")
            
            # Determinar el lenguaje por la extensión
            language = self._get_language_from_extension(file_name)
            
            return {
                "text": f"📄 Archivo {file_name} recibido para <@{user}>",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*📄 Archivo recibido:*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Nombre:* {file_name}\\n*Tipo:* {file_type}\\n*Lenguaje detectado:* {language}"
                        }
                    }
                ],
                "file_name": file_name,
                "file_type": file_type,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            return {
                "text": f"Lo siento, hubo un error procesando el archivo: {str(e)}"
            }
    
    def _get_language_from_extension(self, filename: str) -> str:
        """Determina el lenguaje de programación por la extensión del archivo."""
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'swift': 'swift',
            'kt': 'kotlin',
            'scala': 'scala',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'sh': 'bash',
            'yaml': 'yaml',
            'yml': 'yaml',
            'json': 'json',
            'xml': 'xml'
        }
        
        return language_map.get(extension, 'text')
    
    def _generate_code_fallback(self, requirements: str, language: str) -> Dict[str, Any]:
        """
        Método de respaldo para generar código usando Claude directamente.
        
        Args:
            requirements: Requisitos del código
            language: Lenguaje de programación
            
        Returns:
            Dict con el código generado
        """
        try:
            prompt = f"""Genera código en {language} basado en estos requisitos:

{requirements}

Proporciona:
1. Código funcional y bien documentado
2. Explicación del código
3. Mejores prácticas aplicadas
4. Ejemplos de uso si es apropiado

Responde en formato JSON con las claves: code, explanation, best_practices"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                system=self.instructions,
                messages=[{"role": "user", "content": prompt}]
            )
            
            try:
                result = json.loads(response.content[0].text)
                return {
                    "code": result.get("code", "# Código no generado"),
                    "explanation": result.get("explanation", "Código generado en modo degradado"),
                    "best_practices": result.get("best_practices", [])
                }
            except json.JSONDecodeError:
                # Fallback si no se puede parsear JSON
                code_text = response.content[0].text
                return {
                    "code": code_text,
                    "explanation": "Código generado en modo degradado (sin análisis JSON)",
                    "best_practices": []
                }
                
        except Exception as e:
            log_error_with_context(e, {"requirements": requirements, "language": language}, "generate_code_fallback", "system")
            return {
                "code": f"# Error generando código: {str(e)}",
                "explanation": "Error en generación de código",
                "best_practices": []
            }
    
    def _analyze_code_fallback(self, code: str, language: str) -> Dict[str, Any]:
        """
        Método de respaldo para analizar código usando Claude directamente.
        
        Args:
            code: Código a analizar
            language: Lenguaje de programación
            
        Returns:
            Dict con el análisis
        """
        try:
            prompt = f"""Analiza este código {language}:

{code}

Proporciona:
1. Métricas básicas (líneas, complejidad estimada, calidad)
2. Análisis de la estructura y lógica
3. Sugerencias de mejora
4. Problemas potenciales identificados

Responde en formato JSON con las claves: metrics, analysis, suggestions"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.1,
                system=self.instructions,
                messages=[{"role": "user", "content": prompt}]
            )
            
            try:
                result = json.loads(response.content[0].text)
                return {
                    "metrics": result.get("metrics", {"lines": len(code.split('\n')), "complexity": "N/A", "quality": "N/A"}),
                    "analysis": result.get("analysis", "Análisis básico completado"),
                    "suggestions": result.get("suggestions", ["Análisis realizado en modo degradado"])
                }
            except json.JSONDecodeError:
                # Fallback básico
                lines = len(code.split('\n'))
                return {
                    "metrics": {"lines": lines, "complexity": "N/A", "quality": "N/A"},
                    "analysis": "Análisis básico: código procesado en modo degradado",
                    "suggestions": ["Revisar manualmente el código", "Verificar sintaxis y lógica"]
                }
                
        except Exception as e:
            log_error_with_context(e, {"code_length": len(code), "language": language}, "analyze_code_fallback", "system")
            lines = len(code.split('\n')) if code else 0
            return {
                "metrics": {"lines": lines, "complexity": "Error", "quality": "Error"},
                "analysis": f"Error en análisis: {str(e)}",
                "suggestions": ["Error en análisis de código"]
            }

# Crear instancia del agente solo si se ejecuta como script principal
if __name__ == "__main__":
    agent = ClaudeProgrammingAgent()