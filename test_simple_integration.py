#!/usr/bin/env python3
"""
Test script simple para validar la integración básica del sistema de manejo de errores.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Agregar el directorio src al path de Python
sys.path.append(str(Path(__file__).parent))

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test de importaciones básicas"""
    logger.info("🔍 Testing basic imports...")
    
    try:
        from src.utils.error_handler import ValidationError, ProcessingError, APIError
        from src.utils.health_monitor import health_monitor
        from src.utils.graceful_degradation import degradation_manager
        logger.info("✅ Error handling utilities imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        return False

def test_health_monitor_basic():
    """Test básico del health monitor"""
    logger.info("🔍 Testing health monitor basic functionality...")
    
    try:
        from src.utils.health_monitor import health_monitor
        
        # Test básico de operaciones
        health_monitor.record_api_call("test_service", True, 0.5)
        health_monitor.record_api_call("test_service", False, 1.0, "Test error")
        
        # Test de reporte de estado
        status = health_monitor.get_health_status()
        if "status" in status:
            logger.info(f"✅ Health monitor working - Status: {status['status']}")
            return True
        else:
            logger.error("❌ Health monitor status incomplete")
            return False
            
    except Exception as e:
        logger.error(f"❌ Health monitor error: {str(e)}")
        return False

def test_graceful_degradation_basic():
    """Test básico de graceful degradation"""
    logger.info("🔍 Testing graceful degradation basic functionality...")
    
    try:
        from src.utils.graceful_degradation import degradation_manager, ServiceConfig
        
        # Test de configuración de servicio
        test_config = ServiceConfig(name="test_service", max_failures=2)
        degradation_manager.register_service(test_config)
        
        # Test de verificación de estado
        status = degradation_manager.get_service_status("test_service")
        if "status" in status:
            logger.info(f"✅ Graceful degradation working - Service status: {status['status']}")
            return True
        else:
            logger.error("❌ Graceful degradation status incomplete")
            return False
        
    except Exception as e:
        logger.error(f"❌ Graceful degradation error: {str(e)}")
        return False

def test_error_handling_decorators():
    """Test de decoradores de manejo de errores"""
    logger.info("🔍 Testing error handling decorators...")
    
    try:
        from src.utils.error_handler import retry_on_failure, safe_execute, ValidationError
        
        @retry_on_failure(max_attempts=2, delay=0.1)
        @safe_execute(operation="test_operation", log_errors=True, fallback_value={"status": "error", "message": "Operation failed"})
        def test_function(should_fail=False):
            if should_fail:
                raise ValidationError("Test error")
            return {"status": "success", "message": "Test passed"}
        
        # Test exitoso
        result = test_function(should_fail=False)
        if result and result.get("status") == "success":
            logger.info("✅ Decorators working - Success case")
        else:
            logger.error("❌ Decorators failed - Success case")
            return False
        
        # Test con error
        result = test_function(should_fail=True)
        if result and result.get("status") == "error":
            logger.info("✅ Decorators working - Error case handled")
        else:
            logger.error("❌ Decorators failed - Error case not handled")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling decorators error: {str(e)}")
        return False

def test_tools_basic():
    """Test básico de las herramientas"""
    logger.info("🔍 Testing tools basic functionality...")
    
    try:
        from src.tools.code_analyzer import CodeAnalyzer
        from src.tools.code_generator import CodeGenerator
        from src.tools.testing_debugging import TestingDebugger
        
        # Test CodeAnalyzer
        analyzer = CodeAnalyzer()
        result = analyzer.analyze_code("", "python")  # Debería dar error de validación
        if result.get("error_type") == "validation":
            logger.info("✅ CodeAnalyzer error handling working")
        else:
            logger.error("❌ CodeAnalyzer error handling failed")
            return False
        
        # Test CodeGenerator
        generator = CodeGenerator()
        result = generator.generate_code("", "python")  # Debería dar error de validación
        if result.get("error_type") == "validation":
            logger.info("✅ CodeGenerator error handling working")
        else:
            logger.error("❌ CodeGenerator error handling failed")
            return False
        
        # Test TestingDebugger
        debugger = TestingDebugger()
        result = debugger.run_unit_tests("", "python")  # Debería dar error de validación
        if result.get("error_type") == "validation":
            logger.info("✅ TestingDebugger error handling working")
        else:
            logger.error("❌ TestingDebugger error handling failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Tools basic test error: {str(e)}")
        return False

def main():
    """Función principal para ejecutar los tests simples"""
    logger.info("🚀 Starting simple integration tests...")
    
    tests = [
        ("Basic Imports", test_imports),
        ("Health Monitor Basic", test_health_monitor_basic),
        ("Graceful Degradation Basic", test_graceful_degradation_basic),
        ("Error Handling Decorators", test_error_handling_decorators),
        ("Tools Basic", test_tools_basic)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running: {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {str(e)}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    
    logger.info("\n" + "=" * 50)
    logger.info("📊 SIMPLE INTEGRATION TEST RESULTS")
    logger.info("=" * 50)
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        logger.info("🎉 Basic integration working correctly!")
        return 0
    else:
        logger.error("💥 Basic integration has issues!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)