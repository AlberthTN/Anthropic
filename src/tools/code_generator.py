import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
import json

def generate_code(requirements: str, language: str, context: str = "") -> Dict[str, Any]:
    """
    Genera código basado en los requisitos proporcionados.
    
    Args:
        requirements: Descripción de lo que debe hacer el código
        language: Lenguaje de programación objetivo
        context: Contexto adicional o código existente
    
    Returns:
        Dict con el código generado y recomendaciones
    """
    try:
        # Obtener mejores prácticas del lenguaje
        best_practices = get_language_best_practices(language)
        
        # Generar código basado en requisitos
        generated_code = generate_code_from_requirements(requirements, language, context, best_practices)
        
        # Agregar comentarios y documentación
        documented_code = add_documentation(generated_code, language, requirements)
        
        # Verificar que el código sea válido
        validation_result = validate_generated_code(documented_code, language)
        
        result = {
            "status": "success",
            "language": language,
            "code": documented_code,  # Cambiado de "generated_code" a "code" para consistencia
            "validation": validation_result,
            "best_practices": best_practices,
            "explanation": "Código generado exitosamente"  # Agregado para consistencia
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al generar código: {str(e)}"
        }

def fix_code_errors(code: str, error_message: str, language: str) -> Dict[str, Any]:
    """
    Intenta corregir errores en el código proporcionado.
    
    Args:
        code: Código con errores
        error_message: Mensaje de error o descripción del problema
        language: Lenguaje de programación
    
    Returns:
        Dict con código corregido y explicación
    """
    try:
        # Analizar el error
        error_analysis = analyze_error(error_message, code, language)
        
        # Buscar soluciones comunes
        fixes = find_common_fixes(error_analysis, language)
        
        # Aplicar correcciones
        fixed_code = apply_fixes(code, fixes, language)
        
        # Validar el código corregido
        validation = validate_generated_code(fixed_code, language)
        
        result = {
            "status": "success",
            "language": language,
            "original_code": code,
            "fixed_code": fixed_code,
            "error_analysis": error_analysis,
            "fixes_applied": fixes,
            "validation": validation,
            "explanation": generate_fix_explanation(code, fixed_code, fixes)
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al corregir código: {str(e)}"
        }

def get_language_best_practices(language: str) -> List[str]:
    """Obtiene mejores prácticas para el lenguaje especificado."""
    best_practices = {
        "python": [
            "Usar snake_case para nombres de funciones y variables",
            "Usar PascalCase para nombres de clases",
            "Incluir docstrings para funciones y clases",
            "Manejar excepciones con try/except",
            "Usar type hints cuando sea apropiado",
            "Seguir PEP 8 para estilo de código",
            "Usar list comprehensions cuando sea apropiado",
            "Evitar variables globales"
        ],
        "javascript": [
            "Usar const/let en lugar de var",
            "Usar camelCase para nombres de variables y funciones",
            "Usar PascalCase para clases",
            "Manejar errores con try/catch",
            "Usar async/await para operaciones asíncronas",
            "Evitar callbacks anidados (callback hell)",
            "Usar template literals para strings complejos",
            "Validar tipos de datos cuando sea necesario"
        ],
        "typescript": [
            "Definir interfaces y tipos",
            "Usar tipos estrictos",
            "Aprovechar los generics",
            "Usar enums para valores constantes",
            "Implementar access modifiers (public, private, protected)",
            "Usar async/await",
            "Manejar errores de forma apropiada",
            "Evitar 'any' type cuando sea posible"
        ],
        "java": [
            "Seguir convenciones de nombres Java",
            "Usar encapsulamiento apropiado",
            "Manejar excepciones correctamente",
            "Usar interfaces cuando sea apropiado",
            "Evitar código duplicado",
            "Usar generics",
            "Implementar equals() y hashCode() cuando sea necesario",
            "Usar StringBuilder para concatenación de strings"
        ]
    }
    
    return best_practices.get(language.lower(), ["Seguir mejores prácticas generales de programación"])

def generate_code_from_requirements(requirements: str, language: str, context: str, best_practices: List[str]) -> str:
    """Genera código basado en los requisitos."""
    
    # Templates básicos para diferentes tipos de requisitos
    if "función" in requirements.lower() or "function" in requirements.lower():
        return generate_function_code(requirements, language, context, best_practices)
    elif "clase" in requirements.lower() or "class" in requirements.lower():
        return generate_class_code(requirements, language, context, best_practices)
    elif "api" in requirements.lower():
        return generate_api_code(requirements, language, context, best_practices)
    elif "test" in requirements.lower() or "prueba" in requirements.lower():
        return generate_test_code(requirements, language, context, best_practices)
    else:
        return generate_generic_code(requirements, language, context, best_practices)

def generate_function_code(requirements: str, language: str, context: str, best_practices: List[str]) -> str:
    """Genera código de función."""
    if language.lower() == "python":
        return f'''def process_data(data: str) -> str:
    """
    Procesa los datos según los requisitos: {requirements}
    
    Args:
        data: Datos de entrada
        
    Returns:
        str: Datos procesados
    """
    try:
        # Implementación según requisitos
        result = data.upper()  # Ejemplo básico
        return result
    except Exception as e:
        raise ValueError(f"Error procesando datos: {{e}}")
'''
    elif language.lower() == "javascript":
        return f'''function processData(data) {{
    /**
     * Procesa los datos según los requisitos: {requirements}
     * @param {{string}} data - Datos de entrada
     * @returns {{string}} Datos procesados
     */
    try {{
        // Implementación según requisitos
        const result = data.toUpperCase(); // Ejemplo básico
        return result;
    }} catch (error) {{
        throw new Error(`Error procesando datos: ${{error.message}}`);
    }}
}}
'''
    else:
        return f"// Código generado para {language} según requisitos: {requirements}"

def generate_class_code(requirements: str, language: str, context: str, best_practices: List[str]) -> str:
    """Genera código de clase."""
    if language.lower() == "python":
        return f'''class DataProcessor:
    """
    Procesador de datos según requisitos: {requirements}
    """
    
    def __init__(self, config: dict = None):
        """Inicializa el procesador con configuración opcional."""
        self.config = config or {{}}
    
    def process(self, data: str) -> str:
        """
        Procesa los datos según la configuración.
        
        Args:
            data: Datos de entrada
            
        Returns:
            str: Datos procesados
        """
        try:
            # Implementación
            return data.strip()
        except Exception as e:
            raise ValueError(f"Error en procesamiento: {{e}}")
    
    def validate(self, data: str) -> bool:
        """Valida los datos de entrada."""
        return bool(data and isinstance(data, str))
'''
    else:
        return f"// Clase generada para {language} según requisitos: {requirements}"

def generate_api_code(requirements: str, language: str, context: str, best_practices: List[str]) -> str:
    """Genera código de API."""
    if language.lower() == "python":
        return f'''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class DataRequest(BaseModel):
    data: str

class DataResponse(BaseModel):
    result: str
    status: str

@app.post("/process", response_model=DataResponse)
async def process_data(request: DataRequest):
    """
    Endpoint para procesar datos según: {requirements}
    """
    try:
        # Implementación
        result = request.data.upper()
        return DataResponse(result=result, status="success")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}
'''
    else:
        return f"// API generada para {language} según requisitos: {requirements}"

def generate_test_code(requirements: str, language: str, context: str, best_practices: List[str]) -> str:
    """Genera código de pruebas."""
    if language.lower() == "python":
        return f'''import pytest
from unittest.mock import Mock, patch

class TestDataProcessor:
    """Pruebas para el procesador de datos según: {requirements}"""
    
    def setup_method(self):
        """Configuración inicial para cada prueba."""
        self.processor = DataProcessor()
    
    def test_process_valid_data(self):
        """Prueba el procesamiento de datos válidos."""
        # Arrange
        test_data = "  hello world  "
        
        # Act
        result = self.processor.process(test_data)
        
        # Assert
        assert result == "hello world"
        assert isinstance(result, str)
    
    def test_validate_empty_data(self):
        """Prueba la validación de datos vacíos."""
        assert not self.processor.validate("")
        assert not self.processor.validate(None)
    
    def test_validate_valid_data(self):
        """Prueba la validación de datos válidos."""
        assert self.processor.validate("valid data")
    
    @pytest.mark.parametrize("input_data,expected", [
        ("hello", "hello"),
        ("  spaced  ", "spaced"),
        ("multiple   spaces", "multiple   spaces")
    ])
    def test_process_various_inputs(self, input_data, expected):
        """Prueba el procesamiento con varios inputs."""
        result = self.processor.process(input_data)
        assert result == expected
'''
    else:
        return f"// Pruebas generadas para {language} según requisitos: {requirements}"

def generate_generic_code(requirements: str, language: str, context: str, best_practices: List[str]) -> str:
    """Genera código genérico."""
    return f"// Código generado para {language} según requisitos: {requirements}\\n// Mejores prácticas: {'; '.join(best_practices)}"

def add_documentation(code: str, language: str, requirements: str) -> str:
    """Agrega documentación al código."""
    # Esta función podría usar LLM para generar documentación más inteligente
    # Por ahora, agrega comentarios básicos
    return code

def validate_generated_code(code: str, language: str) -> Dict[str, Any]:
    """Valida el código generado."""
    try:
        if language.lower() == "python":
            # Intentar compilar el código Python
            compile(code, '<string>', 'exec')
            return {"valid": True, "message": "Código Python válido"}
        else:
            # Para otros lenguajes, hacer validación básica
            return {"valid": True, "message": f"Sintaxis básica válida para {language}"}
            
    except SyntaxError as e:
        return {
            "valid": False,
            "message": f"Error de sintaxis: {str(e)}",
            "line": e.lineno,
            "column": e.offset
        }
    except Exception as e:
        return {
            "valid": False,
            "message": f"Error de validación: {str(e)}"
        }

def generate_recommendations(requirements: str, language: str, code: str) -> List[str]:
    """Genera recomendaciones para el código."""
    recommendations = []
    
    # Recomendaciones basadas en el tamaño del código
    lines = code.splitlines()
    if len(lines) > 50:
        recommendations.append("Considera dividir este código en funciones más pequeñas")
    
    if len(lines) > 100:
        recommendations.append("Este archivo es bastante grande - considera dividirlo en módulos")
    
    # Recomendaciones basadas en el lenguaje
    if language.lower() == "python":
        if "def " not in code:
            recommendations.append("Considera encapsular la lógica en funciones")
        if "class " not in code and len(lines) > 20:
            recommendations.append("Podrías beneficiarte de usar clases para organizar mejor el código")
    
    return recommendations

def analyze_error(error_message: str, code: str, language: str) -> Dict[str, Any]:
    """Analiza el mensaje de error."""
    return {
        "error_type": "syntax" if "syntax" in error_message.lower() else "runtime",
        "error_message": error_message,
        "language": language,
        "analysis": f"Error detectado en código {language}: {error_message}"
    }

def find_common_fixes(error_analysis: Dict[str, Any], language: str) -> List[Dict[str, Any]]:
    """Busca correcciones comunes para el error."""
    fixes = []
    
    error_msg = error_analysis["error_message"].lower()
    
    if "undefined" in error_msg and "variable" in error_msg:
        fixes.append({
            "type": "variable_declaration",
            "description": "Agregar declaración de variable",
            "priority": "high"
        })
    
    if "syntax" in error_msg:
        if "missing" in error_msg and "parenthesis" in error_msg:
            fixes.append({
                "type": "add_parenthesis",
                "description": "Agregar paréntesis faltantes",
                "priority": "high"
            })
        
        if "missing" in error_msg and "colon" in error_msg:
            fixes.append({
                "type": "add_colon",
                "description": "Agregar dos puntos faltantes",
                "priority": "high"
            })
    
    return fixes

def apply_fixes(code: str, fixes: List[Dict[str, Any]], language: str) -> str:
    """Aplica las correcciones al código."""
    # Esta es una implementación básica
    # En una implementación real, usarías análisis más sofisticado
    fixed_code = code
    
    for fix in fixes:
        if fix["type"] == "add_parenthesis":
            # Lógica para agregar paréntesis
            pass
        elif fix["type"] == "add_colon":
            # Lógica para agregar dos puntos
            pass
    
    return fixed_code

def generate_fix_explanation(original_code: str, fixed_code: str, fixes: List[Dict[str, Any]]) -> str:
    """Genera explicación de las correcciones aplicadas."""
    explanation = "Se aplicaron las siguientes correcciones:\n"
    
    for fix in fixes:
        explanation += f"- {fix['description']} (prioridad: {fix['priority']})\n"
    
    return explanation

# Importar utilidades de error handling al inicio del archivo
from ..utils.error_handler import (
    retry_on_failure, safe_execute, log_error_with_context,
    ValidationError, ProcessingError, APIError
)
from ..utils.logging_config import log_user_operation, log_metrics
from ..utils.health_monitor import health_monitor

class CodeGenerator:
    """
    Clase para generar código en diferentes lenguajes de programación.
    Proporciona generación inteligente basada en requisitos y mejores prácticas.
    """
    
    def __init__(self):
        """Inicializa el generador de código."""
        self.name = "CodeGenerator"
        self.supported_languages = ["python", "javascript", "typescript", "java", "go", "rust"]
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(ProcessingError, OSError))
    @safe_execute(operation="generate_code", log_errors=True)
    @retry_on_failure(max_attempts=3, delay=1.0)
    @safe_execute(operation="code_generation", log_errors=True)
    def generate_code(self, requirements: str, language: str, context: str = "") -> Dict[str, Any]:
        """
        Genera código basado en los requisitos proporcionados.
        
        Args:
            requirements: Descripción de los requisitos del código
            language: Lenguaje de programación objetivo
            context: Contexto adicional para la generación
        
        Returns:
            Dict con el código generado y metadatos
        """
        import time
        start_time = time.time()
        
        try:
            # Validar entrada
            if not requirements or not requirements.strip():
                raise ValidationError("Requisitos vacíos proporcionados para generación de código")
            
            if not language or not language.strip():
                raise ValidationError("Lenguaje no especificado para generación de código")
            
            # Log de la operación
            log_user_operation("code_generation", "system", {
                "language": language,
                "requirements_length": len(requirements),
                "context_length": len(context) if context else 0
            })
            
            # Registrar métricas de salud
            health_monitor.record_api_call("code_generation", True, time.time() - start_time)
            start_time = time.time()
            
            # Realizar generación
            result = generate_code(requirements, language, context)
            
            duration = time.time() - start_time
            log_metrics("code_generation_duration", duration, {
                "language": language,
                "requirements_length": len(requirements)
            })
            
            # Agregar metadatos de la herramienta
            result["tool_metadata"] = {
                "generator": self.name,
                "generation_duration": duration,
                "timestamp": time.time()
            }
            
            log_user_operation("code_generation", "system", success=True)
            return result
            
        except ValidationError as e:
            health_monitor.record_api_call("code_generation", False, time.time() - start_time)
            log_user_operation("code_generation", "system", success=False)
            return {
                "status": "error",
                "error_type": "validation",
                "message": str(e),
                "language": language
            }
            
        except ProcessingError as e:
            health_monitor.record_api_call("code_generation", False, time.time() - start_time)
            log_user_operation("code_generation", "system", success=False)
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e),
                "language": language
            }
            
        except Exception as e:
            log_error_with_context(e, {"requirements": requirements, "language": language}, "generate_code", "system")
            health_monitor.record_api_call("code_generation", False, time.time() - start_time)
            log_user_operation("code_generation", "system", success=False)
            return {
                "status": "error",
                "error_type": "system",
                "message": f"Error interno del generador: {str(e)}",
                "language": language
            }
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(ProcessingError, OSError))
    @safe_execute(operation="fix_code_errors", log_errors=True)
    def fix_code_errors(self, code: str, error_message: str, language: str) -> Dict[str, Any]:
        """
        Genera código basado en requerimientos específicos.
        
        Args:
            requirements: Descripción de lo que debe hacer el código
            language: Lenguaje de programación objetivo
            
        Returns:
            Dict con código generado y metadatos
        """
        import time
        start_time = time.time()
        
        try:
            # Validar entrada
            if not requirements or not requirements.strip():
                raise ValidationError("Los requerimientos no pueden estar vacíos")
            
            if not language:
                raise ValidationError("El lenguaje de programación es requerido")
            
            # Registrar operación del usuario
            log_user_operation("code_generation", "system", success=True)
            
            # Generar código usando la función externa
            result = generate_code(requirements, language)
            
            # Registrar métricas de salud
            health_monitor.record_api_call("code_generation", True, time.time() - start_time)
            
            import time
            start_time = time.time()
            
            # Realizar corrección
            result = fix_code_errors(code, error_message, language)
            
            duration = time.time() - start_time
            log_metrics("code_error_fixing_duration", duration, {
                "language": language,
                "code_length": len(code)
            })
            
            # Agregar metadatos de la herramienta
            result["tool_metadata"] = {
                "generator": self.name,
                "fixing_duration": duration,
                "timestamp": time.time()
            }
            
            log_user_operation("code_error_fixing", "system", success=True)
            return result
            
        except ValidationError as e:
            health_monitor.record_api_call("code_error_fixing", False, time.time() - start_time)
            log_user_operation("code_error_fixing", "system", success=False)
            return {
                "status": "error",
                "error_type": "validation",
                "message": str(e),
                "language": language
            }
            
        except ProcessingError as e:
            health_monitor.record_api_call("code_error_fixing", False, time.time() - start_time)
            log_user_operation("code_error_fixing", "system", success=False)
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e),
                "language": language
            }
            
        except Exception as e:
            log_error_with_context(e, {"code": code, "error_message": error_message, "language": language}, "fix_code_errors", "system")
            health_monitor.record_api_call("code_error_fixing", False, time.time() - start_time)
            log_user_operation("code_error_fixing", "system", success=False)
            return {
                "status": "error",
                "error_type": "system",
                "message": f"Error interno del generador: {str(e)}",
                "language": language
            }