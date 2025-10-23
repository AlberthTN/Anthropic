"""
Sistema de monitoreo de salud para el Claude Programming Agent.
Proporciona métricas de sistema, monitoreo de APIs y alertas.
"""

import os
import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from threading import Thread, Event
import json

from .error_handler import ErrorCollector
from .logging_config import log_metrics

logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """Métricas de salud del sistema"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    uptime_seconds: float
    active_connections: int
    error_rate: float
    api_response_time_avg: float
    status: str  # healthy, warning, critical

@dataclass
class APIMetrics:
    """Métricas específicas de APIs"""
    service_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_response_time: float
    last_error: Optional[str]
    last_success: str

class HealthMonitor:
    """Monitor de salud del sistema"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.start_time = time.time()
        self.is_running = False
        self.stop_event = Event()
        self.monitor_thread = None
        
        # Colectores de métricas
        self.error_collector = ErrorCollector()
        self.api_metrics: Dict[str, APIMetrics] = {}
        self.health_history: List[HealthMetrics] = []
        self.max_history = 100  # Mantener últimas 100 mediciones
        
        # Umbrales de alerta
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'error_rate_warning': 5.0,  # 5% de errores
            'error_rate_critical': 15.0,  # 15% de errores
            'response_time_warning': 5.0,  # 5 segundos
            'response_time_critical': 10.0  # 10 segundos
        }
    
    def start_monitoring(self):
        """Inicia el monitoreo en segundo plano"""
        if self.is_running:
            return
            
        self.is_running = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🔍 Monitor de salud iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Monitor de salud detenido")
    
    def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        while not self.stop_event.wait(self.check_interval):
            try:
                metrics = self.collect_metrics()
                self.health_history.append(metrics)
                
                # Mantener historial limitado
                if len(self.health_history) > self.max_history:
                    self.health_history.pop(0)
                
                # Verificar alertas
                self._check_alerts(metrics)
                
                # Log de métricas
                log_metrics("system_health", 1, asdict(metrics))
                
            except Exception as e:
                logger.error(f"Error en monitoreo de salud: {e}")
    
    def collect_metrics(self) -> HealthMetrics:
        """Recolecta métricas actuales del sistema"""
        try:
            # Métricas del sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Usar el disco del directorio actual en Windows
            import os
            current_drive = os.path.splitdrive(os.getcwd())[0] + os.sep
            disk = psutil.disk_usage(current_drive)
            
            uptime = time.time() - self.start_time
            
            # Métricas de red (conexiones activas)
            connections = len(psutil.net_connections())
            
            # Métricas de errores
            error_rate = self._calculate_error_rate()
            
            # Métricas de APIs
            avg_response_time = self._calculate_avg_response_time()
            
            # Determinar estado de salud
            status = self._determine_health_status(
                cpu_percent, memory.percent, disk.percent, 
                error_rate, avg_response_time
            )
            
            return HealthMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                uptime_seconds=uptime,
                active_connections=connections,
                error_rate=error_rate,
                api_response_time_avg=avg_response_time,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error recolectando métricas: {e}")
            return HealthMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                uptime_seconds=0.0,
                active_connections=0,
                error_rate=100.0,
                api_response_time_avg=0.0,
                status="critical"
            )
    
    def record_api_call(self, service: str, success: bool, response_time: float, error: str = None):
        """Registra una llamada a API"""
        if service not in self.api_metrics:
            self.api_metrics[service] = APIMetrics(
                service_name=service,
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                avg_response_time=0.0,
                last_error=None,
                last_success=datetime.now().isoformat()
            )
        
        metrics = self.api_metrics[service]
        metrics.total_calls += 1
        
        if success:
            metrics.successful_calls += 1
            metrics.last_success = datetime.now().isoformat()
        else:
            metrics.failed_calls += 1
            metrics.last_error = error
        
        # Actualizar tiempo de respuesta promedio
        metrics.avg_response_time = (
            (metrics.avg_response_time * (metrics.total_calls - 1) + response_time) 
            / metrics.total_calls
        )
    
    def _calculate_error_rate(self) -> float:
        """Calcula la tasa de error general"""
        total_errors = sum(self.error_collector.error_counts.values())
        total_operations = sum(
            api.total_calls for api in self.api_metrics.values()
        )
        
        if total_operations == 0:
            return 0.0
        
        return (total_errors / total_operations) * 100
    
    def _calculate_avg_response_time(self) -> float:
        """Calcula el tiempo de respuesta promedio de todas las APIs"""
        if not self.api_metrics:
            return 0.0
        
        total_time = sum(api.avg_response_time for api in self.api_metrics.values())
        return total_time / len(self.api_metrics)
    
    def _determine_health_status(self, cpu: float, memory: float, disk: float, 
                                error_rate: float, response_time: float) -> str:
        """Determina el estado de salud basado en las métricas"""
        # Verificar condiciones críticas
        if (cpu >= self.thresholds['cpu_critical'] or
            memory >= self.thresholds['memory_critical'] or
            disk >= self.thresholds['disk_critical'] or
            error_rate >= self.thresholds['error_rate_critical'] or
            response_time >= self.thresholds['response_time_critical']):
            return "critical"
        
        # Verificar condiciones de advertencia
        if (cpu >= self.thresholds['cpu_warning'] or
            memory >= self.thresholds['memory_warning'] or
            disk >= self.thresholds['disk_warning'] or
            error_rate >= self.thresholds['error_rate_warning'] or
            response_time >= self.thresholds['response_time_warning']):
            return "warning"
        
        return "healthy"
    
    def _check_alerts(self, metrics: HealthMetrics):
        """Verifica y registra alertas basadas en las métricas"""
        alerts = []
        
        if metrics.cpu_percent >= self.thresholds['cpu_critical']:
            alerts.append(f"🚨 CPU crítico: {metrics.cpu_percent:.1f}%")
        elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
            alerts.append(f"⚠️ CPU alto: {metrics.cpu_percent:.1f}%")
        
        if metrics.memory_percent >= self.thresholds['memory_critical']:
            alerts.append(f"🚨 Memoria crítica: {metrics.memory_percent:.1f}%")
        elif metrics.memory_percent >= self.thresholds['memory_warning']:
            alerts.append(f"⚠️ Memoria alta: {metrics.memory_percent:.1f}%")
        
        if metrics.error_rate >= self.thresholds['error_rate_critical']:
            alerts.append(f"🚨 Tasa de error crítica: {metrics.error_rate:.1f}%")
        elif metrics.error_rate >= self.thresholds['error_rate_warning']:
            alerts.append(f"⚠️ Tasa de error alta: {metrics.error_rate:.1f}%")
        
        # Log de alertas
        for alert in alerts:
            logger.warning(alert)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtiene el estado de salud actual"""
        if not self.health_history:
            # Si no hay historial, crear métricas básicas
            try:
                current_metrics = self.collect_metrics()
                return {
                    "status": current_metrics.status,
                    "timestamp": current_metrics.timestamp,
                    "uptime_hours": current_metrics.uptime_seconds / 3600,
                    "system": {
                        "cpu_percent": current_metrics.cpu_percent,
                        "memory_percent": current_metrics.memory_percent,
                        "memory_available_mb": current_metrics.memory_available_mb,
                        "disk_usage_percent": current_metrics.disk_usage_percent,
                        "active_connections": current_metrics.active_connections
                    },
                    "performance": {
                        "error_rate": current_metrics.error_rate,
                        "avg_response_time": current_metrics.api_response_time_avg
                    },
                    "apis": {name: asdict(metrics) for name, metrics in self.api_metrics.items()},
                    "errors": self.error_collector.get_error_summary()
                }
            except Exception as e:
                logger.error(f"Error obteniendo métricas: {e}")
                return {
                    "status": "unknown", 
                    "message": "No hay datos disponibles",
                    "timestamp": datetime.now().isoformat(),
                    "uptime_hours": 0,
                    "system": {},
                    "performance": {},
                    "apis": {},
                    "errors": {"total_errors": 0}
                }
        
        latest = self.health_history[-1]
        
        return {
            "status": latest.status,
            "timestamp": latest.timestamp,
            "uptime_hours": latest.uptime_seconds / 3600,
            "system": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_available_mb": latest.memory_available_mb,
                "disk_usage_percent": latest.disk_usage_percent,
                "active_connections": latest.active_connections
            },
            "performance": {
                "error_rate": latest.error_rate,
                "avg_response_time": latest.api_response_time_avg
            },
            "apis": {name: asdict(metrics) for name, metrics in self.api_metrics.items()},
            "errors": self.error_collector.get_error_summary()
        }
    
    def get_health_report(self) -> str:
        """Genera un reporte de salud legible"""
        status = self.get_health_status()
        
        if status["status"] == "unknown":
            return "❓ Estado de salud desconocido"
        
        # Emoji basado en el estado
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️", 
            "critical": "🚨"
        }
        
        emoji = status_emoji.get(status["status"], "❓")
        uptime_hours = status["uptime_hours"]
        
        report = f"""{emoji} **Estado del Sistema: {status["status"].upper()}**

🕐 **Tiempo activo:** {uptime_hours:.1f} horas
💻 **CPU:** {status["system"]["cpu_percent"]:.1f}%
🧠 **Memoria:** {status["system"]["memory_percent"]:.1f}% ({status["system"]["memory_available_mb"]:.0f}MB disponible)
💾 **Disco:** {status["system"]["disk_usage_percent"]:.1f}%
🌐 **Conexiones activas:** {status["system"]["active_connections"]}

📊 **Rendimiento:**
• Tasa de error: {status["performance"]["error_rate"]:.1f}%
• Tiempo de respuesta promedio: {status["performance"]["avg_response_time"]:.2f}s

🔧 **APIs monitoreadas:** {len(status["apis"])}"""

        # Agregar información de errores si existen
        if status["errors"]["total_errors"] > 0:
            report += f"\n\n⚠️ **Errores recientes:** {status['errors']['total_errors']}"
        
        return report

# Instancia global del monitor
health_monitor = HealthMonitor()