import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path)

# Agregar el directorio src al path de Python
sys.path.append(str(Path(__file__).parent.parent))

from evals.evaluator import AgentEvaluator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_evaluation_suite():
    """
    Ejecutar una suite de evaluaciones para probar el agente de programación.
    """
    evaluator = AgentEvaluator()
    
    print("🚀 Iniciando suite de evaluaciones...")
    
    # Evaluaciones de generación de código
    print("\n📋 Evaluaciones de Generación de Código:")
    
    # Test 1: Generar una función de suma en Python
    evaluator.evaluate_code_generation(
        test_id="gen_python_sum_001",
        requirements="Crea una función que sume dos números enteros",
        language="python",
        expected_output="def suma(a, b):\n    return a + b"
    )
    
    # Test 2: Generar una función de fibonacci en JavaScript
    evaluator.evaluate_code_generation(
        test_id="gen_js_fibonacci_002",
        requirements="Crea una función que calcule el enésimo número de Fibonacci",
        language="javascript"
    )
    
    # Test 3: Generar una clase en Python
    evaluator.evaluate_code_generation(
        test_id="gen_python_class_003",
        requirements="Crea una clase Calculator con métodos para sumar, restar, multiplicar y dividir",
        language="python"
    )
    
    # Evaluaciones de análisis de código
    print("\n🔍 Evaluaciones de Análisis de Código:")
    
    # Test 4: Analizar código con problemas
    problematic_code = """
def dividir(a, b):
    return a / b

resultado = dividir(10, 0)
print(resultado)
"""
    
    evaluator.evaluate_code_analysis(
        test_id="analysis_python_errors_004",
        code=problematic_code,
        language="python",
        expected_issues=["división por cero", "error handling"]
    )
    
    # Test 5: Analizar código JavaScript
    js_code = """
function processArray(arr) {
    let result = [];
    for (let i = 0; i <= arr.length; i++) {
        result.push(arr[i] * 2);
    }
    return result;
}
"""
    
    evaluator.evaluate_code_analysis(
        test_id="analysis_js_bounds_005",
        code=js_code,
        language="javascript",
        expected_issues=["off-by-one", "array bounds"]
    )
    
    # Guardar resultados
    evaluator.save_results()
    
    # Generar y mostrar reporte
    print("\n" + "="*50)
    evaluator.print_summary()
    
    return evaluator

def main():
    """
    Función principal para ejecutar las evaluaciones.
    """
    try:
        logger.info("🎯 Iniciando sistema de evaluación del agente...")
        
        # Verificar que el agente esté disponible
        try:
            from src.agents.claude_agent import agent
            logger.info("✅ Agente de programación disponible")
        except ImportError as e:
            logger.error(f"❌ No se pudo importar el agente: {e}")
            return 1
        
        # Ejecutar suite de evaluaciones
        evaluator = run_evaluation_suite()
        
        logger.info("✅ Suite de evaluaciones completada exitosamente")
        
        # Preguntar si se desea ver resultados detallados
        print("\n¿Deseas ver resultados detallados de cada evaluación? (s/n): ", end="")
        response = input().strip().lower()
        
        if response == 's':
            print("\n📊 Resultados detallados:")
            for i, result in enumerate(evaluator.results, 1):
                print(f"\n{i}. {result.test_id} ({result.task_type})")
                print(f"   Éxito: {result.success}")
                print(f"   Tiempo: {result.execution_time:.2f}s")
                print(f"   Calidad: {result.quality_score:.1f}/100")
                print(f"   Precisión: {result.accuracy_score:.1f}/100")
                if result.error_message:
                    print(f"   Error: {result.error_message}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Evaluación interrumpida por el usuario")
        return 0
    except Exception as e:
        logger.error(f"❌ Error fatal en la evaluación: {str(e)}")
        logger.error(f"Detalles del error: {type(e).__name__}: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)