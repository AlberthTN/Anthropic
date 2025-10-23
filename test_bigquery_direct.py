#!/usr/bin/env python3
"""
Test directo de BigQuery para verificar inserción y consulta de datos
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.bigquery_client import BigQueryClient

def test_direct_bigquery():
    """Test directo de BigQuery"""
    logger.info("🧪 Iniciando test directo de BigQuery...")
    
    try:
        # Inicializar cliente BigQuery
        bq_client = BigQueryClient()
        
        # Verificar conexión
        logger.info("🔗 Verificando conexión a BigQuery...")
        if not bq_client._test_connection():
            logger.error("❌ No se pudo conectar a BigQuery")
            return False
        
        logger.info("✅ Conexión a BigQuery verificada")
        
        # Crear tablas si no existen
        logger.info("📋 Creando tablas...")
        if not bq_client.create_tables():
            logger.error("❌ No se pudieron crear las tablas")
            return False
        
        logger.info("✅ Tablas creadas/verificadas")
        
        # Insertar datos de prueba directamente
        logger.info("💾 Insertando datos de prueba...")
        
        test_user = {
            'user_id': 'test-user-123',
            'slack_user_id': 'U_TEST_123',
            'real_name': 'Test User',
            'display_name': 'TestUser',
            'email': 'test@example.com',
            'team_id': 'T_TEST_123',
            'timezone': 'UTC',
            'profile_image': 'https://example.com/image.jpg',
            'is_admin': False,
            'is_bot': False,
            'preferences': {'theme': 'dark', 'notifications': True},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Insertar usuario
        success = bq_client.insert_rows('users', [test_user])
        if not success:
            logger.error("❌ Error al insertar usuario")
            return False
        
        logger.info("✅ Usuario insertado exitosamente")
        
        # Esperar un momento para que se propague
        import time
        time.sleep(2)
        
        # Verificar inserción con consulta directa
        logger.info("🔍 Consultando datos insertados...")
        
        query = f"""
        SELECT COUNT(*) as total_users
        FROM `{bq_client.project_id}.{bq_client.dataset_id}.users`
        """
        
        try:
            query_job = bq_client.client.query(query)
            results = query_job.result()
            
            for row in results:
                total_users = row.total_users
                logger.info(f"📊 Total de usuarios en la tabla: {total_users}")
                
                if total_users > 0:
                    logger.info("✅ Los datos se insertaron correctamente")
                    
                    # Consultar el usuario específico
                    user_query = f"""
                    SELECT user_id, slack_user_id, real_name, email
                    FROM `{bq_client.project_id}.{bq_client.dataset_id}.users`
                    WHERE slack_user_id = 'U_TEST_123'
                    """
                    
                    user_job = bq_client.client.query(user_query)
                    user_results = user_job.result()
                    
                    for user_row in user_results:
                        logger.info(f"👤 Usuario encontrado: {user_row.user_id} - {user_row.real_name} ({user_row.email})")
                    
                    return True
                else:
                    logger.error("❌ No se encontraron datos después de la inserción")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error en consulta: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error en test directo: {e}")
        return False

def test_table_info():
    """Test de información de tablas"""
    logger.info("📊 Obteniendo información de tablas...")
    
    try:
        bq_client = BigQueryClient()
        
        tables = ['users', 'conversations', 'messages', 'context']
        
        for table_name in tables:
            info = bq_client.get_table_info(table_name)
            if info:
                logger.info(f"📋 Tabla {table_name}: {info['num_rows']} filas, {info['num_bytes']} bytes")
            else:
                logger.error(f"❌ No se pudo obtener información de tabla {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo información de tablas: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando tests directos de BigQuery...")
    
    # Test 1: Información de tablas antes
    logger.info("\n=== TEST 1: Información de tablas (antes) ===")
    test_table_info()
    
    # Test 2: Inserción directa
    logger.info("\n=== TEST 2: Inserción directa ===")
    success = test_direct_bigquery()
    
    # Test 3: Información de tablas después
    logger.info("\n=== TEST 3: Información de tablas (después) ===")
    test_table_info()
    
    if success:
        logger.info("🎉 Todos los tests pasaron exitosamente")
    else:
        logger.error("❌ Algunos tests fallaron")