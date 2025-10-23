#!/usr/bin/env python3
"""
Test simple de conexión a BigQuery
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_environment():
    """Test de variables de entorno"""
    logger.info("🔧 Verificando variables de entorno...")
    
    required_vars = [
        'BIGQUERY_PROJECT_ID',
        'BIGQUERY_DATASET',
        'GOOGLE_APPLICATION_CREDENTIALS_JSON'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'GOOGLE_APPLICATION_CREDENTIALS_JSON':
                logger.info(f"✅ {var}: [JSON presente - {len(value)} caracteres]")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: No definida")
            return False
    
    return True

def test_bigquery_client():
    """Test de cliente BigQuery"""
    logger.info("🔧 Inicializando cliente BigQuery...")
    
    try:
        from utils.bigquery_client import BigQueryClient
        
        # Crear cliente
        bq_client = BigQueryClient()
        logger.info("✅ Cliente BigQuery creado")
        
        # Test de conexión
        logger.info("🔗 Probando conexión...")
        try:
            bq_client._test_connection()
            logger.info("✅ Conexión exitosa")
            return True
        except Exception as e:
            logger.error(f"❌ Error en conexión: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creando cliente: {e}")
        return False

def test_google_cloud_direct():
    """Test directo de Google Cloud"""
    logger.info("🔧 Test directo de Google Cloud...")
    
    try:
        import json
        from google.cloud import bigquery
        from google.oauth2 import service_account
        
        # Obtener credenciales
        creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not creds_json:
            logger.error("❌ No hay credenciales JSON")
            return False
        
        # Parsear credenciales
        try:
            creds_dict = json.loads(creds_json)
            logger.info("✅ Credenciales JSON parseadas")
        except Exception as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            return False
        
        # Crear credenciales
        try:
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            logger.info("✅ Credenciales de servicio creadas")
        except Exception as e:
            logger.error(f"❌ Error creando credenciales: {e}")
            return False
        
        # Crear cliente
        try:
            project_id = os.getenv('BIGQUERY_PROJECT_ID')
            client = bigquery.Client(credentials=credentials, project=project_id)
            logger.info("✅ Cliente BigQuery directo creado")
        except Exception as e:
            logger.error(f"❌ Error creando cliente directo: {e}")
            return False
        
        # Test de conexión
        try:
            datasets = list(client.list_datasets(max_results=1))
            logger.info(f"✅ Conexión directa exitosa - Datasets encontrados: {len(datasets)}")
            return True
        except Exception as e:
            logger.error(f"❌ Error en conexión directa: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en test directo: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Iniciando tests de conexión...")
    
    # Test 1: Variables de entorno
    logger.info("\n=== TEST 1: Variables de entorno ===")
    env_ok = test_environment()
    
    if not env_ok:
        logger.error("❌ Variables de entorno no configuradas correctamente")
        sys.exit(1)
    
    # Test 2: Cliente BigQuery
    logger.info("\n=== TEST 2: Cliente BigQuery ===")
    client_ok = test_bigquery_client()
    
    # Test 3: Google Cloud directo
    logger.info("\n=== TEST 3: Google Cloud directo ===")
    direct_ok = test_google_cloud_direct()
    
    # Resumen
    logger.info("\n=== RESUMEN ===")
    logger.info(f"Variables de entorno: {'✅' if env_ok else '❌'}")
    logger.info(f"Cliente BigQuery: {'✅' if client_ok else '❌'}")
    logger.info(f"Google Cloud directo: {'✅' if direct_ok else '❌'}")
    
    if env_ok and (client_ok or direct_ok):
        logger.info("🎉 Conexión a BigQuery funcional")
    else:
        logger.error("❌ Problemas con la conexión a BigQuery")