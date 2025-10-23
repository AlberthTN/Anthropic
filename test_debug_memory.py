#!/usr/bin/env python3
"""
Test detallado para debuggear MemoryManager
"""

import os
import sys
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

def test_memory_step_by_step():
    """Test paso a paso del MemoryManager"""
    logger.info("🧪 Test detallado de MemoryManager...")
    
    try:
        logger.info("📦 Importando MemoryManager...")
        from utils.memory_manager import MemoryManager
        logger.info("✅ MemoryManager importado")
        
        logger.info("🔧 Creando instancia de MemoryManager...")
        memory_manager = MemoryManager()
        logger.info("✅ MemoryManager creado")
        
        logger.info("👤 Creando usuario de prueba...")
        slack_user_info = {
            'id': 'U_DEBUG_TEST',
            'real_name': 'Debug Test User',
            'profile': {'email': 'debug@test.com'},
            'team_id': 'T_DEBUG',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(slack_user_info)
        logger.info(f"✅ Usuario creado: {user.user_id}")
        
        logger.info("💬 Creando conversación...")
        conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id='C_DEBUG',
            slack_thread_ts='1234567890.001'
        )
        logger.info(f"✅ Conversación creada: {conversation.conversation_id}")
        
        logger.info("💾 Guardando mensaje...")
        message_saved = memory_manager.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
            content="Mensaje de debug",
            message_type="user"
        )
        
        if message_saved:
            logger.info(f"✅ Mensaje guardado: {message_saved.message_id}")
            
            logger.info("📚 Obteniendo historial...")
            history = memory_manager.get_conversation_history(
                conversation.conversation_id,
                limit=5
            )
            
            logger.info(f"📊 Mensajes en historial: {len(history)}")
            for i, msg in enumerate(history):
                logger.info(f"  {i+1}. {msg.get('message_type', 'unknown')}: {msg.get('content', '')[:50]}...")
            
            if len(history) > 0:
                logger.info("🎉 ¡TEST EXITOSO!")
                return True
            else:
                logger.error("❌ No se encontraron mensajes en el historial")
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
    print("🚀 INICIANDO TEST DETALLADO DE MEMORIA")
    print("=" * 50)
    
    success = test_memory_step_by_step()
    
    print("=" * 50)
    if success:
        print("🎉 ¡TEST EXITOSO!")
    else:
        print("❌ TEST FALLÓ")
    print("=" * 50)