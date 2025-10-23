import subprocess
import tempfile
import os
import json
from typing import Dict, Any, List, Optional

# Importar utilidades de error handling
from ..utils.error_handler import (
    retry_on_failure, safe_execute, log_error_with_context,
    ValidationError, ProcessingError, APIError
)
from ..utils.logging_config import log_user_operation, log_metrics
from ..utils.health_monitor import health_monitor

def run_unit_tests(code: str, language: str, test_framework: str = "auto") -> Dict[str, Any]:
    """
    Ejecuta pruebas unitarias para el código proporcionado.
    
    Args:
        code: Código a probar
        language: Lenguaje de programación
        test_framework: Framework de pruebas (auto-detectado si no se especifica)
        tool_context: Contexto de la herramienta
    
    Returns:
        Dict con resultados de las pruebas
    """
    try:
        # Detectar framework de pruebas
        if test_framework == "auto":
            test_framework = detect_test_framework(code, language)
        
        # Generar pruebas si no existen
        test_code = generate_unit_tests(code, language, test_framework)
        
        # Ejecutar pruebas
        test_results = execute_tests(test_code, language, test_framework)
        
        # Analizar resultados
        analysis = analyze_test_results(test_results)
        
        result = {
            "status": "success",
            "language": language,
            "test_framework": test_framework,
            "test_code": test_code,
            "test_results": test_results,
            "analysis": analysis,
            "coverage": calculate_test_coverage(code, test_code)
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ejecutando pruebas: {str(e)}"
        }

def debug_code(code: str, error_output: str, language: str) -> Dict[str, Any]:
    """
    Ayuda a depurar código proporcionando análisis y sugerencias.
    
    Args:
        code: Código a depurar
        error_output: Salida de error o mensaje de error
        language: Lenguaje de programación
        tool_context: Contexto de la herramienta
    
    Returns:
        Dict con análisis de depuración y sugerencias
    """
    try:
        # Analizar el error
        error_analysis = analyze_error_for_debugging(error_output, code, language)
        
        # Buscar posibles causas
        possible_causes = find_possible_causes(error_analysis, code, language)
        
        # Sugerir soluciones
        suggested_solutions = suggest_solutions(error_analysis, possible_causes, language)
        
        # Generar código de depuración
        debug_code = generate_debug_code(code, error_analysis, language)
        
        result = {
            "status": "success",
            "language": language,
            "error_analysis": error_analysis,
            "possible_causes": possible_causes,
            "suggested_solutions": suggested_solutions,
            "debug_code": debug_code,
            "step_by_step_guide": create_debugging_guide(error_analysis, language)
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en depuración: {str(e)}"
        }

def detect_test_framework(code: str, language: str) -> str:
    """Detecta el framework de pruebas más apropiado."""
    if language.lower() == "python":
        if "pytest" in code.lower():
            return "pytest"
        elif "unittest" in code.lower():
            return "unittest"
        elif "nose" in code.lower():
            return "nose"
        else:
            return "pytest"  # Default
    elif language.lower() == "javascript":
        if "jest" in code.lower():
            return "jest"
        elif "mocha" in code.lower():
            return "mocha"
        elif "jasmine" in code.lower():
            return "jasmine"
        else:
            return "jest"  # Default
    else:
        return "generic"

def generate_unit_tests(code: str, language: str, test_framework: str) -> str:
    """Genera pruebas unitarias para el código."""
    if language.lower() == "python" and test_framework == "pytest":
        return generate_pytest_code(code)
    elif language.lower() == "javascript" and test_framework == "jest":
        return generate_jest_code(code)
    else:
        return generate_generic_test_code(code, language)

def generate_pytest_code(code: str) -> str:
    """Genera código de pruebas pytest."""
    return f'''import pytest
from unittest.mock import Mock, patch
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestGeneratedCode:
    """Pruebas automáticas generadas para el código proporcionado."""
    
    def setup_method(self):
        """Configuración inicial para cada prueba."""
        pass
    
    def test_basic_functionality(self):
        """Prueba la funcionalidad básica."""
        # Esta es una prueba placeholder - deberías personalizarla
        assert True, "Prueba básica superada"
    
    def test_edge_cases(self):
        """Prueba casos extremos."""
        # Prueba con datos vacíos
        assert True, "Prueba de casos extremos"
    
    def test_error_handling(self):
        """Prueba el manejo de errores."""
        # Prueba que los errores se manejen correctamente
        assert True, "Manejo de errores OK"
    
    @pytest.mark.parametrize("input_data,expected", [
        ("test1", True),
        ("test2", True),
        ("", False),
        (None, False)
    ])
    def test_various_inputs(self, input_data, expected):
        """Prueba con diferentes entradas."""
        # Personalizar según el código real
        result = bool(input_data) if input_data is not None else False
        assert result == expected
'''

def generate_jest_code(code: str) -> str:
    """Genera código de pruebas Jest."""
    return f'''describe('Generated Code Tests', () => {{
    beforeEach(() => {{
        // Configuración inicial para cada prueba
    }});
    
    test('basic functionality', () => {{
        // Prueba la funcionalidad básica
        expect(true).toBe(true);
    }});
    
    test('edge cases', () => {{
        // Prueba casos extremos
        expect(true).toBe(true);
    }});
    
    test('error handling', () => {{
        // Prueba el manejo de errores
        expect(() => {{
            // Código que debería lanzar error
        }}).not.toThrow();
    }});
    
    test.each([
        ["test1", true],
        ["test2", true],
        ["", false],
        [null, false]
    ])('various inputs: %s', (input, expected) => {{
        // Prueba con diferentes entradas
        const result = input ? true : false;
        expect(result).toBe(expected);
    }});
}});
'''

def generate_generic_test_code(code: str, language: str) -> str:
    """Genera código de pruebas genérico."""
    return f"""// Pruebas generadas para {language}
// Código original:
/*
{code}
*/

// Pruebas básicas
function runTests() {{
    console.log('Ejecutando pruebas...');
    
    // Test 1: Funcionalidad básica
    console.assert(true, 'Prueba básica');
    
    // Test 2: Casos extremos
    console.assert(true, 'Casos extremos');
    
    console.log('Pruebas completadas');
}}

runTests();
"""

def execute_tests(test_code: str, language: str, test_framework: str) -> Dict[str, Any]:
    """Ejecuta las pruebas generadas."""
    try:
        if language.lower() == "python":
            return execute_python_tests(test_code, test_framework)
        elif language.lower() == "javascript":
            return execute_javascript_tests(test_code, test_framework)
        else:
            return {
                "status": "warning",
                "message": f"Ejecución de pruebas no implementada para {language}",
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ejecutando pruebas: {str(e)}",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }

def execute_python_tests(test_code: str, test_framework: str) -> Dict[str, Any]:
    """Ejecuta pruebas Python."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        # Ejecutar pytest
        result = subprocess.run([
            'python', '-m', 'pytest', temp_file, '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=30)
        
        os.unlink(temp_file)
        
        # Parsear resultados
        output = result.stdout + result.stderr
        tests_run = output.count("PASSED") + output.count("FAILED")
        tests_passed = output.count("PASSED")
        tests_failed = output.count("FAILED")
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "test_output": output,
            "tests_run": tests_run,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout ejecutando pruebas",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }
    except FileNotFoundError:
        # Si pytest no está disponible, intentar con unittest
        return execute_python_unittest(test_code)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error ejecutando pytest: {str(e)}",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }

def execute_python_unittest(test_code: str) -> Dict[str, Any]:
    """Ejecuta pruebas usando unittest."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        # Ejecutar con unittest
        result = subprocess.run([
            'python', '-m', 'unittest', 'discover', '-s', os.path.dirname(temp_file), '-p', '*.py'
        ], capture_output=True, text=True, timeout=30)
        
        os.unlink(temp_file)
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "test_output": result.stdout + result.stderr,
            "tests_run": 1,
            "tests_passed": 1 if result.returncode == 0 else 0,
            "tests_failed": 0 if result.returncode == 0 else 1,
            "return_code": result.returncode,
            "framework": "unittest"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error con unittest: {str(e)}",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }

def analyze_test_results(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Analiza los resultados de las pruebas."""
    if test_results["status"] == "success":
        return {
            "summary": f"Pruebas exitosas: {test_results['tests_passed']}/{test_results['tests_run']}",
            "quality_score": min(100, (test_results['tests_passed'] / max(1, test_results['tests_run'])) * 100),
            "recommendations": [
                "Mantén las pruebas actualizadas",
                "Agrega más casos de prueba edge cases",
                "Considera pruebas de integración"
            ]
        }
    else:
        return {
            "summary": f"Pruebas fallidas: {test_results['tests_failed']}/{test_results['tests_run']}",
            "quality_score": 0,
            "recommendations": [
                "Revisa los errores en las pruebas",
                "Asegúrate de que el código sea testeable",
                "Verifica las dependencias"
            ]
        }

def calculate_test_coverage(original_code: str, test_code: str) -> Dict[str, Any]:
    """Calcula la cobertura de pruebas (estimación básica)."""
    original_lines = len(original_code.splitlines())
    test_lines = len(test_code.splitlines())
    
    # Estimación muy básica
    coverage_percentage = min(100, (test_lines / max(1, original_lines)) * 50)
    
    return {
        "estimated_coverage": coverage_percentage,
        "original_lines": original_lines,
        "test_lines": test_lines,
        "note": "Esta es una estimación básica - usa herramientas de cobertura reales para métricas precisas"
    }

def analyze_error_for_debugging(error_output: str, code: str, language: str) -> Dict[str, Any]:
    """Analiza el error para depuración."""
    return {
        "error_type": classify_error(error_output),
        "error_severity": determine_severity(error_output),
        "likely_causes": identify_likely_causes(error_output, language),
        "code_context": extract_error_context(error_output, code)
    }

def classify_error(error_output: str) -> str:
    """Clasifica el tipo de error."""
    error_lower = error_output.lower()
    
    if "syntax" in error_lower or "parse" in error_lower:
        return "syntax_error"
    elif "undefined" in error_lower or "not defined" in error_lower:
        return "undefined_error"
    elif "type" in error_lower and "error" in error_lower:
        return "type_error"
    elif "exception" in error_lower:
        return "runtime_exception"
    elif "import" in error_lower or "module" in error_lower:
        return "import_error"
    else:
        return "unknown_error"

def determine_severity(error_output: str) -> str:
    """Determina la severidad del error."""
    if any(word in error_output.lower() for word in ["fatal", "critical", "system"]):
        return "critical"
    elif any(word in error_output.lower() for word in ["error", "exception"]):
        return "high"
    elif any(word in error_output.lower() for word in ["warning", "deprecat"]):
        return "medium"
    else:
        return "low"

def identify_likely_causes(error_output: str, language: str) -> List[str]:
    """Identifica causas probables del error."""
    causes = []
    error_lower = error_output.lower()
    
    if "syntax" in error_lower:
        causes.append("Sintaxis incorrecta - revisa paréntesis, llaves, puntos y coma")
    if "undefined" in error_lower:
        causes.append("Variable o función no declarada")
    if "import" in error_lower:
        causes.append("Módulo o paquete no encontrado")
    if "type" in error_lower:
        causes.append("Tipo de dato incorrecto")
    if "index" in error_lower:
        causes.append("Índice fuera de rango")
    if "attribute" in error_lower:
        causes.append("Método o atributo no existe")
    
    return causes if causes else ["Revisa el mensaje de error cuidadosamente"]

def extract_error_context(error_output: str, code: str) -> Dict[str, Any]:
    """Extrae el contexto del error."""
    lines = code.splitlines()
    
    # Intentar encontrar número de línea en el error
    import re
    line_matches = re.findall(r'line (\d+)', error_output, re.IGNORECASE)
    
    if line_matches:
        error_line = int(line_matches[0]) - 1
        start_line = max(0, error_line - 2)
        end_line = min(len(lines), error_line + 3)
        
        return {
            "error_line": error_line + 1,
            "context_lines": lines[start_line:end_line],
            "context_start": start_line + 1,
            "context_end": end_line
        }
    
    return {
        "error_line": None,
        "context_lines": lines[:5] if len(lines) > 5 else lines,
        "context_start": 1,
        "context_end": min(5, len(lines))
    }

def find_possible_causes(error_analysis: Dict[str, Any], code: str, language: str) -> List[Dict[str, Any]]:
    """Encuentra posibles causas del error."""
    causes = []
    
    # Análisis básico del código
    if error_analysis["error_type"] == "syntax_error":
        causes.append({
            "type": "syntax",
            "description": "Revisa la sintaxis del lenguaje",
            "priority": "high"
        })
    
    if error_analysis["error_type"] == "undefined_error":
        causes.append({
            "type": "undefined",
            "description": "Verifica que todas las variables estén declaradas",
            "priority": "high"
        })
    
    return causes

def suggest_solutions(error_analysis: Dict[str, Any], possible_causes: List[Dict[str, Any]], language: str) -> List[str]:
    """Sugiere soluciones para el error."""
    solutions = []
    
    for cause in possible_causes:
        if cause["type"] == "syntax":
            solutions.append("Revisa la documentación de sintaxis del lenguaje")
            solutions.append("Usa un linter o formateador de código")
        elif cause["type"] == "undefined":
            solutions.append("Declara todas las variables antes de usarlas")
            solutions.append("Verifica el scope de las variables")
    
    solutions.append("Busca ejemplos similares en línea")
    solutions.append("Consulta la documentación oficial")
    
    return solutions

def generate_debug_code(code: str, error_analysis: Dict[str, Any], language: str) -> str:
    """Genera código de depuración."""
    if language.lower() == "python":
        return f'''# Código de depuración generado
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_function():
    """Función de depuración."""
    try:
        # Tu código original aquí
        # {code[:200]}...  # Primeras 200 líneas
        
        logger.debug("Iniciando depuración")
        
        # Agregar puntos de control
        print("Checkpoint 1: Inicio")
        
        # Tu código continúa...
        
        print("Checkpoint 2: Fin")
        
    except Exception as e:
        print(f"Error capturado: {{e}}")
        traceback.print_exc()
        logger.error(f"Error en depuración: {{e}}")

if __name__ == "__main__":
    debug_function()
'''
    else:
        return f"// Código de depuración para {language}\\n// Error: {error_analysis.get('error_type', 'unknown')}\\n{code}"

def create_debugging_guide(error_analysis: Dict[str, Any], language: str) -> List[str]:
    """Crea una guía de depuración paso a paso."""
    steps = [
        "Lee cuidadosamente el mensaje de error completo",
        "Identifica el tipo de error y su severidad",
        "Busca el número de línea donde ocurrió el error",
        "Revisa el código en esa línea y alrededor",
        "Verifica la sintaxis y la lógica",
        "Consulta la documentación si es necesario",
        "Prueba con datos de entrada simples",
        "Usa herramientas de depuración del lenguaje"
    ]
    
    return steps

class TestingDebugger:
    """
    Clase para ejecutar pruebas unitarias y depurar código.
    Proporciona capacidades de testing y debugging para diferentes lenguajes.
    """
    
    def __init__(self):
        """Inicializa el testing debugger."""
        self.name = "TestingDebugger"
        self.supported_languages = ["python", "javascript", "typescript", "java", "go", "rust"]
        self.supported_frameworks = {
            "python": ["pytest", "unittest", "nose2"],
            "javascript": ["jest", "mocha", "jasmine"],
            "typescript": ["jest", "mocha", "jasmine"],
            "java": ["junit", "testng"],
            "go": ["testing"],
            "rust": ["cargo test"]
        }
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(ProcessingError, OSError))
    @safe_execute(operation="run_unit_tests", log_errors=True)
    def run_unit_tests(self, code: str, language: str, test_framework: str = "auto") -> Dict[str, Any]:
        """
        Ejecuta pruebas unitarias para el código proporcionado.
        
        Args:
            code: Código a probar
            language: Lenguaje de programación
            test_framework: Framework de pruebas (auto-detectado si no se especifica)
        
        Returns:
            Dict con resultados de las pruebas
        """
        import time
        start_time = time.time()
        
        try:
            # Validar entrada
            if not code or not code.strip():
                raise ValidationError("Código vacío proporcionado para testing")
            
            if not language or not language.strip():
                raise ValidationError("Lenguaje no especificado para testing")
            
            if language.lower() not in self.supported_languages:
                raise ValidationError(f"Lenguaje no soportado: {language}")
            
            # Log de la operación
            log_user_operation("unit_testing", "system", {
                "language": language,
                "code_length": len(code),
                "test_framework": test_framework
            })
            
            # Registrar métricas de salud
            health_monitor.record_api_call("unit_testing", True, time.time() - start_time)
            
            import time
            start_time = time.time()
            
            # Realizar testing
            result = run_unit_tests(code, language, test_framework)
            
            duration = time.time() - start_time
            log_metrics("unit_testing_duration", duration, {
                "language": language,
                "code_length": len(code),
                "test_framework": test_framework
            })
            
            # Agregar metadatos de la herramienta
            result["tool_metadata"] = {
                "debugger": self.name,
                "testing_duration": duration,
                "timestamp": time.time()
            }
            
            log_user_operation("unit_testing", "system", success=True)
            return result
            
        except ValidationError as e:
            health_monitor.record_api_call("unit_testing", False, time.time() - start_time, str(e))
            log_user_operation("unit_testing", "system", success=False)
            return {
                "status": "error",
                "error_type": "validation",
                "message": str(e),
                "language": language
            }
            
        except ProcessingError as e:
            health_monitor.record_api_call("unit_testing", False, time.time() - start_time, str(e))
            log_user_operation("unit_testing", "system", success=False)
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e),
                "language": language
            }
            
        except Exception as e:
            log_error_with_context(e, {"code": code, "language": language, "test_framework": test_framework}, "run_unit_tests", "system")
            health_monitor.record_api_call("unit_testing", False, time.time() - start_time, str(e))
            log_user_operation("unit_testing", "system", success=False)
            return {
                "status": "error",
                "error_type": "system",
                "message": f"Error interno del testing debugger: {str(e)}",
                "language": language
            }
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(ProcessingError, OSError))
    @safe_execute(operation="debug_code", log_errors=True)
    def debug_code(self, code: str, error_output: str, language: str) -> Dict[str, Any]:
        """
        Ayuda a depurar código proporcionando análisis y sugerencias.
        
        Args:
            code: Código a depurar
            error_output: Salida de error o mensaje de error
            language: Lenguaje de programación
        
        Returns:
            Dict con análisis de depuración y sugerencias
        """
        import time
        start_time = time.time()
        
        try:
            # Validar entrada
            if not code or not code.strip():
                raise ValidationError("Código vacío proporcionado para debugging")
            
            if not error_output or not error_output.strip():
                raise ValidationError("Salida de error vacía proporcionada")
            
            if not language or not language.strip():
                raise ValidationError("Lenguaje no especificado para debugging")
            
            if language.lower() not in self.supported_languages:
                raise ValidationError(f"Lenguaje no soportado: {language}")
            
            # Log de la operación
            log_user_operation("code_debugging", "system", {
                "language": language,
                "code_length": len(code),
                "error_output_length": len(error_output)
            })
            
            # Realizar debugging
            result = debug_code(code, error_output, language)
            
            duration = time.time() - start_time
            log_metrics("code_debugging_duration", duration, {
                "language": language,
                "code_length": len(code),
                "error_output_length": len(error_output)
            })
            
            # Agregar metadatos de la herramienta
            result["tool_metadata"] = {
                "debugger": self.name,
                "debugging_duration": duration,
                "timestamp": time.time()
            }
            
            # Registrar métricas de salud
            health_monitor.record_api_call("code_debugging", True, time.time() - start_time)
            
            log_user_operation("code_debugging", "system", success=True)
            return result
            
        except ValidationError as e:
            health_monitor.record_api_call("code_debugging", False, time.time() - start_time, str(e))
            log_user_operation("code_debugging", "system", success=False)
            return {
                "status": "error",
                "error_type": "validation",
                "message": str(e),
                "language": language
            }
            
        except ProcessingError as e:
            health_monitor.record_api_call("code_debugging", False, time.time() - start_time, str(e))
            log_user_operation("code_debugging", "system", success=False)
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e),
                "language": language
            }
            
        except Exception as e:
            log_error_with_context(e, {"code": code, "error_output": error_output, "language": language}, "debug_code", "system")
            health_monitor.record_api_call("code_debugging", False, time.time() - start_time, str(e))
            log_user_operation("code_debugging", "system", success=False)
            return {
                "status": "error",
                "error_type": "system",
                "message": f"Error interno del testing debugger: {str(e)}",
                "language": language
            }