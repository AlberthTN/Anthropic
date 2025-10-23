"""
Configuración avanzada de logging para el Claude Programming Agent.
Incluye rotación de logs, diferentes niveles y formateo estructurado.
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """Formatter que produce logs estructurados en JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Crear estructura base del log
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información adicional si está disponible
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        
        if hasattr(record, 'error_context'):
            log_entry['error_context'] = record.error_context
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))

class ColoredConsoleFormatter(logging.Formatter):
    """Formatter con colores para la consola."""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Obtener color para el nivel
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Formatear mensaje con color
        record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)

def setup_logging(
    app_name: str = "claude_agent",
    log_dir: str = "logs",
    log_level: str = "INFO",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_json_logs: bool = True
) -> Dict[str, logging.Logger]:
    """
    Configurar sistema de logging completo.
    
    Args:
        app_name: Nombre de la aplicación
        log_dir: Directorio para archivos de log
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_file_size: Tamaño máximo de archivo de log en bytes
        backup_count: Número de archivos de backup a mantener
        enable_console: Si habilitar logging a consola
        enable_json_logs: Si habilitar logs estructurados en JSON
    
    Returns:
        Dict con los loggers configurados
    """
    # Crear directorio de logs
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configurar nivel de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Limpiar configuración existente
    logging.getLogger().handlers.clear()
    
    # Configurar logger principal
    main_logger = logging.getLogger(app_name)
    main_logger.setLevel(numeric_level)
    
    # Logger específico para errores
    error_logger = logging.getLogger(f"{app_name}.errors")
    error_logger.setLevel(logging.ERROR)
    
    # Logger para operaciones de usuario
    user_logger = logging.getLogger(f"{app_name}.user_operations")
    user_logger.setLevel(logging.INFO)
    
    # Logger para APIs externas
    api_logger = logging.getLogger(f"{app_name}.api")
    api_logger.setLevel(logging.INFO)
    
    # Logger para métricas y monitoreo
    metrics_logger = logging.getLogger(f"{app_name}.metrics")
    metrics_logger.setLevel(logging.INFO)
    
    # === HANDLERS DE ARCHIVO ===
    
    # Handler principal con rotación
    main_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    main_file_handler.setLevel(numeric_level)
    
    # Handler para errores
    error_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}_errors.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # Handler para operaciones de usuario
    user_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}_user_operations.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    user_file_handler.setLevel(logging.INFO)
    
    # Handler para APIs
    api_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}_api.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    api_file_handler.setLevel(logging.INFO)
    
    # Handler para métricas (JSON estructurado)
    metrics_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"{app_name}_metrics.json",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    metrics_file_handler.setLevel(logging.INFO)
    
    # === FORMATTERS ===
    
    # Formatter estándar para archivos de texto
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formatter detallado para errores
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d\n'
        'Message: %(message)s\n'
        '%(exc_info)s\n' + '-' * 80,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formatter JSON para métricas
    json_formatter = StructuredFormatter()
    
    # Aplicar formatters
    main_file_handler.setFormatter(standard_formatter)
    error_file_handler.setFormatter(detailed_formatter)
    user_file_handler.setFormatter(standard_formatter)
    api_file_handler.setFormatter(standard_formatter)
    metrics_file_handler.setFormatter(json_formatter)
    
    # === HANDLER DE CONSOLA ===
    
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        
        # Usar formatter con colores para consola
        console_formatter = ColoredConsoleFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Agregar handler de consola a todos los loggers
        main_logger.addHandler(console_handler)
    
    # === AGREGAR HANDLERS A LOGGERS ===
    
    # Logger principal
    main_logger.addHandler(main_file_handler)
    
    # Logger de errores
    error_logger.addHandler(error_file_handler)
    
    # Logger de operaciones de usuario
    user_logger.addHandler(user_file_handler)
    
    # Logger de APIs
    api_logger.addHandler(api_file_handler)
    
    # Logger de métricas
    metrics_logger.addHandler(metrics_file_handler)
    
    # === CONFIGURAR LOGGERS DE LIBRERÍAS EXTERNAS ===
    
    # Reducir verbosidad de librerías externas
    logging.getLogger('slack_bolt').setLevel(logging.WARNING)
    logging.getLogger('slack_sdk').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Log de inicialización
    main_logger.info(f"Sistema de logging inicializado - Nivel: {log_level}")
    main_logger.info(f"Directorio de logs: {log_path.absolute()}")
    
    return {
        'main': main_logger,
        'errors': error_logger,
        'user_operations': user_logger,
        'api': api_logger,
        'metrics': metrics_logger
    }

def log_user_operation(
    operation: str,
    user_id: str,
    details: Dict[str, Any] = None,
    success: bool = True
):
    """
    Registrar operación de usuario.
    
    Args:
        operation: Tipo de operación realizada
        user_id: ID del usuario
        details: Detalles adicionales de la operación
        success: Si la operación fue exitosa
    """
    user_logger = logging.getLogger('claude_agent.user_operations')
    
    status = "SUCCESS" if success else "FAILED"
    message = f"[{status}] {operation} - Usuario: {user_id}"
    
    if details:
        message += f" - Detalles: {json.dumps(details, ensure_ascii=False)}"
    
    if success:
        user_logger.info(message, extra={'user_id': user_id, 'operation': operation})
    else:
        user_logger.warning(message, extra={'user_id': user_id, 'operation': operation})

def log_api_call(
    api_name: str,
    endpoint: str,
    duration: float,
    status_code: int = None,
    error: str = None
):
    """
    Registrar llamada a API externa.
    
    Args:
        api_name: Nombre de la API (anthropic, slack, etc.)
        endpoint: Endpoint llamado
        duration: Duración de la llamada en segundos
        status_code: Código de estado HTTP si aplica
        error: Mensaje de error si la llamada falló
    """
    api_logger = logging.getLogger('claude_agent.api')
    
    message = f"API {api_name} - {endpoint} - {duration:.3f}s"
    
    if status_code:
        message += f" - Status: {status_code}"
    
    extra = {
        'api_name': api_name,
        'endpoint': endpoint,
        'duration': duration,
        'status_code': status_code
    }
    
    if error:
        message += f" - Error: {error}"
        extra['error'] = error
        api_logger.error(message, extra=extra)
    else:
        api_logger.info(message, extra=extra)

def log_metrics(metric_name: str, value: Any, tags: Dict[str, str] = None):
    """
    Registrar métrica del sistema.
    
    Args:
        metric_name: Nombre de la métrica
        value: Valor de la métrica
        tags: Tags adicionales para la métrica
    """
    metrics_logger = logging.getLogger('claude_agent.metrics')
    
    metric_data = {
        'metric': metric_name,
        'value': value,
        'tags': tags or {},
        'timestamp': datetime.now().isoformat()
    }
    
    metrics_logger.info(json.dumps(metric_data, ensure_ascii=False))

# Configurar logging al importar el módulo
loggers = setup_logging()