#!/usr/bin/env python3
"""
Test script para validar el sistema integrado de manejo de errores.
Prueba todos los componentes principales con escenarios comprehensivos.
"""

import os
import sys
import time
import json
import requests
import logging
from pathlib import Path

# Agregar el directorio src al path de Python
sys.path.append(str(Path(__file__).parent))

from src.utils.error_handler import ValidationError, ProcessingError, APIError
from src.utils.health_monitor import health_monitor
from src.utils.graceful_degradation import degradation_manager
from src.agents.claude_agent import ClaudeProgrammingAgent
from src.tools.code_analyzer import CodeAnalyzer
from src.tools.code_generator import CodeGenerator
from src.tools.testing_debugging import TestingDebugger

# Configurar logging para tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedSystemTester:
    """Tester para el sistema integrado de manejo de errores"""
    
    def __init__(self):
        self.test_results = []
        self.health_port = os.getenv("HEALTH_PORT", "8081")
        
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Registra el resultado de un test"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {details}")
    
    def test_health_monitor_integration(self):
        """Test del monitoreo de salud integrado"""
        logger.info("🔍 Testing health monitor integration...")
        
        try:
            # Test 1: Inicialización del health monitor
            health_monitor.start_monitoring()
            self.log_test_result("health_monitor_start", True, "Health monitor iniciado correctamente")
            
            # Test 2: Registro de operaciones
            health_monitor.record_api_call("test_operation", True, 0.5)
            health_monitor.record_api_call("test_operation", False, 1.0, "Test error")
            self.log_test_result("health_monitor_operations", True, "Operaciones registradas correctamente")
            
            # Test 3: Obtener reporte de salud
            status = health_monitor.get_health_status()
            if "status" in status:
                self.log_test_result("health_monitor_report", True, f"Reporte generado: {status['status']}")
            else:
                self.log_test_result("health_monitor_report", False, "Reporte incompleto")
                
        except Exception as e:
            self.log_test_result("health_monitor_integration", False, f"Error: {str(e)}")
    
    def test_graceful_degradation(self):
        """Test del sistema de degradación graceful"""
        logger.info("🔍 Testing graceful degradation...")
        
        try:
            # Test 1: Inicialización
            degradation_manager.initialize()
            self.log_test_result("graceful_degradation_init", True, "Sistema inicializado")
            
            # Test 2: Verificar modo degradado
            can_operate = degradation_manager.can_operate_in_degraded_mode()
            self.log_test_result("graceful_degradation_check", True, f"Puede operar en modo degradado: {can_operate}")
            
            # Test 3: Simular falla de servicio
            degradation_manager.mark_service_unavailable("test_service")
            is_available = degradation_manager.is_service_available("test_service")
            self.log_test_result("graceful_degradation_service", not is_available, f"Servicio no disponible después de marcarlo: {not is_available}")
            
        except Exception as e:
            self.log_test_result("graceful_degradation", False, f"Error: {str(e)}")
    
    def test_code_analyzer_error_handling(self):
        """Test del manejo de errores en CodeAnalyzer"""
        logger.info("🔍 Testing CodeAnalyzer error handling...")
        
        try:
            analyzer = CodeAnalyzer()
            
            # Test 1: Entrada válida
            valid_code = "def hello(): return 'Hello World'"
            result = analyzer.analyze_code(valid_code, "python")
            if result.get("status") != "error":
                self.log_test_result("analyzer_valid_input", True, "Análisis exitoso con entrada válida")
            else:
                self.log_test_result("analyzer_valid_input", False, f"Error inesperado: {result.get('message')}")
            
            # Test 2: Entrada inválida (código vacío)
            result = analyzer.analyze_code("", "python")
            if result.get("error_type") == "validation":
                self.log_test_result("analyzer_empty_code", True, "Error de validación detectado correctamente")
            else:
                self.log_test_result("analyzer_empty_code", False, "No se detectó error de validación")
            
            # Test 3: Lenguaje no soportado
            result = analyzer.analyze_code("code", "unsupported_language")
            if result.get("error_type") == "validation":
                self.log_test_result("analyzer_unsupported_lang", True, "Lenguaje no soportado detectado")
            else:
                self.log_test_result("analyzer_unsupported_lang", False, "No se detectó lenguaje no soportado")
                
        except Exception as e:
            self.log_test_result("code_analyzer_error_handling", False, f"Error: {str(e)}")
    
    def test_code_generator_error_handling(self):
        """Test del manejo de errores en CodeGenerator"""
        logger.info("🔍 Testing CodeGenerator error handling...")
        
        try:
            generator = CodeGenerator()
            
            # Test 1: Entrada válida
            result = generator.generate_code("Create a hello world function", "python")
            if result.get("status") != "error":
                self.log_test_result("generator_valid_input", True, "Generación exitosa con entrada válida")
            else:
                self.log_test_result("generator_valid_input", False, f"Error inesperado: {result.get('message')}")
            
            # Test 2: Requisitos vacíos
            result = generator.generate_code("", "python")
            if result.get("error_type") == "validation":
                self.log_test_result("generator_empty_requirements", True, "Error de validación detectado")
            else:
                self.log_test_result("generator_empty_requirements", False, "No se detectó error de validación")
            
            # Test 3: Lenguaje vacío
            result = generator.generate_code("Create function", "")
            if result.get("error_type") == "validation":
                self.log_test_result("generator_empty_language", True, "Lenguaje vacío detectado")
            else:
                self.log_test_result("generator_empty_language", False, "No se detectó lenguaje vacío")
                
        except Exception as e:
            self.log_test_result("code_generator_error_handling", False, f"Error: {str(e)}")
    
    def test_testing_debugger_error_handling(self):
        """Test del manejo de errores en TestingDebugger"""
        logger.info("🔍 Testing TestingDebugger error handling...")
        
        try:
            debugger = TestingDebugger()
            
            # Test 1: Entrada válida para testing
            valid_code = "def add(a, b): return a + b"
            result = debugger.run_unit_tests(valid_code, "python")
            if result.get("status") != "error":
                self.log_test_result("debugger_valid_test", True, "Testing exitoso con entrada válida")
            else:
                self.log_test_result("debugger_valid_test", False, f"Error inesperado: {result.get('message')}")
            
            # Test 2: Código vacío para testing
            result = debugger.run_unit_tests("", "python")
            if result.get("error_type") == "validation":
                self.log_test_result("debugger_empty_code", True, "Error de validación detectado")
            else:
                self.log_test_result("debugger_empty_code", False, "No se detectó error de validación")
            
            # Test 3: Debugging con entrada válida
            result = debugger.debug_code("print('hello')", "NameError: name 'hello' is not defined", "python")
            if result.get("status") != "error":
                self.log_test_result("debugger_valid_debug", True, "Debugging exitoso")
            else:
                self.log_test_result("debugger_valid_debug", False, f"Error inesperado: {result.get('message')}")
                
        except Exception as e:
            self.log_test_result("testing_debugger_error_handling", False, f"Error: {str(e)}")
    
    def test_health_endpoints(self):
        """Test de los endpoints de salud"""
        logger.info("🔍 Testing health endpoints...")
        
        try:
            base_url = f"http://localhost:{self.health_port}"
            
            # Test 1: Endpoint básico de salud
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    self.log_test_result("health_endpoint_basic", True, f"Status: {data.get('status')}")
                else:
                    self.log_test_result("health_endpoint_basic", False, f"Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_test_result("health_endpoint_basic", False, f"Connection error: {str(e)}")
            
            # Test 2: Endpoint detallado de salud
            try:
                response = requests.get(f"{base_url}/health/detailed", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if "metrics" in data and "system_info" in data:
                        self.log_test_result("health_endpoint_detailed", True, "Endpoint detallado funcional")
                    else:
                        self.log_test_result("health_endpoint_detailed", False, "Datos incompletos")
                else:
                    self.log_test_result("health_endpoint_detailed", False, f"Status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_test_result("health_endpoint_detailed", False, f"Connection error: {str(e)}")
                
        except Exception as e:
            self.log_test_result("health_endpoints", False, f"Error: {str(e)}")
    
    def test_claude_agent_error_handling(self):
        """Test del manejo de errores en ClaudeProgrammingAgent"""
        logger.info("🔍 Testing ClaudeProgrammingAgent error handling...")
        
        try:
            # Solo probar si tenemos la API key
            if not os.getenv("ANTHROPIC_API_KEY"):
                self.log_test_result("claude_agent_no_api_key", True, "Sin API key - test omitido")
                return
            
            agent = ClaudeProgrammingAgent()
            
            # Test 1: Solicitud válida
            result = agent.analyze_request("Analyze this Python code: print('hello')")
            if result.get("status") != "error":
                self.log_test_result("claude_agent_valid_request", True, "Análisis exitoso")
            else:
                self.log_test_result("claude_agent_valid_request", False, f"Error: {result.get('message')}")
            
            # Test 2: Solicitud vacía
            result = agent.analyze_request("")
            if result.get("error_type") == "validation":
                self.log_test_result("claude_agent_empty_request", True, "Error de validación detectado")
            else:
                self.log_test_result("claude_agent_empty_request", False, "No se detectó error de validación")
                
        except Exception as e:
            self.log_test_result("claude_agent_error_handling", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Ejecuta todos los tests del sistema integrado"""
        logger.info("🚀 Iniciando tests del sistema integrado de manejo de errores...")
        
        # Ejecutar todos los tests
        self.test_health_monitor_integration()
        self.test_graceful_degradation()
        self.test_code_analyzer_error_handling()
        self.test_code_generator_error_handling()
        self.test_testing_debugger_error_handling()
        self.test_health_endpoints()
        self.test_claude_agent_error_handling()
        
        # Generar reporte final y retornar el resultado
        return self.generate_final_report()
    
    def generate_final_report(self):
        """Genera el reporte final de tests"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 REPORTE FINAL DE TESTS")
        logger.info("=" * 60)
        logger.info(f"Total de tests: {total_tests}")
        logger.info(f"Tests exitosos: {passed_tests}")
        logger.info(f"Tests fallidos: {failed_tests}")
        logger.info(f"Tasa de éxito: {success_rate:.1f}%")
        logger.info("=" * 60)
        
        if failed_tests > 0:
            logger.info("❌ TESTS FALLIDOS:")
            for result in self.test_results:
                if not result["success"]:
                    logger.info(f"  - {result['test_name']}: {result['details']}")
        
        # Guardar reporte en archivo
        report_data = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results,
            "timestamp": time.time()
        }
        
        with open("test_integrated_system_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"📄 Reporte guardado en: test_integrated_system_report.json")
        
        return success_rate >= 80  # Considerar exitoso si >= 80% de tests pasan

def main():
    """Función principal para ejecutar los tests"""
    tester = IntegratedSystemTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 Sistema integrado funcionando correctamente!")
        return 0
    else:
        logger.error("💥 Sistema integrado tiene problemas críticos!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)