#!/usr/bin/env python3
"""
Script de debug para rastrear el flujo completo de inserción de conversaciones
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.memory_manager import MemoryManager

def debug_memory_flow():
    """Debug del flujo completo de memoria"""
    logger.info("🚀 Iniciando debug del flujo de memoria...")
    
    try:
        # 1. Inicializar MemoryManager
        logger.info("🔧 Inicializando MemoryManager...")
        memory_manager = MemoryManager()
        logger.info("✅ MemoryManager inicializado")
        
        # 2. Crear usuario de prueba
        logger.info("👤 Creando usuario de prueba...")
        test_slack_user = {
            'id': 'U_DEBUG_TEST_123',
            'real_name': 'Debug Test User',
            'profile': {
                'display_name': 'DebugUser',
                'email': 'debug@test.com',
                'image_192': 'https://example.com/debug.jpg'
            },
            'team_id': 'T_DEBUG_123',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(test_slack_user)
        if user:
            logger.info(f"✅ Usuario creado: {user.user_id}")
        else:
            logger.error("❌ Error creando usuario")
            return False
        
        # 3. Crear conversación
        logger.info("💬 Creando conversación...")
        conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id="C_DEBUG_123"
        )
        
        if conversation:
            logger.info(f"✅ Conversación creada: {conversation.conversation_id}")
        else:
            logger.error("❌ Error creando conversación")
            return False
        
        # 4. Guardar mensaje de usuario
        logger.info("💾 Guardando mensaje de usuario...")
        user_message = memory_manager.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
            content="Hola, este es un mensaje de prueba",
            message_type="user",
            slack_message_ts="1234567890.123456"
        )
        
        if user_message:
            logger.info(f"✅ Mensaje de usuario guardado: {user_message.message_id}")
        else:
            logger.error("❌ Error guardando mensaje de usuario")
            return False
        
        # 5. Guardar mensaje de asistente
        logger.info("💾 Guardando mensaje de asistente...")
        assistant_message = memory_manager.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
            content="Hola! Este es mi respuesta de prueba",
            message_type="assistant",
            tokens_used=25,
            model_used="claude-3-sonnet",
            response_time_ms=1500
        )
        
        if assistant_message:
            logger.info(f"✅ Mensaje de asistente guardado: {assistant_message.message_id}")
        else:
            logger.error("❌ Error guardando mensaje de asistente")
            return False
        
        # 6. Verificar datos en BigQuery
        logger.info("🔍 Verificando datos en BigQuery...")
        
        # Verificar usuario
        user_check = memory_manager.get_user_by_slack_id('U_DEBUG_TEST_123')
        if user_check:
            logger.info(f"✅ Usuario verificado en BigQuery: {user_check['user_id']}")
        else:
            logger.error("❌ Usuario no encontrado en BigQuery")
        
        # Verificar conversación
        conversation_check = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id="C_DEBUG_123"
        )
        if conversation_check:
            logger.info(f"✅ Conversación verificada en BigQuery: {conversation_check.conversation_id}")
        else:
            logger.error("❌ Conversación no encontrada en BigQuery")
        
        # Verificar mensajes
        history = memory_manager.get_conversation_history(conversation.conversation_id, limit=10)
        if history:
            logger.info(f"✅ Historial verificado: {len(history)} mensajes encontrados")
            for i, msg in enumerate(history):
                logger.info(f"   Mensaje {i+1}: {msg.get('message_type')} - {msg.get('content')[:50]}...")
        else:
            logger.error("❌ No se encontraron mensajes en el historial")
        
        logger.info("🎉 Debug del flujo de memoria completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en debug del flujo de memoria: {e}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

def debug_bigquery_tables():
    """Debug de las tablas de BigQuery"""
    logger.info("📊 Verificando tablas de BigQuery...")
    
    try:
        memory_manager = MemoryManager()
        
        # Verificar información de tablas
        tables = ['users', 'conversations', 'messages', 'context']
        
        for table_name in tables:
            info = memory_manager.bq_client.get_table_info(table_name)
            if info:
                logger.info(f"📋 Tabla {table_name}:")
                logger.info(f"   - Filas: {info['num_rows']}")
                logger.info(f"   - Bytes: {info['num_bytes']:,}")
                logger.info(f"   - Última modificación: {info['modified']}")
            else:
                logger.error(f"❌ No se pudo obtener información de tabla {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando tablas: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando debug completo del sistema de memoria...")
    logger.info("🚀 Iniciando debug completo del sistema de memoria...")
    
    print("\n" + "="*60)
    print("DEBUG MEMORY FLOW")
    print("="*60)
    
    # Test 1: Verificar tablas
    print("\n1. VERIFICACIÓN DE TABLAS:")
    try:
        tables_ok = debug_bigquery_tables()
        print(f"   Resultado: {'✅ OK' if tables_ok else '❌ ERROR'}")
    except Exception as e:
        print(f"   ❌ Error en verificación de tablas: {e}")
        tables_ok = False
    
    # Test 2: Flujo completo
    print("\n2. FLUJO COMPLETO DE MEMORIA:")
    try:
        flow_ok = debug_memory_flow()
        print(f"   Resultado: {'✅ OK' if flow_ok else '❌ ERROR'}")
    except Exception as e:
        print(f"   ❌ Error en flujo de memoria: {e}")
        import traceback
        print(f"   ❌ Traceback: {traceback.format_exc()}")
        flow_ok = False
    
    print("\n" + "="*60)
    if tables_ok and flow_ok:
        print("🎉 DEBUG COMPLETO: TODO OK")
    else:
        print("❌ DEBUG COMPLETO: HAY PROBLEMAS")
        print(f"   Tablas: {'✅' if tables_ok else '❌'}")
        print(f"   Flujo: {'✅' if flow_ok else '❌'}")
    print("="*60)