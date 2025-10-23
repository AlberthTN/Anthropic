#!/usr/bin/env python3
"""
Test script para verificar la extracción de JSON del texto problemático
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
        # Buscar bloques de código JSON
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON en bloque de código
            r'```\s*(\{.*?\})\s*```',      # JSON en bloque de código sin especificar lenguaje
            r'(\{[^{}]*"[^"]*"[^{}]*:[^{}]*\})',  # JSON simple en una línea
            r'(\{(?:[^{}]|{[^{}]*})*\})'   # JSON anidado
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            for match in matches:
                try:
                    # Limpiar el match
                    clean_match = match.strip()
                    if clean_match.startswith('{') and clean_match.endswith('}'):
                        parsed = json.loads(clean_match)
                        print(f"🎯 JSON encontrado con patrón: {pattern}")
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        # Si no se encuentra en bloques, buscar el primer JSON válido
        start_idx = text.find('{')
        if start_idx != -1:
            # Encontrar el JSON balanceado
            brace_count = 0
            for i, char in enumerate(text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_candidate = text[start_idx:i+1]
                        try:
                            parsed = json.loads(json_candidate)
                            print(f"🎯 JSON encontrado por balanceo de llaves")
                            return parsed
                        except json.JSONDecodeError:
                            break
        
        print(f"⚠️ No se pudo extraer JSON válido del texto")
        return None
        
    except Exception as e:
        print(f"❌ Error en extracción de JSON: {e}")
        return None

def test_json_extraction():
    """
    Prueba la extracción de JSON con el texto problemático del error
    """
    print("🧪 INICIANDO PRUEBA DE EXTRACCIÓN DE JSON")
    print("=" * 60)
    
    # Texto problemático del error reportado
    problematic_text = '''Analizaré la solicitud "Hola" y proporcionaré un análisis estructurado.

ANÁLISIS:
La solicitud es demasiado general y carece de información específica para determinar el alcance exacto o los requisitos técnicos. Sin contexto adicional, solo podemos hacer suposiciones básicas.

RESPUESTA JSON:
```json
{
    "type": "undefined",
    "language": "unknown",
    "requirements": {
        "identified": [],
        "missing": [
            "Propósito específico del programa",
            "Lenguaje de programación deseado",
            "Funcionalidades requeridas",
            "Contexto de uso",
            "Restricciones técnicas"
        ]
    },
    "priority": "undefined",
    "estimated_complexity": "undefined",
    "additional_info": {
        "status": "insufficient_information",
        "recommendation": "Se necesita más información para proporcionar una respuesta útil",
        "suggested_details": [
            "¿Qué lenguaje de programación deseas utilizar?",
            "¿Cuál es el objetivo del programa?",
            "¿Hay requisitos específicos de implementación?",
            "¿En qué contexto se utilizará?",
            "¿Existen restricciones técnicas o de rendimiento?"
        ]
    }
}
```

RECOMENDACIONES:
Para proporcionar una asistencia más efectiva, sería útil incluir:

1. Descripción clara del objetivo
2. Lenguaje de programación deseado
3. Funcionalidades específicas requeridas
4. Contexto de uso
5. Cualquier restricción técnica

Por ejemplo, una solicitud más completa podría ser:
"Necesito un programa en Python que muestre 'Hola' en la consola, con manejo de errores básico y documentación"

¿Te gustaría proporcionar más detalles sobre tu solicitud para que pueda ayudarte de manera más específica?'''

    print(f"📝 Texto de entrada (primeros 200 caracteres):")
    print(f"'{problematic_text[:200]}...'")
    print()
    
    # Intentar parsear directamente (esto debería fallar)
    print("🔍 PRUEBA 1: Parseo directo con json.loads()")
    try:
        direct_result = json.loads(problematic_text)
        print("✅ Parseo directo exitoso (inesperado)")
        print(f"Resultado: {direct_result}")
    except json.JSONDecodeError as e:
        print(f"❌ Parseo directo falló como se esperaba: {e}")
    print()
    
    # Usar el método de extracción
    print("🔍 PRUEBA 2: Extracción inteligente de JSON")
    extracted_json = extract_json_from_text(problematic_text)
    
    if extracted_json:
        print("✅ Extracción exitosa!")
        print(f"Tipo extraído: {extracted_json.get('type', 'N/A')}")
        print(f"Lenguaje: {extracted_json.get('language', 'N/A')}")
        print(f"Prioridad: {extracted_json.get('priority', 'N/A')}")
        print(f"Estado: {extracted_json.get('additional_info', {}).get('status', 'N/A')}")
        print()
        print("📋 JSON completo extraído:")
        print(json.dumps(extracted_json, indent=2, ensure_ascii=False))
    else:
        print("❌ No se pudo extraer JSON")
    
    print()
    print("=" * 60)
    print("🏁 PRUEBA COMPLETADA")

if __name__ == "__main__":
    test_json_extraction()