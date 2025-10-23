#!/usr/bin/env python3
"""
Prueba simple para diagnosticar problemas con la memoria persistente.
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.memory_manager import MemoryManager
from utils.bigquery_client import BigQueryClient

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simple_insert():
    """Prueba simple de inserción directa."""
    try:
        logger.info("🔧 Probando inserción directa en BigQuery...")
        
        # Inicializar cliente
        bq_client = BigQueryClient()
        
        # Datos de prueba simples
        test_data = [{
            'user_id': str(uuid.uuid4()),
            'slack_user_id': 'U12345TEST',
            'real_name': 'Usuario Prueba',
            'display_name': 'Test User',
            'email': 'test@example.com',
            'team_id': 'T12345',
            'timezone': 'UTC',
            'profile_image': None,
            'is_admin': False,
            'is_bot': False,
            'preferences': '{}',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }]
        
        logger.info(f"📝 Insertando datos: {json.dumps(test_data[0], indent=2)}")
        
        # Intentar insertar
        success = bq_client.insert_rows('users', test_data)
        
        if success:
            logger.info("✅ Inserción exitosa")
            
            # Verificar que se insertó
            info = bq_client.get_table_info('users')
            logger.info(f"📊 Filas en tabla users: {info.get('num_rows', 0)}")
            
            return True
        else:
            logger.error("❌ Falló la inserción")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en prueba simple: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_memory_manager_step_by_step():
    """Prueba el MemoryManager paso a paso."""
    try:
        logger.info("🧠 Probando MemoryManager paso a paso...")
        
        # Inicializar
        memory_manager = MemoryManager()
        
        # Datos de usuario de Slack
        slack_user_info = {
            'id': 'U12345STEP',
            'real_name': 'Usuario Paso a Paso',
            'profile': {
                'display_name': 'Step User',
                'email': 'step@example.com'
            },
            'team_id': 'T12345',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        logger.info("👤 Creando usuario...")
        user = memory_manager.create_or_update_user(slack_user_info)
        
        if user:
            logger.info(f"✅ Usuario creado: {user.user_id}")
            
            # Verificar en BigQuery
            info = memory_manager.bq_client.get_table_info('users')
            logger.info(f"📊 Filas en tabla users después de crear usuario: {info.get('num_rows', 0)}")
            
            return True
        else:
            logger.error("❌ No se pudo crear usuario")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en prueba paso a paso: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal."""
    logger.info("🚀 Iniciando diagnóstico de memoria persistente...")
    
    # Verificar variables de entorno
    required_vars = ['BIGQUERY_PROJECT_ID', 'BIGQUERY_DATASET', 'GOOGLE_APPLICATION_CREDENTIALS_JSON']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {missing_vars}")
        return False
    
    logger.info("✅ Variables de entorno OK")
    
    # Ejecutar pruebas
    tests = [
        ("Inserción directa", test_simple_insert),
        ("MemoryManager paso a paso", test_memory_manager_step_by_step)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n🔬 Ejecutando: {test_name}")
        try:
            result = test_func()
            if result:
                logger.info(f"✅ {test_name}: PASÓ")
            else:
                logger.error(f"❌ {test_name}: FALLÓ")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")

if __name__ == "__main__":
    main()