#!/usr/bin/env python3
"""
Test final de verificación del sistema de memoria con IDs únicos
"""

import os
import sys
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_final_memory_verification():
    """Test final de verificación del sistema de memoria"""
    logger.info("🧪 Test final de verificación del sistema de memoria...")
    
    # Generar IDs únicos para este test
    test_id = str(uuid.uuid4())[:8]
    user_id = f'U_FINAL_{test_id}'
    channel_id = f'C_FINAL_{test_id}'
    
    try:
        from utils.memory_manager import MemoryManager
        
        # Crear instancia
        memory_manager = MemoryManager()
        logger.info("✅ MemoryManager creado")
        
        # 1. Crear usuario único
        logger.info(f"👤 Creando usuario único: {user_id}")
        slack_user_info = {
            'id': user_id,
            'real_name': f'Final Test User {test_id}',
            'profile': {'email': f'final{test_id}@test.com'},
            'team_id': f'T_FINAL_{test_id}',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(slack_user_info)
        logger.info(f"✅ Usuario creado: {user.user_id}")
        
        # 2. Crear conversación única
        logger.info(f"💬 Creando conversación única: {channel_id}")
        conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id=channel_id,
            slack_thread_ts=f'{test_id}.001'
        )
        logger.info(f"✅ Conversación creada: {conversation.conversation_id}")
        
        # 3. Guardar mensajes de prueba
        logger.info("💾 Guardando mensajes de prueba...")
        test_messages = [
            {"content": f"Mensaje 1 del test {test_id}", "type": "user"},
            {"content": f"Respuesta 1 del test {test_id}", "type": "assistant"},
            {"content": f"Mensaje 2 del test {test_id}", "type": "user"}
        ]
        
        saved_count = 0
        for i, msg_data in enumerate(test_messages):
            logger.info(f"  Guardando: {msg_data['content']}")
            
            message = memory_manager.save_message(
                conversation_id=conversation.conversation_id,
                user_id=user.user_id,
                content=msg_data['content'],
                message_type=msg_data['type'],
                slack_message_ts=f'{test_id}.{str(i+2).zfill(3)}'
            )
            
            if message:
                saved_count += 1
                logger.info(f"    ✅ Guardado exitosamente")
            else:
                logger.error(f"    ❌ Error guardando mensaje")
                return False
        
        logger.info(f"✅ {saved_count} mensajes guardados")
        
        # 4. Verificar historial específico de esta conversación
        logger.info("📚 Verificando historial específico...")
        history = memory_manager.get_conversation_history(
            conversation.conversation_id,
            limit=10
        )
        
        logger.info(f"📊 Mensajes encontrados: {len(history)}")
        
        if len(history) != len(test_messages):
            logger.error(f"❌ Esperaba {len(test_messages)} mensajes, encontré {len(history)}")
            # Mostrar los mensajes encontrados para debug
            for i, msg in enumerate(history):
                logger.info(f"  {i+1}. {msg.get('message_type')}: {msg.get('content', '')}")
            return False
        
        # Verificar contenido de los mensajes
        logger.info("🔍 Verificando contenido de mensajes...")
        for i, msg in enumerate(history):
            expected_content = test_messages[i]['content']
            actual_content = msg.get('content', '')
            
            if actual_content == expected_content:
                logger.info(f"  ✅ Mensaje {i+1}: Correcto")
            else:
                logger.error(f"  ❌ Mensaje {i+1}: No coincide")
                logger.error(f"    Esperado: {expected_content}")
                logger.error(f"    Actual: {actual_content}")
                return False
        
        # 5. Test de recuperación de conversación
        logger.info("🔄 Probando recuperación de conversación...")
        recovered_conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id=channel_id,
            slack_thread_ts=f'{test_id}.001'
        )
        
        if recovered_conversation.conversation_id == conversation.conversation_id:
            logger.info("✅ Conversación recuperada correctamente")
        else:
            logger.error("❌ Error en recuperación de conversación")
            return False
        
        # 6. Agregar un mensaje más y verificar continuidad
        logger.info("➕ Agregando mensaje adicional...")
        additional_message = memory_manager.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
            content=f"Mensaje adicional del test {test_id}",
            message_type="user",
            slack_message_ts=f'{test_id}.004'
        )
        
        if additional_message:
            logger.info("✅ Mensaje adicional guardado")
            
            # Verificar que ahora hay 4 mensajes
            updated_history = memory_manager.get_conversation_history(
                conversation.conversation_id,
                limit=10
            )
            
            if len(updated_history) == 4:
                logger.info("✅ Continuidad de conversación verificada")
            else:
                logger.error(f"❌ Esperaba 4 mensajes, encontré {len(updated_history)}")
                return False
        else:
            logger.error("❌ Error guardando mensaje adicional")
            return False
        
        logger.info("🎉 ¡SISTEMA DE MEMORIA VERIFICADO EXITOSAMENTE!")
        logger.info("✅ Todas las funcionalidades están trabajando correctamente:")
        logger.info("  - Creación de usuarios ✅")
        logger.info("  - Creación de conversaciones ✅") 
        logger.info("  - Guardado de mensajes ✅")
        logger.info("  - Recuperación de historial ✅")
        logger.info("  - Continuidad de conversaciones ✅")
        logger.info("  - Recuperación de conversaciones existentes ✅")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 INICIANDO VERIFICACIÓN FINAL DEL SISTEMA DE MEMORIA")
    logger.info("=" * 70)
    
    success = test_final_memory_verification()
    
    logger.info("=" * 70)
    if success:
        logger.info("🎉 ¡VERIFICACIÓN FINAL EXITOSA!")
        logger.info("🎯 El sistema de memoria persistente está completamente funcional")
    else:
        logger.error("❌ VERIFICACIÓN FINAL FALLÓ")
        logger.error("❌ Hay problemas pendientes en el sistema de memoria")
    logger.info("=" * 70)