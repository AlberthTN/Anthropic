"""
Módulo de manejo robusto de errores para el Claude Programming Agent.
Proporciona decoradores, utilidades de retry y logging avanzado.
"""

import functools
import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime
import json
import os

# Configurar logger específico para errores
error_logger = logging.getLogger('claude_agent.errors')

class AgentError(Exception):
    """Excepción base para errores del agente."""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "AGENT_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class APIError(AgentError):
    """Error relacionado con APIs externas (Anthropic, Slack)."""
    def __init__(self, message: str, api_name: str, status_code: int = None, **kwargs):
        super().__init__(message, f"API_ERROR_{api_name.upper()}", **kwargs)
        self.api_name = api_name
        self.status_code = status_code

class ValidationError(AgentError):
    """Error de validación de datos."""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, "VALIDATION_ERROR", **kwargs)
        self.field = field

class ProcessingError(AgentError):
    """Error durante el procesamiento de código o análisis."""
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(message, "PROCESSING_ERROR", **kwargs)
        self.operation = operation

def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorador para reintentar operaciones que fallan.
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial entre reintentos (segundos)
        backoff_factor: Factor de incremento del delay
        exceptions: Tupla de excepciones que activarán el retry
        on_retry: Función a llamar en cada reintento
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Último intento fallido
                        error_logger.error(
                            f"Función {func.__name__} falló después de {max_attempts} intentos: {str(e)}"
                        )
                        raise
                    
                    # Log del reintento
                    error_logger.warning(
                        f"Intento {attempt + 1}/{max_attempts} falló para {func.__name__}: {str(e)}. "
                        f"Reintentando en {current_delay}s..."
                    )
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            raise last_exception
        
        return wrapper
    return decorator

def safe_execute(
    operation: str,
    fallback_value: Any = None,
    log_errors: bool = True,
    raise_on_error: bool = False
):
    """
    Decorador para ejecutar funciones de forma segura con fallback.
    
    Args:
        operation: Nombre de la operación para logging
        fallback_value: Valor a retornar si la función falla
        log_errors: Si registrar errores en el log
        raise_on_error: Si re-lanzar la excepción después del logging
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    error_context = {
                        'operation': operation,
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()),
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'traceback': traceback.format_exc()
                    }
                    
                    error_logger.error(
                        f"Error en operación '{operation}': {str(e)}",
                        extra={'error_context': error_context}
                    )
                
                if raise_on_error:
                    raise
                
                return fallback_value
        
        return wrapper
    return decorator

class ErrorCollector:
    """Colector de errores para análisis y monitoreo."""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors: List[Dict] = []
        self.error_counts: Dict[str, int] = {}
    
    def add_error(self, error: Exception, context: Dict = None):
        """Agregar un error al colector."""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'context': context or {},
            'traceback': traceback.format_exc() if hasattr(error, '__traceback__') else None
        }
        
        # Agregar información específica para errores del agente
        if isinstance(error, AgentError):
            error_info.update({
                'error_code': error.error_code,
                'details': error.details
            })
        
        self.errors.append(error_info)
        
        # Mantener solo los últimos max_errors
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        
        # Contar tipos de errores
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_error_summary(self) -> Dict:
        """Obtener resumen de errores."""
        return {
            'total_errors': len(self.errors),
            'error_counts': self.error_counts.copy(),
            'recent_errors': self.errors[-10:] if self.errors else []
        }
    
    def clear_errors(self):
        """Limpiar el colector de errores."""
        self.errors.clear()
        self.error_counts.clear()

# Instancia global del colector de errores
error_collector = ErrorCollector()

def log_error_with_context(
    error: Exception,
    context: Dict = None,
    operation: str = None,
    user_id: str = None
):
    """
    Registrar error con contexto completo.
    
    Args:
        error: La excepción ocurrida
        context: Contexto adicional del error
        operation: Operación que estaba ejecutándose
        user_id: ID del usuario si aplica
    """
    error_context = {
        'operation': operation,
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        **(context or {})
    }
    
    # Agregar al colector
    error_collector.add_error(error, error_context)
    
    # Log detallado
    error_logger.error(
        f"Error en {operation or 'operación desconocida'}: {str(error)}",
        extra={
            'error_type': type(error).__name__,
            'error_context': error_context,
            'user_id': user_id
        },
        exc_info=True
    )

def create_error_response(
    error: Exception,
    user_friendly: bool = True,
    include_details: bool = False
) -> Dict[str, Any]:
    """
    Crear respuesta de error formateada para Slack.
    
    Args:
        error: La excepción ocurrida
        user_friendly: Si usar mensaje amigable para el usuario
        include_details: Si incluir detalles técnicos
    
    Returns:
        Dict con la respuesta formateada
    """
    if isinstance(error, AgentError):
        if user_friendly:
            message = f"❌ {error.message}"
        else:
            message = f"❌ Error {error.error_code}: {error.message}"
        
        if include_details and error.details:
            details_text = "\n".join([f"• {k}: {v}" for k, v in error.details.items()])
            message += f"\n\n*Detalles:*\n{details_text}"
    
    elif isinstance(error, (ConnectionError, TimeoutError)):
        message = "🔌 Problema de conexión. Por favor intenta nuevamente en unos momentos."
    
    elif isinstance(error, ValueError):
        message = "⚠️ Los datos proporcionados no son válidos. Por favor verifica tu solicitud."
    
    else:
        if user_friendly:
            message = "❌ Ocurrió un error inesperado. El equipo técnico ha sido notificado."
        else:
            message = f"❌ Error: {str(error)}"
    
    return {
        "text": message,
        "response_type": "ephemeral"  # Solo visible para el usuario
    }

def setup_error_logging(log_file: str = "logs/errors.log", level: int = logging.ERROR):
    """
    Configurar logging específico para errores.
    
    Args:
        log_file: Archivo donde guardar los logs de errores
        level: Nivel de logging
    """
    # Crear directorio de logs si no existe
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configurar handler para archivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    # Formato detallado para errores
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
        'Context: %(error_context)s\n'
        '%(exc_info)s\n' + '-' * 80,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Agregar handler al logger de errores
    error_logger.addHandler(file_handler)
    error_logger.setLevel(level)

# Configurar logging de errores al importar el módulo
setup_error_logging()