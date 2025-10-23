"""Utilidades para el Claude Programming Agent.
Incluye manejo de errores, logging, monitoreo de salud y degradación elegante."""

from .error_handler import (
    AgentError,
    APIError, 
    ValidationError,
    ProcessingError,
    retry_on_failure,
    safe_execute,
    ErrorCollector,
    log_error_with_context,
    create_error_response,
    setup_error_logging
)

from .logging_config import (
    setup_logging,
    log_user_operation,
    log_api_call,
    log_metrics
)

from .health_monitor import (
    HealthMonitor,
    HealthMetrics,
    APIMetrics,
    health_monitor
)

from .graceful_degradation import (
    GracefulDegradation,
    ServiceConfig,
    ServiceStatus,
    ServiceUnavailableError,
    degradation_manager,
    with_graceful_degradation,
    setup_default_services
)

__all__ = [
    # Error handling
    'AgentError', 'APIError', 'ValidationError', 'ProcessingError',
    'retry_on_failure', 'safe_execute', 'ErrorCollector',
    'log_error_with_context', 'create_error_response', 'setup_error_logging',
    
    # Logging
    'setup_logging', 'log_user_operation', 'log_api_call', 'log_metrics',
    
    # Health monitoring
    'HealthMonitor', 'HealthMetrics', 'APIMetrics', 'health_monitor',
    
    # Graceful degradation
    'GracefulDegradation', 'ServiceConfig', 'ServiceStatus', 
    'ServiceUnavailableError', 'degradation_manager', 
    'with_graceful_degradation', 'setup_default_services'
]