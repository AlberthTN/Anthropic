#!/usr/bin/env python3
"""
Test completo del sistema de memoria persistente
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_complete_memory_system():
    """Test completo del sistema de memoria"""
    logger.info("🧪 Test completo del sistema de memoria...")
    
    try:
        from utils.memory_manager import MemoryManager
        from utils.bigquery_client import BigQueryClient
        
        # Crear instancias
        memory_manager = MemoryManager()
        bq_client = BigQueryClient()
        logger.info("✅ Instancias creadas")
        
        # 1. Crear usuario
        logger.info("👤 Creando usuario...")
        slack_user_info = {
            'id': 'U_COMPLETE_TEST',
            'real_name': 'Complete Test User',
            'profile': {'email': 'complete@test.com', 'title': 'Tester'},
            'team_id': 'T_COMPLETE',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(slack_user_info)
        logger.info(f"✅ Usuario: {user.user_id}")
        
        # 2. Crear conversación
        logger.info("💬 Creando conversación...")
        conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id='C_COMPLETE',
            slack_thread_ts='1234567890.001'
        )
        logger.info(f"✅ Conversación: {conversation.conversation_id}")
        
        # 3. Guardar múltiples mensajes para probar continuidad
        logger.info("💾 Guardando múltiples mensajes...")
        messages = [
            {"content": "Hola, ¿cómo estás?", "type": "user"},
            {"content": "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?", "type": "assistant"},
            {"content": "Necesito ayuda con un proyecto de Python", "type": "user"},
            {"content": "Perfecto, estaré encantado de ayudarte con tu proyecto de Python. ¿Podrías contarme más detalles?", "type": "assistant"},
            {"content": "Quiero crear una API REST", "type": "user"}
        ]
        
        saved_messages = []
        for i, msg_data in enumerate(messages):
            logger.info(f"  Guardando mensaje {i+1}: {msg_data['content'][:30]}...")
            
            message = memory_manager.save_message(
                conversation_id=conversation.conversation_id,
                user_id=user.user_id,
                content=msg_data['content'],
                message_type=msg_data['type'],
                slack_message_ts=f"1234567890.{str(i+2).zfill(3)}",
                metadata={'sequence': i+1, 'test': True}
            )
            
            if message:
                saved_messages.append(message)
                logger.info(f"    ✅ Mensaje {i+1} guardado")
            else:
                logger.error(f"    ❌ Error guardando mensaje {i+1}")
                return False
        
        logger.info(f"✅ {len(saved_messages)} mensajes guardados")
        
        # 4. Verificar historial y continuidad
        logger.info("📚 Verificando historial...")
        history = memory_manager.get_conversation_history(
            conversation.conversation_id,
            limit=10
        )
        
        logger.info(f"📊 Mensajes en historial: {len(history)}")
        
        if len(history) != len(messages):
            logger.error(f"❌ Esperaba {len(messages)} mensajes, encontré {len(history)}")
            return False
        
        # Verificar orden cronológico y contenido
        for i, msg in enumerate(history):
            expected_content = messages[i]['content']
            actual_content = msg.get('content', '')
            
            if actual_content != expected_content:
                logger.error(f"❌ Mensaje {i+1} no coincide:")
                logger.error(f"    Esperado: {expected_content}")
                logger.error(f"    Actual: {actual_content}")
                return False
            
            logger.info(f"  ✅ Mensaje {i+1}: {msg.get('message_type')} - {actual_content[:50]}...")
        
        # 5. Verificar datos en BigQuery directamente
        logger.info("🔍 Verificando datos en BigQuery...")
        
        # Verificar tabla users
        users_info = bq_client.get_table_info('users')
        if users_info and users_info['num_rows'] > 0:
            logger.info(f"✅ Tabla users: {users_info['num_rows']} filas")
        else:
            logger.warning("⚠️ Tabla users vacía o no accesible")
        
        # Verificar tabla conversations
        conversations_info = bq_client.get_table_info('conversations')
        if conversations_info and conversations_info['num_rows'] > 0:
            logger.info(f"✅ Tabla conversations: {conversations_info['num_rows']} filas")
        else:
            logger.warning("⚠️ Tabla conversations vacía o no accesible")
        
        # Verificar tabla messages
        messages_info = bq_client.get_table_info('messages')
        if messages_info and messages_info['num_rows'] > 0:
            logger.info(f"✅ Tabla messages: {messages_info['num_rows']} filas")
        else:
            logger.warning("⚠️ Tabla messages vacía o no accesible")
        
        # 6. Test de recuperación de conversación existente
        logger.info("🔄 Probando recuperación de conversación existente...")
        existing_conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id='C_COMPLETE',
            slack_thread_ts='1234567890.001'
        )
        
        if existing_conversation.conversation_id == conversation.conversation_id:
            logger.info("✅ Conversación existente recuperada correctamente")
        else:
            logger.error("❌ Error recuperando conversación existente")
            return False
        
        logger.info("🎉 ¡SISTEMA DE MEMORIA FUNCIONANDO CORRECTAMENTE!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 INICIANDO TEST COMPLETO DE MEMORIA")
    logger.info("=" * 60)
    
    success = test_complete_memory_system()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 ¡TEST COMPLETO EXITOSO!")
        logger.info("✅ El sistema de memoria persistente está funcionando correctamente")
    else:
        logger.error("❌ TEST COMPLETO FALLÓ")
        logger.error("❌ Hay problemas con el sistema de memoria")
    logger.info("=" * 60)