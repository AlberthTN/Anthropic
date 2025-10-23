import ast
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
import json
import re

# Importar utilidades de error handling
from ..utils.error_handler import (
    retry_on_failure, safe_execute, log_error_with_context,
    ValidationError, ProcessingError, APIError
)
from ..utils.logging_config import log_user_operation, log_metrics
from ..utils.health_monitor import health_monitor

class CodeAnalyzer:
    """
    Clase para analizar código en diferentes lenguajes de programación.
    Proporciona análisis de calidad, complejidad y mejores prácticas.
    """
    
    def __init__(self):
        """Inicializa el analizador de código."""
        self.name = "CodeAnalyzer"
        self.supported_languages = ["python", "javascript", "typescript", "java"]
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(ProcessingError, OSError))
    @safe_execute(operation="analyze_code", log_errors=True)
    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analiza el código proporcionado y devuelve información sobre su estructura y calidad.
        
        Args:
            code: El código fuente a analizar
            language: El lenguaje de programación (python, javascript, etc.)
        
        Returns:
            Dict con análisis del código incluyendo errores, advertencias y métricas
        """
        import time
        start_time = time.time()
        
        try:
            # Validar entrada
            if not code or not code.strip():
                raise ValidationError("Código vacío proporcionado para análisis")
            
            if not language or not language.strip():
                raise ValidationError("Lenguaje no especificado para análisis")
            
            # Log de la operación
            log_user_operation("code_analysis", "system", {
                "language": language,
                "code_length": len(code),
                "lines_count": len(code.splitlines())
            })
            
            # Realizar análisis
            result = analyze_code(code, language)
            
            duration = time.time() - start_time
            log_metrics("code_analysis_duration", duration, {
                "language": language,
                "code_length": len(code)
            })
            
            # Registrar métricas de salud
            health_monitor.record_api_call("code_analysis", True, time.time() - start_time)
            
            # Agregar metadatos de la herramienta
            result["tool_metadata"] = {
                "analyzer": self.name,
                "analysis_duration": duration,
                "timestamp": time.time()
            }
            
            log_user_operation("code_analysis", "system", success=True)
            return result
            
        except ValidationError as e:
            health_monitor.record_api_call("code_analysis", False, time.time() - start_time, str(e))
            log_user_operation("code_analysis", "system", success=False)
            return {
                "status": "error",
                "error_type": "validation",
                "message": str(e),
                "language": language
            }
            
        except ProcessingError as e:
            health_monitor.record_api_call("code_analysis", False, time.time() - start_time, str(e))
            log_user_operation("code_analysis", "system", success=False)
            return {
                "status": "error",
                "error_type": "processing",
                "message": str(e),
                "language": language
            }
            
        except Exception as e:
            log_error_with_context(e, {"code_length": len(code), "language": language}, "analyze_code", "system")
            health_monitor.record_api_call("code_analysis", False, time.time() - start_time, str(e))
            log_user_operation("code_analysis", "system", success=False)
            return {
                "status": "error",
                "error_type": "system",
                "message": f"Error interno del analizador: {str(e)}",
                "language": language
            }

def analyze_code(code: str, language: str) -> Dict[str, Any]:
    """
    Analiza el código proporcionado y devuelve información sobre su estructura y calidad.
    
    Args:
        code: El código fuente a analizar
        language: El lenguaje de programación (python, javascript, etc.)
    
    Returns:
        Dict con análisis del código incluyendo errores, advertencias y métricas
    """
    # Lista de lenguajes soportados
    supported_languages = ["python", "javascript", "typescript", "java"]
    
    if language.lower() not in supported_languages:
        raise ValidationError(f"Lenguaje '{language}' no soportado. Lenguajes soportados: {', '.join(supported_languages)}")
    
    try:
        if language.lower() == "python":
            return analyze_python_code(code)
        elif language.lower() in ["javascript", "typescript"]:
            return analyze_javascript_code(code)
        elif language.lower() == "java":
            return analyze_java_code(code)
        else:
            return {
                "status": "warning",
                "message": f"Análisis básico para {language} - características limitadas",
                "metrics": {
                    "lines_of_code": len(code.splitlines()),
                    "characters": len(code),
                    "complexity": "unknown"
                }
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al analizar código: {str(e)}",
            "error_details": str(e)
        }

def analyze_python_code(code: str) -> Dict[str, Any]:
    """Analiza código Python específicamente."""
    try:
        # Parsear el AST
        tree = ast.parse(code)
        
        # Análisis básico
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        
        # Calcular complejidad ciclomática básica
        complexity = calculate_cyclomatic_complexity(tree)
        
        # Verificar problemas comunes
        issues = check_python_issues(tree, code)
        
        # Ejecutar flake8 si está disponible
        lint_results = run_python_linter(code)
        
        result = {
            "status": "success",
            "language": "python",
            "metrics": {
                "lines_of_code": len(code.splitlines()),
                "functions": len(functions),
                "classes": len(classes),
                "imports": len(imports),
                "cyclomatic_complexity": complexity,
                "maintainability_index": calculate_maintainability_index(code)
            },
            "structure": {
                "functions": [func.name for func in functions],
                "classes": [cls.name for cls in classes],
                "imports": extract_imports(imports)
            },
            "issues": issues,
            "lint_results": lint_results
        }
        
        return result
        
    except SyntaxError as e:
        return {
            "status": "error",
            "message": f"Error de sintaxis en Python: {str(e)}",
            "line": e.lineno,
            "column": e.offset
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al analizar código Python: {str(e)}"
        }

def analyze_javascript_code(code: str) -> Dict[str, Any]:
    """Analiza código JavaScript/TypeScript."""
    try:
        # Análisis básico con expresiones regulares
        functions = re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=.*=>|(\w+)\s*:\s*function', code)
        classes = re.findall(r'class\s+(\w+)', code)
        imports = re.findall(r'import.*from|require\(', code)
        
        # Calcular métricas básicas
        lines = code.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        
        result = {
            "status": "success",
            "language": "javascript",
            "metrics": {
                "lines_of_code": len(lines),
                "non_empty_lines": len(non_empty_lines),
                "functions": len(functions),
                "classes": len(classes),
                "imports": len(imports),
                "complexity": "basic"
            },
            "structure": {
                "functions": list(set([f[0] or f[1] or f[2] for f in functions if any(f)])),
                "classes": classes,
                "imports": imports
            },
            "issues": check_javascript_issues(code)
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al analizar código JavaScript: {str(e)}"
        }

def analyze_java_code(code: str) -> Dict[str, Any]:
    """Analiza código Java."""
    try:
        # Análisis básico con expresiones regulares
        classes = re.findall(r'class\s+(\w+)', code)
        methods = re.findall(r'(public|private|protected)\s+(?:static\s+)?(?:\w+\s+)*(\w+)\s*\(', code)
        imports = re.findall(r'import\s+([\w.]+);', code)
        
        lines = code.splitlines()
        
        result = {
            "status": "success",
            "language": "java",
            "metrics": {
                "lines_of_code": len(lines),
                "classes": len(classes),
                "methods": len(methods),
                "imports": len(imports)
            },
            "structure": {
                "classes": classes,
                "methods": [method[1] for method in methods],
                "imports": imports
            }
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al analizar código Java: {str(e)}"
        }

def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calcula la complejidad ciclomática básica."""
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity

def calculate_maintainability_index(code: str) -> float:
    """Calcula un índice básico de mantenibilidad."""
    lines = code.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    comments = [line for line in non_empty_lines if line.strip().startswith('#')]
    
    if len(non_empty_lines) == 0:
        return 0.0
    
    comment_ratio = len(comments) / len(non_empty_lines)
    return min(100.0, comment_ratio * 200)

def check_python_issues(tree: ast.AST, code: str) -> List[Dict[str, Any]]:
    """Verifica problemas comunes en código Python."""
    issues = []
    
    for node in ast.walk(tree):
        # Verificar nombres de variables poco descriptivos
        if isinstance(node, ast.Name) and len(node.id) < 3 and node.id not in ['i', 'j', 'k', 'x', 'y', 'z']:
            issues.append({
                "type": "warning",
                "message": f"Variable '{node.id}' puede tener un nombre más descriptivo",
                "line": getattr(node, 'lineno', 0)
            })
        
        # Verificar funciones sin docstrings
        if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
            issues.append({
                "type": "warning",
                "message": f"Función '{node.name}' debería tener un docstring",
                "line": node.lineno
            })
    
    return issues

def check_javascript_issues(code: str) -> List[Dict[str, Any]]:
    """Verifica problemas comunes en código JavaScript."""
    issues = []
    lines = code.splitlines()
    
    for i, line in enumerate(lines, 1):
        # Verificar uso de var en lugar de let/const
        if re.search(r'\bvar\s+', line):
            issues.append({
                "type": "warning",
                "message": "Considera usar 'let' o 'const' en lugar de 'var'",
                "line": i
            })
        
        # Verificar console.log
        if 'console.log' in line:
            issues.append({
                "type": "info",
                "message": "Recuerda remover los console.log antes de producción",
                "line": i
            })
    
    return issues

def extract_imports(imports: List[ast.AST]) -> List[str]:
    """Extrae los nombres de los imports."""
    import_names = []
    for node in imports:
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                import_names.append(f"{module}.{alias.name}")
    return import_names

def run_python_linter(code: str) -> Dict[str, Any]:
    """Ejecuta flake8 en el código si está disponible."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        result = subprocess.run(['flake8', '--max-line-length=88', temp_file], 
                              capture_output=True, text=True)
        
        os.unlink(temp_file)
        
        if result.returncode == 0:
            return {"status": "success", "message": "No se encontraron problemas de estilo"}
        else:
            return {"status": "warning", "issues": result.stdout.splitlines()}
            
    except FileNotFoundError:
        return {"status": "info", "message": "Flake8 no está disponible"}
    except Exception as e:
        return {"status": "error", "message": f"Error ejecutando linter: {str(e)}"}

import re