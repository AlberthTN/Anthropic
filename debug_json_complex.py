#!/usr/bin/env python3
"""
Debug específico para el JSON anidado complejo
"""

import json
import re

def debug_complex_json():
    """
    Debug del caso específico del JSON anidado complejo
    """
    text = '''Análisis completo:

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

Fin del análisis.'''

    print("🔍 DEBUG DEL JSON ANIDADO COMPLEJO")
    print("=" * 50)
    print(f"Texto completo:\n{text}")
    print("=" * 50)
    
    # Probar cada patrón individualmente
    patterns = [
        (r'```json\s*(\{.*?\})\s*```', "JSON en bloque ```json"),
        (r'```\s*(\{.*?\})\s*```', "JSON en bloque ```"),
        (r'(\{[^{}]*"[^"]*"[^{}]*:[^{}]*\})', "JSON simple en línea"),
    ]
    
    for pattern, description in patterns:
        print(f"\n🔍 Probando patrón: {description}")
        print(f"Regex: {pattern}")
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        print(f"Matches encontrados: {len(matches)}")
        for i, match in enumerate(matches):
            print(f"  Match {i+1}: {match[:100]}...")
            try:
                parsed = json.loads(match.strip())
                print(f"  ✅ JSON válido: {parsed.get('type', 'N/A')}")
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON inválido: {e}")
    
    # Probar el método de balanceo de llaves
    print(f"\n🔍 Probando método de balanceo de llaves")
    start_idx = text.find('{')
    print(f"Primer '{{' encontrado en posición: {start_idx}")
    
    if start_idx != -1:
        brace_count = 0
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_candidate = text[start_idx:i+1]
                    print(f"JSON candidato encontrado (posición {start_idx}-{i}):")
                    print(f"Longitud: {len(json_candidate)} caracteres")
                    print(f"Primeros 100 chars: {json_candidate[:100]}...")
                    print(f"Últimos 100 chars: ...{json_candidate[-100:]}")
                    
                    try:
                        parsed = json.loads(json_candidate)
                        print(f"✅ JSON válido extraído!")
                        print(f"Tipo: {parsed.get('type', 'N/A')}")
                        print(f"Claves: {list(parsed.keys())}")
                        return parsed
                    except json.JSONDecodeError as e:
                        print(f"❌ Error al parsear JSON: {e}")
                        print(f"Posición del error: {e.pos if hasattr(e, 'pos') else 'N/A'}")
                        break
    
    print("❌ No se pudo extraer JSON válido")
    return None

if __name__ == "__main__":
    debug_complex_json()