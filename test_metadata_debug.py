#!/usr/bin/env python3
"""
Test para debuggear el problema con metadata
"""

import os
import sys
import logging
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging simple
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_metadata_formats():
    """Test diferentes formatos de metadata"""
    logger.info("🧪 Test de formatos de metadata...")
    
    try:
        from utils.bigquery_client import BigQueryClient
        
        # Crear cliente BigQuery
        bq_client = BigQueryClient()
        logger.info("✅ Cliente BigQuery creado")
        
        # Test 1: metadata como None
        logger.info("📝 Test 1: metadata como None")
        test_data_1 = {
            'message_id': 'test_msg_1',
            'conversation_id': 'test_conv_1',
            'user_id': 'test_user_1',
            'slack_message_ts': '1234567890.001',
            'message_type': 'user',
            'content': 'Test message 1',
            'metadata': None,
            'tokens_used': None,
            'model_used': None,
            'response_time_ms': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result_1 = bq_client.insert_rows('messages', [test_data_1])
        logger.info(f"Resultado 1: {result_1}")
        
        # Test 2: metadata como dict vacío
        logger.info("📝 Test 2: metadata como dict vacío")
        test_data_2 = {
            'message_id': 'test_msg_2',
            'conversation_id': 'test_conv_2',
            'user_id': 'test_user_2',
            'slack_message_ts': '1234567890.002',
            'message_type': 'user',
            'content': 'Test message 2',
            'metadata': {},
            'tokens_used': None,
            'model_used': None,
            'response_time_ms': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result_2 = bq_client.insert_rows('messages', [test_data_2])
        logger.info(f"Resultado 2: {result_2}")
        
        # Test 3: metadata con datos
        logger.info("📝 Test 3: metadata con datos")
        test_data_3 = {
            'message_id': 'test_msg_3',
            'conversation_id': 'test_conv_3',
            'user_id': 'test_user_3',
            'slack_message_ts': '1234567890.003',
            'message_type': 'user',
            'content': 'Test message 3',
            'metadata': {'test_key': 'test_value', 'number': 123},
            'tokens_used': None,
            'model_used': None,
            'response_time_ms': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result_3 = bq_client.insert_rows('messages', [test_data_3])
        logger.info(f"Resultado 3: {result_3}")
        
        # Test 4: sin campo metadata
        logger.info("📝 Test 4: sin campo metadata")
        test_data_4 = {
            'message_id': 'test_msg_4',
            'conversation_id': 'test_conv_4',
            'user_id': 'test_user_4',
            'slack_message_ts': '1234567890.004',
            'message_type': 'user',
            'content': 'Test message 4',
            # NO incluir metadata
            'tokens_used': None,
            'model_used': None,
            'response_time_ms': None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        result_4 = bq_client.insert_rows('messages', [test_data_4])
        logger.info(f"Resultado 4: {result_4}")
        
        return True
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 INICIANDO TEST DE METADATA")
    logger.info("=" * 40)
    
    success = test_metadata_formats()
    
    logger.info("=" * 40)
    if success:
        logger.info("🎉 ¡TEST COMPLETADO!")
    else:
        logger.error("❌ TEST FALLÓ")
    logger.info("=" * 40)