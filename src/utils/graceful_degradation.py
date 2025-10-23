"""
Sistema de degradación elegante para el Claude Programming Agent.
Maneja fallos de servicios externos de manera elegante con fallbacks.
"""

import logging
import time
from typing import Dict, Any, Callable, Optional, List
from functools import wraps
from enum import Enum
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """Estados de servicio"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"

@dataclass
class ServiceConfig:
    """Configuración de servicio"""
    name: str
    max_failures: int = 3
    failure_window: int = 300  # 5 minutos
    recovery_time: int = 60    # 1 minuto
    fallback_enabled: bool = True

class CircuitBreaker:
    """Implementación de Circuit Breaker pattern"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time = 0
        self.status = ServiceStatus.HEALTHY
        self.lock = Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Ejecuta función con circuit breaker"""
        with self.lock:
            # Verificar si podemos intentar recuperación
            if self.status == ServiceStatus.FAILED:
                if time.time() - self.last_failure_time > self.config.recovery_time:
                    self.status = ServiceStatus.RECOVERING
                    logger.info(f"🔄 Intentando recuperar servicio {self.config.name}")
                else:
                    raise ServiceUnavailableError(f"Servicio {self.config.name} no disponible")
        
        try:
            result = func(*args, **kwargs)
            
            # Éxito - resetear contador
            with self.lock:
                if self.status in [ServiceStatus.DEGRADED, ServiceStatus.RECOVERING]:
                    logger.info(f"✅ Servicio {self.config.name} recuperado")
                self.failure_count = 0
                self.status = ServiceStatus.HEALTHY
            
            return result
            
        except Exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.config.max_failures:
                    self.status = ServiceStatus.FAILED
                    logger.error(f"🚨 Servicio {self.config.name} marcado como fallido")
                else:
                    self.status = ServiceStatus.DEGRADED
                    logger.warning(f"⚠️ Servicio {self.config.name} degradado ({self.failure_count}/{self.config.max_failures})")
            
            raise e

class ServiceUnavailableError(Exception):
    """Error cuando un servicio no está disponible"""
    pass

class GracefulDegradation:
    """Sistema de degradación elegante"""
    
    def __init__(self):
        self.services: Dict[str, CircuitBreaker] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.lock = Lock()
        self.initialized = False
    
    def initialize(self):
        """Inicializa el sistema de degradación elegante"""
        if not self.initialized:
            setup_default_services()
            self.initialized = True
            logger.info("✅ Sistema de degradación elegante inicializado")
    
    def can_operate_in_degraded_mode(self) -> bool:
        """Verifica si el sistema puede operar en modo degradado"""
        if not self.services:
            return True  # Sin servicios registrados, puede operar
        
        # Verificar si al menos algunos servicios están disponibles o tienen fallbacks
        available_services = 0
        for service_name, circuit_breaker in self.services.items():
            if (circuit_breaker.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED] or
                service_name in self.fallback_handlers):
                available_services += 1
        
        return available_services > 0
    
    def mark_service_unavailable(self, service_name: str):
        """Marca un servicio como no disponible"""
        # Si el servicio no está registrado, lo registramos primero
        if service_name not in self.services:
            config = ServiceConfig(name=service_name, max_failures=3, failure_window=300, recovery_time=60)
            self.register_service(config)
        
        with self.lock:
            self.services[service_name].status = ServiceStatus.FAILED
            self.services[service_name].failure_count = self.services[service_name].config.max_failures
            self.services[service_name].last_failure_time = time.time()
        logger.warning(f"⚠️ Servicio {service_name} marcado como no disponible")
    
    def is_service_available(self, service_name: str) -> bool:
        """Verifica si un servicio está disponible"""
        if service_name not in self.services:
            # Para servicios no registrados, primero los registramos con configuración por defecto
            config = ServiceConfig(name=service_name, max_failures=3, failure_window=300, recovery_time=60)
            self.register_service(config)
        
        circuit_breaker = self.services[service_name]
        return circuit_breaker.status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED, ServiceStatus.RECOVERING]
    
    def register_service(self, config: ServiceConfig):
        """Registra un servicio para monitoreo"""
        with self.lock:
            self.services[config.name] = CircuitBreaker(config)
        logger.info(f"📝 Servicio {config.name} registrado para monitoreo")
    
    def register_fallback(self, service_name: str, fallback_func: Callable):
        """Registra función de fallback para un servicio"""
        with self.lock:
            self.fallback_handlers[service_name] = fallback_func
        logger.info(f"🔄 Fallback registrado para servicio {service_name}")
    
    def call_service(self, service_name: str, func: Callable, *args, **kwargs):
        """Llama a un servicio con degradación elegante"""
        if service_name not in self.services:
            # Si no está registrado, llamar directamente
            return func(*args, **kwargs)
        
        circuit_breaker = self.services[service_name]
        
        try:
            return circuit_breaker.call(func, *args, **kwargs)
            
        except ServiceUnavailableError:
            # Servicio no disponible, usar fallback si existe
            if service_name in self.fallback_handlers:
                logger.info(f"🔄 Usando fallback para servicio {service_name}")
                return self.fallback_handlers[service_name](*args, **kwargs)
            else:
                raise
        
        except Exception as e:
            # Error en el servicio, intentar fallback
            if (service_name in self.fallback_handlers and 
                circuit_breaker.config.fallback_enabled):
                logger.warning(f"⚠️ Error en {service_name}, usando fallback: {str(e)}")
                return self.fallback_handlers[service_name](*args, **kwargs)
            else:
                raise
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Obtiene el estado de un servicio"""
        if service_name not in self.services:
            return {"status": "unknown", "message": "Servicio no registrado"}
        
        circuit_breaker = self.services[service_name]
        
        return {
            "name": service_name,
            "status": circuit_breaker.status.value,
            "failure_count": circuit_breaker.failure_count,
            "max_failures": circuit_breaker.config.max_failures,
            "last_failure_time": circuit_breaker.last_failure_time,
            "has_fallback": service_name in self.fallback_handlers
        }
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene el estado de todos los servicios"""
        return {
            name: self.get_service_status(name) 
            for name in self.services.keys()
        }

# Instancia global
degradation_manager = GracefulDegradation()

# Decorador para servicios con degradación elegante
def with_graceful_degradation(service_name: str, fallback_func: Optional[Callable] = None):
    """Decorador para aplicar degradación elegante a una función"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return degradation_manager.call_service(service_name, func, *args, **kwargs)
            except Exception as e:
                if fallback_func:
                    logger.warning(f"⚠️ Usando fallback inline para {service_name}: {str(e)}")
                    return fallback_func(*args, **kwargs)
                raise
        return wrapper
    return decorator

# Funciones de fallback predefinidas
def anthropic_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback para API de Anthropic"""
    return {
        "text": "🤖 **Servicio temporalmente no disponible**\n\n"
               "El servicio de análisis de Claude está experimentando problemas temporales. "
               "Por favor, intenta nuevamente en unos minutos.\n\n"
               "💡 **Mientras tanto, puedes:**\n"
               "• Usar comandos básicos como `/help`\n"
               "• Revisar la documentación\n"
               "• Contactar al administrador si el problema persiste",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🤖 *Servicio temporalmente no disponible*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "El servicio de análisis está experimentando problemas. Intenta nuevamente en unos minutos."
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 Usa `/help` para ver comandos disponibles"
                    }
                ]
            }
        ]
    }

def slack_fallback(*args, **kwargs) -> str:
    """Fallback para API de Slack"""
    return "📱 Servicio de Slack temporalmente no disponible. Mensaje guardado para reenvío."

def code_analysis_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback para análisis de código"""
    return {
        "status": "degraded",
        "message": "Análisis básico disponible. Funcionalidades avanzadas temporalmente no disponibles.",
        "suggestions": [
            "Verificar sintaxis básica",
            "Revisar imports y dependencias",
            "Consultar documentación oficial"
        ]
    }

def code_generation_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback para generación de código"""
    return {
        "status": "degraded", 
        "message": "Generación de código no disponible. Proporcionando plantillas básicas.",
        "templates": {
            "python": "# Plantilla básica de Python\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()",
            "javascript": "// Plantilla básica de JavaScript\nfunction main() {\n    // Tu código aquí\n}\n\nmain();",
            "html": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Página</title>\n</head>\n<body>\n    <!-- Tu contenido aquí -->\n</body>\n</html>"
        }
    }

# Configuración de servicios por defecto
def setup_default_services():
    """Configura servicios por defecto con degradación elegante"""
    
    # Configurar Anthropic API
    anthropic_config = ServiceConfig(
        name="anthropic",
        max_failures=3,
        failure_window=300,
        recovery_time=60,
        fallback_enabled=True
    )
    degradation_manager.register_service(anthropic_config)
    degradation_manager.register_fallback("anthropic", anthropic_fallback)
    
    # Configurar Slack API
    slack_config = ServiceConfig(
        name="slack",
        max_failures=5,
        failure_window=180,
        recovery_time=30,
        fallback_enabled=True
    )
    degradation_manager.register_service(slack_config)
    degradation_manager.register_fallback("slack", slack_fallback)
    
    # Configurar análisis de código
    code_analysis_config = ServiceConfig(
        name="code_analysis",
        max_failures=2,
        failure_window=120,
        recovery_time=45,
        fallback_enabled=True
    )
    degradation_manager.register_service(code_analysis_config)
    degradation_manager.register_fallback("code_analysis", code_analysis_fallback)
    
    # Configurar generación de código
    code_generation_config = ServiceConfig(
        name="code_generation",
        max_failures=2,
        failure_window=120,
        recovery_time=45,
        fallback_enabled=True
    )
    degradation_manager.register_service(code_generation_config)
    degradation_manager.register_fallback("code_generation", code_generation_fallback)
    
    logger.info("✅ Servicios de degradación elegante configurados")