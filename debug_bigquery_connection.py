#!/usr/bin/env python3
"""
Script de debug para diagnosticar problemas de conexión con BigQuery
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_environment_variables():
    """Debug de variables de entorno"""
    logger.info("🔍 Verificando variables de entorno...")
    
    required_vars = [
        'BIGQUERY_PROJECT_ID',
        'BIGQUERY_DATASET', 
        'GOOGLE_APPLICATION_CREDENTIALS_JSON'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'GOOGLE_APPLICATION_CREDENTIALS_JSON':
                # Solo mostrar los primeros caracteres para seguridad
                logger.info(f"✅ {var}: {value[:50]}...")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: NO DEFINIDA")

def debug_credentials():
    """Debug de credenciales JSON"""
    logger.info("🔐 Verificando credenciales JSON...")
    
    credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not credentials_json:
        logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON no está definida")
        return False
    
    try:
        credentials_info = json.loads(credentials_json)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field in credentials_info:
                if field == 'private_key':
                    logger.info(f"✅ {field}: [PRESENTE - {len(credentials_info[field])} caracteres]")
                else:
                    logger.info(f"✅ {field}: {credentials_info[field]}")
            else:
                logger.error(f"❌ {field}: FALTANTE")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error parseando JSON: {e}")
        return False

def debug_google_cloud_import():
    """Debug de importación de Google Cloud"""
    logger.info("📦 Verificando importación de Google Cloud...")
    
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        logger.info("✅ Librerías de Google Cloud importadas correctamente")
        return True
    except ImportError as e:
        logger.error(f"❌ Error importando Google Cloud: {e}")
        return False

def debug_bigquery_client():
    """Debug de cliente BigQuery"""
    logger.info("🔧 Probando inicialización de cliente BigQuery...")
    
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        credentials_info = json.loads(credentials_json)
        
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        project_id = os.getenv('BIGQUERY_PROJECT_ID')
        location = os.getenv('BIGQUERY_LOCATION', 'us-central1')
        
        client = bigquery.Client(
            credentials=credentials,
            project=project_id,
            location=location
        )
        
        logger.info("✅ Cliente BigQuery creado exitosamente")
        
        # Probar conexión básica
        logger.info("🔗 Probando conexión básica...")
        datasets = list(client.list_datasets(max_results=1))
        logger.info(f"✅ Conexión exitosa - Datasets disponibles: {len(datasets)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando cliente BigQuery: {e}")
        logger.error(f"❌ Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando debug de conexión BigQuery...")
    
    print("\n" + "="*60)
    print("DEBUG BIGQUERY CONNECTION")
    print("="*60)
    
    # Test 1: Variables de entorno
    print("\n1. VARIABLES DE ENTORNO:")
    debug_environment_variables()
    
    # Test 2: Credenciales JSON
    print("\n2. CREDENCIALES JSON:")
    creds_ok = debug_credentials()
    
    # Test 3: Importación de librerías
    print("\n3. IMPORTACIÓN DE LIBRERÍAS:")
    import_ok = debug_google_cloud_import()
    
    # Test 4: Cliente BigQuery
    if creds_ok and import_ok:
        print("\n4. CLIENTE BIGQUERY:")
        client_ok = debug_bigquery_client()
    else:
        logger.error("❌ Saltando test de cliente por errores previos")
        client_ok = False
    
    print("\n" + "="*60)
    if client_ok:
        print("🎉 DIAGNÓSTICO COMPLETO: TODO OK")
    else:
        print("❌ DIAGNÓSTICO COMPLETO: HAY PROBLEMAS")
    print("="*60)