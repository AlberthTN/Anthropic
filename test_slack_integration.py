#!/usr/bin/env python3
"""
Script para probar la integración completa del bot de Slack con BigQuery
Simula un mensaje de Slack y verifica que se inserte correctamente en la base de datos.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.memory_manager import MemoryManager
from utils.bigquery_client import BigQueryClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_slack_integration():
    """Prueba la integración completa del bot de Slack con BigQuery."""
    
    print("🧪 INICIANDO PRUEBA DE INTEGRACIÓN SLACK-BIGQUERY")
    print("=" * 60)
    
    try:
        # 1. Inicializar MemoryManager
        print("\n1️⃣ Inicializando MemoryManager...")
        memory_manager = MemoryManager()
        print("✅ MemoryManager inicializado correctamente")
        
        # 2. Simular datos de usuario de Slack
        print("\n2️⃣ Simulando usuario de Slack...")
        slack_user_info = {
            'id': 'U12345TEST',  # Cambiar 'slack_id' por 'id'
            'real_name': 'Usuario de Prueba',
            'display_name': 'test_user',
            'email': 'test@example.com',
            'timezone': 'America/Mexico_City',
            'is_bot': False
        }
        
        # 3. Crear/actualizar usuario
        print("3️⃣ Creando/actualizando usuario...")
        memory_manager.create_or_update_user(slack_user_info)
        print("✅ Usuario creado/actualizado correctamente")
        
        # 4. Obtener el usuario por Slack ID
        print("4️⃣ Obteniendo usuario por Slack ID...")
        user_obj = memory_manager.get_user_by_slack_id('U12345TEST')
        if not user_obj:
            raise Exception("❌ No se pudo obtener el usuario creado")
        
        print(f"✅ Usuario obtenido: {user_obj['user_id']}")
        user_id = user_obj['user_id']
        
        # 5. Crear conversación
        print("5️⃣ Creando conversación...")
        conversation = memory_manager.get_or_create_conversation(
            user_id=user_id,
            slack_channel_id='C12345TEST'
        )
        
        if not conversation:
            raise Exception("❌ No se pudo crear la conversación")
        
        print(f"✅ Conversación creada: {conversation.conversation_id}")
        conversation_id = conversation.conversation_id
        
        # 6. Guardar mensaje del usuario
        print("6️⃣ Guardando mensaje del usuario...")
        memory_manager.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            message_type="user",
            content="Hola, este es un mensaje de prueba desde Slack",
            slack_message_ts="1234567890.123456"
        )
        print("✅ Mensaje del usuario guardado")
        
        # 7. Guardar respuesta del bot
        print("7️⃣ Guardando respuesta del bot...")
        memory_manager.save_message(
            conversation_id=conversation_id,
            user_id=user_id,
            message_type="assistant",
            content="¡Hola! He recibido tu mensaje correctamente. La integración con BigQuery está funcionando.",
            metadata={"response_time": 1.5, "model": "claude-3-sonnet"}
        )
        print("✅ Respuesta del bot guardada")
        
        # 8. Verificar datos en BigQuery
        print("\n8️⃣ Verificando datos en BigQuery...")
        verify_data_in_bigquery(memory_manager, user_id, conversation_id)
        
        print("\n🎉 PRUEBA DE INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("✅ Usuario creado correctamente")
        print("✅ Conversación creada correctamente") 
        print("✅ Mensajes guardados correctamente")
        print("✅ Datos verificados en BigQuery")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_data_in_bigquery(memory_manager: MemoryManager, user_id: str, conversation_id: str):
    """Verifica que los datos se hayan insertado correctamente en BigQuery."""
    
    bq_client = memory_manager.bq_client
    
    # Verificar usuario
    print("   📋 Verificando usuario en BigQuery...")
    user_query = f"""
    SELECT * FROM `{bq_client.project_id}.{bq_client.dataset_id}.users`
    WHERE user_id = '{user_id}'
    """
    
    user_results = list(bq_client.client.query(user_query).result())
    if not user_results:
        raise Exception("❌ Usuario no encontrado en BigQuery")
    
    print(f"   ✅ Usuario encontrado: {user_results[0]['real_name']}")
    
    # Verificar conversación
    print("   💬 Verificando conversación en BigQuery...")
    conversation_query = f"""
    SELECT * FROM `{bq_client.project_id}.{bq_client.dataset_id}.conversations`
    WHERE conversation_id = '{conversation_id}'
    """
    
    conversation_results = list(bq_client.client.query(conversation_query).result())
    if not conversation_results:
        raise Exception("❌ Conversación no encontrada en BigQuery")
    
    print(f"   ✅ Conversación encontrada: {conversation_results[0]['conversation_type']}")
    
    # Verificar mensajes
    print("   💭 Verificando mensajes en BigQuery...")
    messages_query = f"""
    SELECT * FROM `{bq_client.project_id}.{bq_client.dataset_id}.messages`
    WHERE conversation_id = '{conversation_id}'
    ORDER BY created_at
    """
    
    message_results = list(bq_client.client.query(messages_query).result())
    if len(message_results) < 2:
        raise Exception(f"❌ Se esperaban 2 mensajes, se encontraron {len(message_results)}")
    
    print(f"   ✅ {len(message_results)} mensajes encontrados:")
    for i, msg in enumerate(message_results, 1):
        print(f"      {i}. Tipo: {msg['message_type']}, Contenido: {msg['content'][:50]}...")

def cleanup_test_data():
    """Limpia los datos de prueba de BigQuery."""
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        bq_client = BigQueryClient()
        
        # Eliminar mensajes de prueba
        delete_messages_query = f"""
        DELETE FROM `{bq_client.project_id}.{bq_client.dataset_id}.messages`
        WHERE conversation_id IN (
            SELECT conversation_id FROM `{bq_client.project_id}.{bq_client.dataset_id}.conversations`
            WHERE slack_channel_id = 'C12345TEST'
        )
        """
        bq_client.client.query(delete_messages_query).result()
        
        # Eliminar conversaciones de prueba
        delete_conversations_query = f"""
        DELETE FROM `{bq_client.project_id}.{bq_client.dataset_id}.conversations`
        WHERE slack_channel_id = 'C12345TEST'
        """
        bq_client.client.query(delete_conversations_query).result()
        
        # Eliminar usuarios de prueba
        delete_users_query = f"""
        DELETE FROM `{bq_client.project_id}.{bq_client.dataset_id}.users`
        WHERE slack_user_id = 'U12345TEST'
        """
        bq_client.client.query(delete_users_query).result()
        
        print("✅ Datos de prueba eliminados correctamente")
        
    except Exception as e:
        print(f"⚠️ Error limpiando datos de prueba: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBA DE INTEGRACIÓN SLACK-BIGQUERY")
    print("=" * 60)
    
    success = test_slack_integration()
    
    if success:
        print("\n¿Deseas limpiar los datos de prueba? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', 's', 'si']:
                cleanup_test_data()
        except KeyboardInterrupt:
            print("\n\n👋 Prueba finalizada")
    
    print("\n" + "=" * 60)
    print("🏁 PRUEBA FINALIZADA")