import os
import sys
import logging
from pathlib import Path
import signal
import atexit
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Agregar el directorio src al path de Python
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.error_handler import setup_error_logging, log_error_with_context
from src.utils.logging_config import setup_logging, log_metrics
from src.utils.health_monitor import health_monitor
from src.utils.graceful_degradation import degradation_manager
from src.utils.config_validator import ConfigValidator
from src.agents.claude_agent import ClaudeProgrammingAgent
from src.slack.webhook_handler import SlackWebhookHandler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_signal_handlers():
    """Configura manejadores de señales para shutdown graceful"""
    def signal_handler(signum, frame):
        logger.info(f"🛑 Señal {signum} recibida, iniciando shutdown graceful...")
        # degradation_manager no tiene método initiate_graceful_shutdown
        # degradation_manager.initiate_graceful_shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def cleanup_on_exit():
    """Función de limpieza al salir"""
    logger.info("🧹 Ejecutando limpieza final...")
    health_monitor.stop_monitoring()
    # degradation_manager no tiene método cleanup, solo comentamos esta línea
    # degradation_manager.cleanup()

def main():
    """Función principal del agente Claude Programming"""
    try:
        print("=" * 80)
        print("🤖 CLAUDE PROGRAMMING AGENT - INICIANDO")
        print("=" * 80)
        
        # Configurar logging robusto
        print("📋 Configurando sistema de logging...")
        setup_logging()
        setup_error_logging()
        print("✅ Sistema de logging configurado correctamente")
        
        # Configurar manejadores de señales y limpieza
        print("🔧 Configurando manejadores de señales...")
        setup_signal_handlers()
        atexit.register(cleanup_on_exit)
        print("✅ Manejadores de señales configurados")
        
        logger = logging.getLogger(__name__)
        logger.info("🚀 Iniciando Claude Programming Agent...")
        
        # Validar configuración completa del sistema
        validation_result = ConfigValidator.validate_configuration()
        
        if not validation_result.is_valid:
            print(f"\n❌ CONFIGURACIÓN INVÁLIDA")
            print("💡 Errores encontrados:")
            for error in validation_result.missing_required:
                print(f"   - Variable requerida faltante: {error}")
            for error in validation_result.invalid_values:
                print(f"   - Valor inválido: {error}")
            print("\n💡 Por favor corrige estos errores antes de continuar")
            return 1
        
        # Mostrar advertencias si las hay
        if validation_result.warnings:
            print(f"\n⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
            for warning in validation_result.warnings:
                print(f"   - {warning}")
            print()
        
        bigquery_configured = validation_result.bigquery_available
        
        # Inicializar monitoreo de salud
        print("\n💊 INICIALIZANDO MONITOREO DE SALUD")
        print("-" * 50)
        try:
            health_monitor.start_monitoring()
            print("✅ Monitoreo de salud iniciado correctamente")
            logger.info("✅ Monitoreo de salud iniciado")
            log_metrics("health_monitoring_startup", 1, {"status": "success"})
        except Exception as e:
            print(f"⚠️ Error iniciando monitoreo de salud: {str(e)}")
            logger.warning(f"⚠️ Error iniciando monitoreo de salud: {str(e)}")
            log_error_with_context(e, {}, "health_monitoring_startup", "system")
            log_metrics("health_monitoring_startup", 0, {"status": "failed"})
        
        # Inicializar degradación graceful
        print("\n🛡️ INICIALIZANDO SISTEMA DE DEGRADACIÓN GRACEFUL")
        print("-" * 50)
        try:
            degradation_manager.initialize()
            print("✅ Sistema de degradación graceful inicializado")
            logger.info("✅ Sistema de degradación graceful inicializado")
            log_metrics("graceful_degradation_startup", 1, {"status": "success"})
        except Exception as e:
            print(f"⚠️ Error iniciando degradación graceful: {str(e)}")
            logger.warning(f"⚠️ Error iniciando degradación graceful: {str(e)}")
            log_error_with_context(e, {}, "graceful_degradation_startup", "system")
            log_metrics("graceful_degradation_startup", 0, {"status": "failed"})
        
        # Inicializar agente Claude con manejo de errores
        print("\n🤖 INICIALIZANDO AGENTE CLAUDE")
        print("-" * 50)
        try:
            print("🔄 Conectando con Anthropic API...")
            agent = ClaudeProgrammingAgent()
            print("✅ Agente Claude inicializado correctamente")
            logger.info("✅ Agente Claude inicializado correctamente")
            log_metrics("agent_initialization", 1, {"status": "success"})
            health_monitor.record_api_call("agent_initialization", True, 0)
        except Exception as e:
            print(f"❌ Error inicializando agente Claude: {str(e)}")
            logger.error(f"❌ Error inicializando agente Claude: {str(e)}")
            log_error_with_context(e, {}, "agent_initialization", "system")
            log_metrics("agent_initialization", 0, {"status": "failed"})
            health_monitor.record_api_call("agent_initialization", False, 0, str(e))
            
            # Intentar modo degradado
            if degradation_manager.can_operate_in_degraded_mode():
                print("⚠️ Operando en modo degradado sin agente Claude completo")
                logger.warning("⚠️ Operando en modo degradado sin agente Claude completo")
                agent = None
            else:
                print("💥 No se puede operar sin agente Claude. Terminando...")
                return 1
        
        # Inicializar manejador de webhooks Slack con manejo de errores
        print("\n💬 INICIALIZANDO INTEGRACIÓN CON SLACK")
        print("-" * 50)
        try:
            print("🔄 Configurando webhooks de Slack...")
            slack_handler = SlackWebhookHandler(agent)
            print("✅ Manejador de webhooks Slack inicializado correctamente")
            logger.info("✅ Manejador de webhooks Slack inicializado correctamente")
            log_metrics("slack_initialization", 1, {"status": "success"})
            health_monitor.record_api_call("slack_initialization", True, 0)
        except Exception as e:
            print(f"❌ Error inicializando manejador de webhooks Slack: {str(e)}")
            logger.error(f"❌ Error inicializando manejador de webhooks Slack: {str(e)}")
            log_error_with_context(e, {}, "slack_initialization", "system")
            log_metrics("slack_initialization", 0, {"status": "failed"})
            health_monitor.record_api_call("slack_initialization", False, 0, str(e))
            print("💥 No se puede operar sin integración de Slack. Terminando...")
            return 1
        
        # Iniciar el servidor HTTP con manejo de errores
        print("\n🌐 INICIANDO SERVIDOR HTTP")
        print("-" * 50)
        try:
            # Obtener puerto del entorno o usar 8080 por defecto
            port = int(os.getenv("WEBHOOK_PORT", "8080"))
            print(f"🔄 Iniciando servidor HTTP en puerto {port}...")
            logger.info("🔄 Iniciando servidor HTTP para webhooks de Slack...")
            
            # Registrar el estado de la aplicación como saludable
            health_monitor.record_api_call("application_startup", True, 0)
            log_metrics("application_health", 1, {"status": "healthy"})
            
            print("=" * 80)
            print("🎉 CLAUDE PROGRAMMING AGENT INICIADO EXITOSAMENTE")
            print("=" * 80)
            print(f"🌐 Servidor HTTP ejecutándose en puerto: {port}")
            print("💬 Bot de Slack listo para recibir mensajes")
            if bigquery_configured:
                print("🗄️ Memoria persistente activa (BigQuery)")
            else:
                print("⚠️ Memoria persistente deshabilitada")
            print("🔍 Monitoreo de salud activo")
            print("🛡️ Sistema de degradación graceful activo")
            print("=" * 80)
            print("📝 Para detener el bot, presiona Ctrl+C")
            print("=" * 80)
            
            slack_handler.start(host="0.0.0.0", port=port)
            log_metrics("bot_startup", 1, {"status": "success"})
            health_monitor.record_api_call("bot_startup", True, 0)
            
        except Exception as e:
            print(f"❌ Error iniciando servidor HTTP de Slack: {str(e)}")
            logger.error(f"❌ Error iniciando servidor HTTP de Slack: {str(e)}")
            log_error_with_context(e, {}, "bot_startup", "system")
            log_metrics("bot_startup", 0, {"status": "failed"})
            health_monitor.record_api_call("bot_startup", False, 0, str(e))
            print("💥 No se puede iniciar el servidor. Terminando...")
            return 1
            
    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("🛑 DETENIENDO CLAUDE PROGRAMMING AGENT")
        print("=" * 80)
        print("👋 Agente detenido por el usuario")
        logger.info("🛑 Agente detenido por el usuario")
        log_metrics("shutdown", 1, {"reason": "user_interrupt"})
        health_monitor.record_api_call("shutdown", True, 0)
        print("✅ Shutdown completado correctamente")
        return 0
    except Exception as e:
        print("\n" + "=" * 80)
        print("💥 ERROR FATAL")
        print("=" * 80)
        print(f"❌ Error fatal durante el inicio: {str(e)}")
        print("💡 Revisa la configuración y los logs para más detalles")
        print("=" * 80)
        logger.error(f"💥 Error fatal durante el inicio: {str(e)}")
        log_error_with_context(e, {}, "fatal_startup", "system")
        log_metrics("fatal_error", 1, {"error_type": type(e).__name__})
        health_monitor.record_api_call("fatal_startup", False, 0, str(e))
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)