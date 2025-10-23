#!/usr/bin/env python3
"""
Test simple de inserción de mensajes
"""

import os
import sys
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

def test_simple_message():
    """Test simple de mensaje sin metadata"""
    logger.info("🧪 Test simple de mensaje...")
    
    try:
        from utils.memory_manager import MemoryManager
        
        # Crear MemoryManager
        memory_manager = MemoryManager()
        logger.info("✅ MemoryManager creado")
        
        # Crear usuario simple
        slack_user_info = {
            'id': 'U_SIMPLE_TEST',
            'real_name': 'Simple Test User',
            'profile': {},
            'team_id': 'T_TEST',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(slack_user_info)
        logger.info(f"✅ Usuario: {user.user_id}")
        
        # Crear conversación
        conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id='C_SIMPLE',
            slack_thread_ts='1234567890.001'
        )
        logger.info(f"✅ Conversación: {conversation.conversation_id}")
        
        # Guardar mensaje SIN metadata
        logger.info("💾 Guardando mensaje sin metadata...")
        message_saved = memory_manager.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
            content="Mensaje simple de prueba",
            message_type="user"
            # NO incluir metadata
        )
        
        if message_saved:
            logger.info("✅ Mensaje guardado exitosamente")
            
            # Verificar historial
            history = memory_manager.get_conversation_history(
                conversation.conversation_id,
                limit=5
            )
            
            logger.info(f"📊 Mensajes en historial: {len(history)}")
            
            if len(history) > 0:
                logger.info("🎉 ¡MENSAJE GUARDADO CORRECTAMENTE!")
                return True
            else:
                logger.error("❌ No se encontró el mensaje en el historial")
                return False
        else:
            logger.error("❌ Error guardando mensaje")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 INICIANDO TEST SIMPLE DE MENSAJE")
    logger.info("=" * 40)
    
    success = test_simple_message()
    
    logger.info("=" * 40)
    if success:
        logger.info("🎉 ¡TEST EXITOSO!")
    else:
        logger.error("❌ TEST FALLÓ")
    logger.info("=" * 40)