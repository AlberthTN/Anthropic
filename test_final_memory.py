#!/usr/bin/env python3
"""
Test final de memoria persistente - Simplificado
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_memory_manager():
    """Test del MemoryManager"""
    logger.info("🧪 Iniciando test de MemoryManager...")
    
    try:
        from utils.memory_manager import MemoryManager
        
        # Crear MemoryManager
        logger.info("🔧 Creando MemoryManager...")
        memory_manager = MemoryManager()
        logger.info("✅ MemoryManager creado")
        
        # Crear usuario de prueba
        logger.info("👤 Creando usuario de prueba...")
        slack_user_info = {
            'id': 'U_TEST_FINAL',
            'real_name': 'Test Final User',
            'profile': {
                'display_name': 'TestFinal',
                'email': 'testfinal@example.com'
            },
            'team_id': 'T_TEST',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(slack_user_info)
        if user:
            logger.info(f"✅ Usuario creado: {user.user_id}")
            
            # Crear conversación
            logger.info("💬 Creando conversación...")
            conversation = memory_manager.get_or_create_conversation(
                user_id=user.user_id,
                slack_channel_id='C_TEST_FINAL',
                slack_thread_ts='1234567890.123'
            )
            
            if conversation:
                logger.info(f"✅ Conversación creada: {conversation.conversation_id}")
                
                # Guardar mensaje
                logger.info("💾 Guardando mensaje...")
                message_saved = memory_manager.save_message(
                    conversation_id=conversation.conversation_id,
                    user_id=user.user_id,
                    content="Mensaje de prueba final",
                    message_type="user",
                    slack_message_ts="1234567890.124"
                )
                
                if message_saved:
                    logger.info("✅ Mensaje guardado exitosamente")
                    
                    # Obtener historial
                    logger.info("📖 Obteniendo historial...")
                    history = memory_manager.get_conversation_history(
                        conversation.conversation_id,
                        limit=10
                    )
                    
                    logger.info(f"📊 Mensajes en historial: {len(history)}")
                    
                    if len(history) > 0:
                        logger.info("🎉 ¡MEMORIA PERSISTENTE FUNCIONANDO CORRECTAMENTE!")
                        return True
                    else:
                        logger.error("❌ No se encontraron mensajes en el historial")
                        return False
                else:
                    logger.error("❌ Error guardando mensaje")
                    return False
            else:
                logger.error("❌ Error creando conversación")
                return False
        else:
            logger.error("❌ Error creando usuario")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_bigquery_data():
    """Verificar datos en BigQuery directamente"""
    logger.info("🔍 Verificando datos en BigQuery...")
    
    try:
        from utils.bigquery_client import BigQueryClient
        
        bq_client = BigQueryClient()
        
        # Verificar cada tabla
        tables = ['users', 'conversations', 'messages', 'context']
        
        for table_name in tables:
            try:
                info = bq_client.get_table_info(table_name)
                if info:
                    logger.info(f"📋 {table_name}: {info['num_rows']} filas")
                else:
                    logger.warning(f"⚠️ No se pudo obtener info de {table_name}")
            except Exception as e:
                logger.error(f"❌ Error con tabla {table_name}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando BigQuery: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 INICIANDO TEST FINAL DE MEMORIA PERSISTENTE")
    logger.info("=" * 50)
    
    # Test principal
    success = test_memory_manager()
    
    # Verificar datos
    logger.info("\n" + "=" * 50)
    verify_bigquery_data()
    
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("🎉 ¡MEMORIA PERSISTENTE VERIFICADA EXITOSAMENTE!")
    else:
        logger.error("❌ PROBLEMAS CON LA MEMORIA PERSISTENTE")
    logger.info("=" * 50)