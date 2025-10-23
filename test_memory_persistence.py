#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de la memoria persistente.
Simula interacciones de usuario y verifica que los datos se guarden correctamente en BigQuery.
"""

import os
import sys
import json
import uuid
import asyncio
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryPersistenceTest:
    """Clase para probar la persistencia de memoria."""
    
    def __init__(self):
        """Inicializa el test."""
        self.memory_manager = None
        self.bq_client = None
        self.test_user_id = None
        self.test_conversation_id = None
        
    async def setup(self):
        """Configura el entorno de prueba."""
        try:
            logger.info("🚀 Iniciando configuración de pruebas...")
            
            # Inicializar MemoryManager
            self.memory_manager = MemoryManager()
            self.bq_client = BigQueryClient()
            
            logger.info("✅ Configuración completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en configuración: {e}")
            return False
    
    def test_user_creation(self):
        """Prueba la creación y actualización de usuarios."""
        try:
            logger.info("👤 Probando creación de usuario...")
            
            # Simular datos de usuario de Slack
            slack_user_info = {
                'id': f'U{uuid.uuid4().hex[:8].upper()}',
                'real_name': 'Usuario de Prueba',
                'profile': {
                    'display_name': 'Test User',
                    'email': 'test@example.com',
                    'image_192': 'https://example.com/avatar.jpg'
                },
                'team_id': 'T12345678',
                'tz': 'America/Mexico_City',
                'is_admin': False,
                'is_bot': False
            }
            
            # Crear usuario
            user = self.memory_manager.create_or_update_user(slack_user_info)
            
            if user:
                self.test_user_id = user.user_id
                logger.info(f"✅ Usuario creado exitosamente: {user.user_id}")
                
                # Verificar que se puede recuperar
                retrieved_user = self.memory_manager.get_user_by_slack_id(slack_user_info['id'])
                if retrieved_user:
                    logger.info("✅ Usuario recuperado exitosamente")
                    return True
                else:
                    logger.error("❌ No se pudo recuperar el usuario")
                    return False
            else:
                logger.error("❌ No se pudo crear el usuario")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando creación de usuario: {e}")
            return False
    
    def test_conversation_creation(self):
        """Prueba la creación de conversaciones."""
        try:
            logger.info("💬 Probando creación de conversación...")
            
            if not self.test_user_id:
                logger.error("❌ No hay usuario de prueba disponible")
                return False
            
            # Crear conversación
            conversation = self.memory_manager.create_conversation(
                user_id=self.test_user_id,
                slack_channel_id="C12345678",
                conversation_type="channel"
            )
            
            if conversation:
                self.test_conversation_id = conversation.conversation_id
                logger.info(f"✅ Conversación creada exitosamente: {conversation.conversation_id}")
                return True
            else:
                logger.error("❌ No se pudo crear la conversación")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando creación de conversación: {e}")
            return False
    
    def test_message_saving(self):
        """Prueba el guardado de mensajes."""
        try:
            logger.info("📝 Probando guardado de mensajes...")
            
            if not self.test_conversation_id or not self.test_user_id:
                logger.error("❌ No hay conversación o usuario de prueba disponible")
                return False
            
            # Guardar mensaje de usuario
            user_message = self.memory_manager.save_message(
                conversation_id=self.test_conversation_id,
                user_id=self.test_user_id,
                content="Hola, este es un mensaje de prueba",
                message_type="user",
                slack_message_ts="1234567890.123456"
            )
            
            if not user_message:
                logger.error("❌ No se pudo guardar el mensaje de usuario")
                return False
            
            logger.info("✅ Mensaje de usuario guardado exitosamente")
            
            # Guardar mensaje del asistente
            assistant_message = self.memory_manager.save_message(
                conversation_id=self.test_conversation_id,
                user_id=self.test_user_id,
                content="¡Hola! Este es mi respuesta de prueba",
                message_type="assistant",
                tokens_used=25,
                model_used="claude-3-sonnet-20240229",
                response_time_ms=1500
            )
            
            if not assistant_message:
                logger.error("❌ No se pudo guardar el mensaje del asistente")
                return False
            
            logger.info("✅ Mensaje del asistente guardado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error probando guardado de mensajes: {e}")
            return False
    
    def test_conversation_history(self):
        """Prueba la recuperación del historial de conversación."""
        try:
            logger.info("📚 Probando recuperación de historial...")
            
            if not self.test_conversation_id:
                logger.error("❌ No hay conversación de prueba disponible")
                return False
            
            # Obtener historial
            history = self.memory_manager.get_conversation_history(
                conversation_id=self.test_conversation_id,
                limit=10
            )
            
            if history:
                logger.info(f"✅ Historial recuperado: {len(history)} mensajes")
                
                # Verificar que los mensajes están en orden cronológico
                for i, message in enumerate(history):
                    logger.info(f"  {i+1}. [{message['message_type']}] {message['content'][:50]}...")
                
                return len(history) >= 2  # Esperamos al menos 2 mensajes
            else:
                logger.error("❌ No se pudo recuperar el historial")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando recuperación de historial: {e}")
            return False
    
    def test_context_saving(self):
        """Prueba el guardado de contexto."""
        try:
            logger.info("🧠 Probando guardado de contexto...")
            
            if not self.test_conversation_id or not self.test_user_id:
                logger.error("❌ No hay conversación o usuario de prueba disponible")
                return False
            
            # Guardar contexto
            context_data = {
                "user_preferences": {
                    "language": "es",
                    "tone": "friendly"
                },
                "conversation_summary": "El usuario está probando el sistema de memoria",
                "key_topics": ["testing", "memory", "persistence"]
            }
            
            context = self.memory_manager.save_context(
                conversation_id=self.test_conversation_id,
                user_id=self.test_user_id,
                context_type="summary",
                context_data=context_data,
                relevance_score=0.9
            )
            
            if context:
                logger.info("✅ Contexto guardado exitosamente")
                
                # Recuperar contexto
                user_context = self.memory_manager.get_user_context(
                    user_id=self.test_user_id,
                    context_types=["summary"]
                )
                
                if user_context:
                    logger.info(f"✅ Contexto recuperado: {len(user_context)} registros")
                    return True
                else:
                    logger.error("❌ No se pudo recuperar el contexto")
                    return False
            else:
                logger.error("❌ No se pudo guardar el contexto")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando guardado de contexto: {e}")
            return False
    
    def verify_bigquery_data(self):
        """Verifica que los datos estén correctamente en BigQuery."""
        try:
            logger.info("🔍 Verificando datos en BigQuery...")
            
            # Verificar tabla users
            users_info = self.bq_client.get_table_info('users')
            logger.info(f"📊 Tabla 'users': {users_info.get('num_rows', 0)} filas")
            
            # Verificar tabla conversations
            conversations_info = self.bq_client.get_table_info('conversations')
            logger.info(f"📊 Tabla 'conversations': {conversations_info.get('num_rows', 0)} filas")
            
            # Verificar tabla messages
            messages_info = self.bq_client.get_table_info('messages')
            logger.info(f"📊 Tabla 'messages': {messages_info.get('num_rows', 0)} filas")
            
            # Verificar tabla context
            context_info = self.bq_client.get_table_info('context')
            logger.info(f"📊 Tabla 'context': {context_info.get('num_rows', 0)} filas")
            
            # Verificar que hay datos
            total_rows = (
                users_info.get('num_rows', 0) +
                conversations_info.get('num_rows', 0) +
                messages_info.get('num_rows', 0) +
                context_info.get('num_rows', 0)
            )
            
            if total_rows > 0:
                logger.info(f"✅ Verificación exitosa: {total_rows} filas totales en BigQuery")
                return True
            else:
                logger.error("❌ No se encontraron datos en BigQuery")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verificando datos en BigQuery: {e}")
            return False
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        logger.info("🧪 Iniciando pruebas de memoria persistente...")
        
        # Configurar
        if not await self.setup():
            logger.error("❌ Falló la configuración inicial")
            return False
        
        # Ejecutar pruebas
        tests = [
            ("Creación de usuario", self.test_user_creation),
            ("Creación de conversación", self.test_conversation_creation),
            ("Guardado de mensajes", self.test_message_saving),
            ("Recuperación de historial", self.test_conversation_history),
            ("Guardado de contexto", self.test_context_saving),
            ("Verificación BigQuery", self.verify_bigquery_data)
        ]
        
        results = {}
        for test_name, test_func in tests:
            logger.info(f"\n🔬 Ejecutando: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    logger.info(f"✅ {test_name}: PASÓ")
                else:
                    logger.error(f"❌ {test_name}: FALLÓ")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Resumen
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        logger.info(f"\n📊 RESUMEN DE PRUEBAS:")
        logger.info(f"✅ Pasaron: {passed}/{total}")
        logger.info(f"❌ Fallaron: {total - passed}/{total}")
        
        if passed == total:
            logger.info("🎉 ¡TODAS LAS PRUEBAS PASARON! La memoria persistente funciona correctamente.")
            return True
        else:
            logger.error("⚠️ Algunas pruebas fallaron. Revisar la configuración.")
            return False

async def main():
    """Función principal."""
    test = MemoryPersistenceTest()
    success = await test.run_all_tests()
    return success

if __name__ == "__main__":
    asyncio.run(main())