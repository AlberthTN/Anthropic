#!/usr/bin/env python3
"""
Test script para verificar la robustez de la extracción de JSON con diferentes tipos de respuestas
"""

import json
import re
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def extract_json_from_text(text):
    """
    Método de prueba que replica la funcionalidad de _extract_json_from_text
    """
    try:
        # Buscar bloques de código JSON con patrones mejorados para JSON anidado
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON en bloque de código
            r'```\s*(\{.*?\})\s*```',      # JSON en bloque de código sin especificar lenguaje
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                try:
                    # Limpiar el match
                    clean_match = match.strip()
                    if clean_match.startswith('{') and clean_match.endswith('}'):
                        parsed = json.loads(clean_match)
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        # Si no se encuentra en bloques, buscar el primer JSON válido usando balanceo de llaves
        start_idx = text.find('{')
        if start_idx != -1:
            # Encontrar el JSON balanceado manejando strings correctamente
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(text[start_idx:], start_idx):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_candidate = text[start_idx:i+1]
                            try:
                                parsed = json.loads(json_candidate)
                                return parsed
                            except json.JSONDecodeError:
                                break
        
        return None
        
    except Exception as e:
        return None

def test_robust_json_extraction():
    """
    Prueba la extracción de JSON con diferentes tipos de respuestas
    """
    print("🧪 INICIANDO PRUEBAS DE ROBUSTEZ DE EXTRACCIÓN DE JSON")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "JSON en bloque de código con ```json",
            "text": '''Aquí está el análisis:

```json
{
    "type": "code_generation",
    "language": "python",
    "priority": "high"
}
```

Espero que esto ayude.''',
            "expected_type": "code_generation"
        },
        {
            "name": "JSON en bloque de código sin especificar lenguaje",
            "text": '''La respuesta es:

```
{
    "type": "debugging",
    "language": "javascript",
    "priority": "medium"
}
```

¿Te sirve?''',
            "expected_type": "debugging"
        },
        {
            "name": "JSON simple en una línea",
            "text": '''El resultado es {"type": "analysis", "status": "complete"} y ya está listo.''',
            "expected_type": "analysis"
        },
        {
            "name": "JSON anidado complejo",
            "text": '''Análisis completo:

{
    "type": "complex_analysis",
    "data": {
        "nested": {
            "value": "test",
            "array": [1, 2, 3]
        }
    },
    "metadata": {
        "timestamp": "2025-10-22",
        "version": "1.0"
    }
}

Fin del análisis.''',
            "expected_type": "complex_analysis"
        },
        {
            "name": "Múltiples JSONs (debería tomar el primero)",
            "text": '''Primer JSON: {"type": "first", "id": 1}
Segundo JSON: {"type": "second", "id": 2}''',
            "expected_type": "first"
        },
        {
            "name": "JSON con caracteres especiales",
            "text": '''```json
{
    "type": "special_chars",
    "message": "Hola, ¿cómo estás? ¡Bien!",
    "symbols": "áéíóú ñ @#$%",
    "unicode": "🚀 🎉 ✅"
}
```''',
            "expected_type": "special_chars"
        },
        {
            "name": "Texto sin JSON válido",
            "text": '''Este es solo texto plano sin JSON.
No hay nada que extraer aquí.
Solo palabras y más palabras.''',
            "expected_type": None
        },
        {
            "name": "JSON malformado",
            "text": '''```json
{
    "type": "malformed",
    "missing_quote: "value",
    "extra_comma": "value",
}
```''',
            "expected_type": None
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 PRUEBA {i}: {test_case['name']}")
        print("-" * 50)
        
        result = extract_json_from_text(test_case['text'])
        
        if test_case['expected_type'] is None:
            # Esperamos que no se extraiga JSON
            if result is None:
                print("✅ PASÓ: No se extrajo JSON como se esperaba")
                passed_tests += 1
            else:
                print(f"❌ FALLÓ: Se extrajo JSON inesperadamente: {result}")
        else:
            # Esperamos que se extraiga JSON con el tipo correcto
            if result and result.get('type') == test_case['expected_type']:
                print(f"✅ PASÓ: JSON extraído correctamente")
                print(f"   Tipo: {result.get('type')}")
                passed_tests += 1
            elif result:
                print(f"❌ FALLÓ: Tipo incorrecto. Esperado: {test_case['expected_type']}, Obtenido: {result.get('type')}")
            else:
                print(f"❌ FALLÓ: No se pudo extraer JSON")
        
        print()
    
    print("=" * 70)
    print(f"🏁 RESUMEN DE PRUEBAS")
    print(f"✅ Pruebas pasadas: {passed_tests}/{total_tests}")
    print(f"❌ Pruebas fallidas: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! La extracción de JSON es robusta.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar la implementación.")
    
    print("=" * 70)

if __name__ == "__main__":
    test_robust_json_extraction()