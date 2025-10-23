#!/usr/bin/env python3
"""
Test simple de debug del sistema de memoria
"""

import os
import sys
import uuid
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🚀 INICIANDO TEST SIMPLE DE DEBUG")
    print("=" * 50)
    
    # Generar ID único
    test_id = str(uuid.uuid4())[:8]
    print(f"🆔 Test ID: {test_id}")
    
    try:
        print("📦 Importando MemoryManager...")
        from utils.memory_manager import MemoryManager
        print("✅ MemoryManager importado")
        
        print("🔧 Creando instancia...")
        memory_manager = MemoryManager()
        print("✅ MemoryManager creado")
        
        # Crear usuario
        user_id = f'U_DEBUG_{test_id}'
        print(f"👤 Creando usuario: {user_id}")
        
        slack_user_info = {
            'id': user_id,
            'real_name': f'Debug User {test_id}',
            'profile': {'email': f'debug{test_id}@test.com'},
            'team_id': f'T_DEBUG_{test_id}',
            'tz': 'UTC',
            'is_admin': False,
            'is_bot': False
        }
        
        user = memory_manager.create_or_update_user(slack_user_info)
        print(f"✅ Usuario creado: {user.user_id}")
        
        # Crear conversación
        channel_id = f'C_DEBUG_{test_id}'
        print(f"💬 Creando conversación: {channel_id}")
        
        conversation = memory_manager.get_or_create_conversation(
            user_id=user.user_id,
            slack_channel_id=channel_id,
            slack_thread_ts=f'{test_id}.001'
        )
        print(f"✅ Conversación creada: {conversation.conversation_id}")
        
        # Guardar un mensaje
        print("💾 Guardando mensaje...")
        message = memory_manager.save_message(
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
            content=f"Mensaje de debug {test_id}",
            message_type="user",
            slack_message_ts=f'{test_id}.002'
        )
        
        if message:
            print(f"✅ Mensaje guardado: {message.message_id}")
        else:
            print("❌ Error guardando mensaje")
            return False
        
        # Verificar historial
        print("📚 Verificando historial...")
        history = memory_manager.get_conversation_history(
            conversation.conversation_id,
            limit=5
        )
        
        print(f"📊 Mensajes en historial: {len(history)}")
        
        if len(history) > 0:
            for i, msg in enumerate(history):
                print(f"  {i+1}. {msg.get('message_type')}: {msg.get('content', '')[:50]}...")
            print("✅ Historial recuperado correctamente")
        else:
            print("❌ No se encontraron mensajes en el historial")
            return False
        
        print("🎉 ¡TEST SIMPLE EXITOSO!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print("=" * 50)
    if success:
        print("🎯 TEST COMPLETADO EXITOSAMENTE")
    else:
        print("❌ TEST FALLÓ")