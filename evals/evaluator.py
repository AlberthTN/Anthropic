import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)

@dataclass
class EvaluationResult:
    """Resultado de una evaluación del agente."""
    test_id: str
    timestamp: datetime
    task_type: str  # 'code_generation', 'analysis', 'debugging', 'testing'
    input_data: Dict[str, Any]
    expected_output: Optional[str]
    actual_output: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    quality_score: float = 0.0  # 0-100
    accuracy_score: float = 0.0  # 0-100
    code_quality_score: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class AgentEvaluator:
    """Sistema de evaluación para el agente de programación."""
    
    def __init__(self, results_file: str = "evals/results.json"):
        self.results_file = results_file
        self.results: List[EvaluationResult] = []
        self.load_existing_results()
    
    def load_existing_results(self):
        """Cargar resultados de evaluaciones previas."""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results = [
                        EvaluationResult(
                            test_id=item['test_id'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            task_type=item['task_type'],
                            input_data=item['input_data'],
                            expected_output=item.get('expected_output'),
                            actual_output=item['actual_output'],
                            success=item['success'],
                            execution_time=item['execution_time'],
                            error_message=item.get('error_message'),
                            quality_score=item.get('quality_score', 0.0),
                            accuracy_score=item.get('accuracy_score', 0.0),
                            code_quality_score=item.get('code_quality_score', 0.0)
                        )
                        for item in data
                    ]
                logger.info(f"✅ Cargados {len(self.results)} resultados previos")
        except Exception as e:
            logger.error(f"Error cargando resultados: {e}")
            self.results = []
    
    def save_results(self):
        """Guardar todos los resultados en archivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.results_file), exist_ok=True)
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump([result.to_dict() for result in self.results], f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Guardados {len(self.results)} resultados")
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
    
    def evaluate_code_generation(self, test_id: str, requirements: str, language: str, expected_output: Optional[str] = None) -> EvaluationResult:
        """Evaluar la generación de código."""
        logger.info(f"Evaluando generación de código: {test_id}")
        
        start_time = time.time()
        
        try:
            # Importar el agente
            from src.agents.claude_agent import ClaudeProgrammingAgent
            
            # Crear instancia del agente
            agent = ClaudeProgrammingAgent()
            
            # Crear contexto para generación de código
            context = {
                "language": language,
                "requirements": requirements,
                "user": "evaluator"
            }
            
            # Ejecutar el agente
            result = agent.generate_code(context)
            execution_time = time.time() - start_time
            
            # Calificar la calidad del código
            quality_score = self._evaluate_code_quality(result, language)
            accuracy_score = self._evaluate_accuracy(result, expected_output) if expected_output else 0.0
            code_quality_score = self._evaluate_code_structure(result, language)
            
            success = quality_score > 70 and accuracy_score > 70
            
            evaluation = EvaluationResult(
                test_id=test_id,
                timestamp=datetime.now(),
                task_type='code_generation',
                input_data={'requirements': requirements, 'language': language},
                expected_output=expected_output,
                actual_output=result,
                success=success,
                execution_time=execution_time,
                quality_score=quality_score,
                accuracy_score=accuracy_score,
                code_quality_score=code_quality_score
            )
            
            self.results.append(evaluation)
            logger.info(f"✅ Evaluación completada: {test_id} (Éxito: {success})")
            return evaluation
            
        except Exception as e:
            execution_time = time.time() - start_time
            evaluation = EvaluationResult(
                test_id=test_id,
                timestamp=datetime.now(),
                task_type='code_generation',
                input_data={'requirements': requirements, 'language': language},
                expected_output=expected_output,
                actual_output={"error": str(e), "code": ""},
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            
            self.results.append(evaluation)
            logger.error(f"❌ Error en evaluación {test_id}: {e}")
            return evaluation
    
    def evaluate_code_analysis(self, test_id: str, code: str, language: str, expected_issues: Optional[List[str]] = None) -> EvaluationResult:
        """Evaluar el análisis de código."""
        logger.info(f"Evaluando análisis de código: {test_id}")
        
        start_time = time.time()
        
        try:
            from src.agents.claude_agent import ClaudeProgrammingAgent
            
            # Crear instancia del agente
            agent = ClaudeProgrammingAgent()
            
            # Crear contexto para análisis de código
            context = {
                "language": language,
                "code": code,
                "user": "evaluator"
            }
            
            result = agent.analyze_code(context)
            execution_time = time.time() - start_time
            
            quality_score = self._evaluate_analysis_quality(result, code, language)
            accuracy_score = self._evaluate_analysis_accuracy(result, expected_issues) if expected_issues else 0.0
            
            success = quality_score > 70
            
            evaluation = EvaluationResult(
                test_id=test_id,
                timestamp=datetime.now(),
                task_type='analysis',
                input_data={'code': code, 'language': language},
                expected_output=str(expected_issues) if expected_issues else None,
                actual_output=result,
                success=success,
                execution_time=execution_time,
                quality_score=quality_score,
                accuracy_score=accuracy_score
            )
            
            self.results.append(evaluation)
            logger.info(f"✅ Análisis completado: {test_id} (Éxito: {success})")
            return evaluation
            
        except Exception as e:
            execution_time = time.time() - start_time
            evaluation = EvaluationResult(
                test_id=test_id,
                timestamp=datetime.now(),
                task_type='analysis',
                input_data={'code': code, 'language': language},
                expected_output=str(expected_issues) if expected_issues else None,
                actual_output={"error": str(e), "analysis": ""},
                success=False,
                execution_time=execution_time,
                error_message=str(e)
            )
            
            self.results.append(evaluation)
            logger.error(f"❌ Error en análisis {test_id}: {e}")
            return evaluation
    
    def _evaluate_code_quality(self, result: Dict[str, Any], language: str) -> float:
        """Evaluar la calidad general del código."""
        # Si hay error, la calidad es 0
        if result.get('error'):
            return 0.0
            
        score = 50.0  # Puntuación base
        
        # Extraer el código del resultado del agente
        if isinstance(result, dict):
            code = result.get('code', '')
        else:
            code = str(result)
        
        # Verificar documentación
        if 'def ' in code and '"""' in code:
            score += 20
        
        # Verificar manejo de errores
        if any(keyword in code.lower() for keyword in ['try:', 'except', 'catch', 'error']):
            score += 15
        
        # Verificar comentarios
        if any(keyword in code for keyword in ['#', '//', '/*']):
            score += 10
        
        # Verificar estructura
        if language == 'python' and 'if __name__ == "__main__"' in code:
            score += 5
        
        return min(score, 100.0)
    
    def _evaluate_accuracy(self, result: Dict[str, Any], expected: Optional[str]) -> float:
        """Evaluar la exactitud comparando con la salida esperada."""
        if not expected:
            return 0.0
            
        # Si hay error, la precisión es 0
        if result.get('error'):
            return 0.0
        
        # Extraer el código del resultado del agente
        if isinstance(result, dict):
            actual_code = result.get('code', '')
        else:
            actual_code = str(result)
        
        # Comparación simple (se puede mejorar con técnicas más sofisticadas)
        actual_normalized = actual_code.strip().lower()
        expected_normalized = str(expected).strip().lower()
        
        if actual_normalized == expected_normalized:
            return 100.0
        elif expected_normalized in actual_normalized or actual_normalized in expected_normalized:
            return 75.0
        else:
            return 25.0
    
    def _evaluate_code_structure(self, result: Dict[str, Any], language: str) -> float:
        """Evaluar la estructura y organización del código."""
        # Si hay error, la estructura es 0
        if result.get('error'):
            return 0.0
            
        score = 50.0
        
        # Extraer el código del resultado del agente
        if isinstance(result, dict):
            code = result.get('code', '')
        else:
            code = str(result)
        
        # Verificar funciones/métodos
        if language == 'python':
            function_count = code.count('def ')
            class_count = code.count('class ')
        elif language == 'javascript':
            function_count = code.count('function ') + code.count('=>')
            class_count = code.count('class ')
        else:
            function_count = 0
            class_count = 0
        
        # Bonus por modularidad
        if function_count > 0:
            score += min(function_count * 5, 30)
        
        if class_count > 0:
            score += min(class_count * 10, 20)
        
        return min(score, 100.0)
    
    def _evaluate_analysis_quality(self, result: Dict[str, Any], original_code: str, language: str) -> float:
        """Evaluar la calidad del análisis de código."""
        # Si hay error, la calidad es 0
        if result.get('error'):
            return 0.0
            
        score = 50.0
        
        # Extraer el análisis del resultado del agente
        if isinstance(result, dict):
            analysis = result.get('analysis', '')
        else:
            analysis = str(result)
        
        # Verificar profundidad del análisis
        if len(analysis) > 200:
            score += 20
        
        # Verificar mención de problemas específicos
        if any(keyword in analysis.lower() for keyword in ['performance', 'optimización', 'mejora', 'problema', 'error']):
            score += 15
        
        # Verificar sugerencias concretas
        if any(keyword in analysis.lower() for keyword in ['sugerencia', 'recomendación', 'considerar', 'debería']):
            score += 15
        
        return min(score, 100.0)
    
    def _evaluate_analysis_accuracy(self, result: Dict[str, Any], expected_issues: Optional[List[str]]) -> float:
        """Evaluar la precisión del análisis comparando con los problemas esperados."""
        if not expected_issues:
            return 0.0
            
        # Si hay error, la precisión es 0
        if result.get('error'):
            return 0.0
        
        # Extraer el análisis del resultado del agente
        if isinstance(result, dict):
            analysis = result.get('analysis', '')
        else:
            analysis = str(result)
        
        analysis_lower = analysis.lower()
        
        # Contar cuántos problemas esperados se mencionan
        mentioned_issues = 0
        for issue in expected_issues:
            if issue.lower() in analysis_lower:
                mentioned_issues += 1
        
        # Calcular precisión
        if len(expected_issues) > 0:
            accuracy = (mentioned_issues / len(expected_issues)) * 100
        else:
            accuracy = 0.0
        
        return min(accuracy, 100.0)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generar un reporte de todas las evaluaciones."""
        if not self.results:
            return {'message': 'No hay evaluaciones para generar reporte'}
        
        # Agrupar por tipo de tarea
        by_task_type = {}
        for result in self.results:
            if result.task_type not in by_task_type:
                by_task_type[result.task_type] = []
            by_task_type[result.task_type].append(result)
        
        # Calcular estadísticas
        report = {
            'total_evaluations': len(self.results),
            'overall_success_rate': sum(1 for r in self.results if r.success) / len(self.results) * 100,
            'average_execution_time': statistics.mean(r.execution_time for r in self.results),
            'task_breakdown': {}
        }
        
        for task_type, results in by_task_type.items():
            task_stats = {
                'count': len(results),
                'success_rate': sum(1 for r in results if r.success) / len(results) * 100,
                'avg_quality_score': statistics.mean(r.quality_score for r in results),
                'avg_accuracy_score': statistics.mean(r.accuracy_score for r in results),
                'avg_execution_time': statistics.mean(r.execution_time for r in results)
            }
            report['task_breakdown'][task_type] = task_stats
        
        return report
    
    def print_summary(self):
        """Imprimir un resumen de las evaluaciones."""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("📊 RESUMEN DE EVALUACIONES DEL AGENTE")
        print("="*60)
        
        if 'message' in report:
            print(f"⚠️  {report['message']}")
            return
        
        print(f"📈 Total de evaluaciones: {report['total_evaluations']}")
        print(f"✅ Tasa de éxito general: {report['overall_success_rate']:.1f}%")
        print(f"⏱️  Tiempo promedio de ejecución: {report['average_execution_time']:.2f}s")
        
        print("\n📋 Desglose por tipo de tarea:")
        for task_type, stats in report['task_breakdown'].items():
            print(f"\n  🔍 {task_type.upper()}:")
            print(f"     Evaluaciones: {stats['count']}")
            print(f"     Tasa de éxito: {stats['success_rate']:.1f}%")
            print(f"     Calidad promedio: {stats['avg_quality_score']:.1f}/100")
            print(f"     Precisión promedio: {stats['avg_accuracy_score']:.1f}/100")
            print(f"     Tiempo promedio: {stats['avg_execution_time']:.2f}s")
        
        print("\n" + "="*60)

# Importar os aquí para evitar problemas circulares
import os