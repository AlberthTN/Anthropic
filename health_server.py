"""
Servidor de salud para monitoreo externo del Claude Programming Agent.
Proporciona endpoints HTTP para verificar el estado del sistema.
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from threading import Thread
import time

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.health_monitor import health_monitor
from utils.graceful_degradation import degradation_manager
from utils.error_handler import ErrorCollector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint básico de salud"""
    try:
        # Asegurar que el monitor esté iniciado
        if not health_monitor.is_running:
            health_monitor.start_monitoring()
            
        status = health_monitor.get_health_status()
        
        # Determinar código de respuesta HTTP basado en el estado
        if status["status"] == "healthy":
            http_status = 200
        elif status["status"] == "warning":
            http_status = 200  # Aún funcional
        else:  # critical o unknown
            http_status = 503  # Service Unavailable
        
        return jsonify({
            "status": status["status"],
            "timestamp": status["timestamp"],
            "uptime_hours": round(status["uptime_hours"], 2),
            "message": f"Sistema {status['status']}"
        }), http_status
        
    except Exception as e:
        logger.error(f"Error en health check: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Error interno del servidor de salud"
        }), 500

@app.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Endpoint detallado de salud"""
    try:
        status = health_monitor.get_health_status()
        services_status = degradation_manager.get_all_services_status()
        
        return jsonify({
            "overall_status": status["status"],
            "timestamp": status["timestamp"],
            "system_metrics": status["system"],
            "system_info": {
                "uptime_hours": status.get("uptime_hours", 0),
                "version": "1.0.0",
                "environment": "development"
            },
            "metrics": {
                "performance": status["performance"],
                "apis": status["apis"],
                "errors": status["errors"]
            },
            "performance_metrics": status["performance"],
            "services": services_status,
            "apis": status["apis"],
            "errors": status["errors"]
        }), 200
        
    except Exception as e:
        logger.error(f"Error en detailed health: {e}")
        return jsonify({
            "status": "error",
            "message": "Error obteniendo métricas detalladas"
        }), 500

@app.route('/health/report', methods=['GET'])
def health_report():
    """Endpoint de reporte de salud legible"""
    try:
        report = health_monitor.get_health_report()
        
        # Determinar formato de respuesta
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "report": report,
                "format": "markdown"
            }), 200
        else:
            return report, 200, {'Content-Type': 'text/plain; charset=utf-8'}
            
    except Exception as e:
        logger.error(f"Error en health report: {e}")
        return "Error generando reporte de salud", 500

@app.route('/health/services', methods=['GET'])
def services_status():
    """Estado de servicios individuales"""
    try:
        services = degradation_manager.get_all_services_status()
        
        return jsonify({
            "services": services,
            "total_services": len(services),
            "healthy_services": len([s for s in services.values() if s["status"] == "healthy"]),
            "degraded_services": len([s for s in services.values() if s["status"] == "degraded"]),
            "failed_services": len([s for s in services.values() if s["status"] == "failed"])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en services status: {e}")
        return jsonify({
            "error": "Error obteniendo estado de servicios"
        }), 500

@app.route('/health/metrics', methods=['GET'])
def system_metrics():
    """Métricas del sistema"""
    try:
        status = health_monitor.get_health_status()
        
        # Formatear métricas para Prometheus si se solicita
        if request.headers.get('Accept') == 'text/plain':
            metrics_text = f"""# HELP claude_agent_cpu_percent CPU usage percentage
# TYPE claude_agent_cpu_percent gauge
claude_agent_cpu_percent {status["system"]["cpu_percent"]}

# HELP claude_agent_memory_percent Memory usage percentage  
# TYPE claude_agent_memory_percent gauge
claude_agent_memory_percent {status["system"]["memory_percent"]}

# HELP claude_agent_error_rate Error rate percentage
# TYPE claude_agent_error_rate gauge
claude_agent_error_rate {status["performance"]["error_rate"]}

# HELP claude_agent_response_time Average response time in seconds
# TYPE claude_agent_response_time gauge
claude_agent_response_time {status["performance"]["avg_response_time"]}

# HELP claude_agent_uptime_hours Uptime in hours
# TYPE claude_agent_uptime_hours counter
claude_agent_uptime_hours {status["uptime_hours"]}
"""
            return metrics_text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error en system metrics: {e}")
        return jsonify({
            "error": "Error obteniendo métricas del sistema"
        }), 500

@app.route('/health/ping', methods=['GET'])
def ping():
    """Endpoint simple de ping"""
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "message": "pong"
    }), 200

@app.errorhandler(404)
def not_found(error):
    """Manejador de errores 404"""
    return jsonify({
        "error": "Endpoint no encontrado",
        "available_endpoints": [
            "/health",
            "/health/detailed", 
            "/health/report",
            "/health/services",
            "/health/metrics",
            "/health/ping"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejador de errores 500"""
    return jsonify({
        "error": "Error interno del servidor",
        "message": "Consulta los logs para más detalles"
    }), 500

def start_health_server(port: int = 8080, host: str = "0.0.0.0"):
    """Inicia el servidor de salud"""
    try:
        logger.info(f"🏥 Iniciando servidor de salud en {host}:{port}")
        
        # Configurar Flask para producción
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False
        
        # Iniciar servidor
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Error iniciando servidor de salud: {e}")
        raise

def start_health_server_thread(port: int = 8080, host: str = "0.0.0.0"):
    """Inicia el servidor de salud en un hilo separado"""
    def run_server():
        start_health_server(port, host)
    
    thread = Thread(target=run_server, daemon=True)
    thread.start()
    logger.info(f"🏥 Servidor de salud iniciado en hilo separado: http://{host}:{port}")
    return thread

if __name__ == "__main__":
    # Configurar puerto desde variable de entorno
    port = int(os.getenv("HEALTH_PORT", 8080))
    host = os.getenv("HEALTH_HOST", "0.0.0.0")
    
    # Iniciar monitor de salud
    health_monitor.start_monitoring()
    
    try:
        start_health_server(port, host)
    except KeyboardInterrupt:
        logger.info("🛑 Servidor de salud detenido por el usuario")
    finally:
        health_monitor.stop_monitoring()