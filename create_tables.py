#!/usr/bin/env python3
"""
Script para crear las tablas de BigQuery para memoria persistente.
Ejecuta este script para inicializar la base de datos.
"""

import sys
import os
import logging
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.memory_manager import MemoryManager
from src.utils.bigquery_client import BigQueryClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Función principal para crear las tablas."""
    try:
        logger.info("Iniciando creación de tablas de BigQuery...")
        
        # Verificar variables de entorno
        required_env_vars = [
            'BIGQUERY_PROJECT_ID',
            'BIGQUERY_DATASET',
            'GOOGLE_APPLICATION_CREDENTIALS_JSON'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {missing_vars}")
            return False
        
        # Crear cliente de BigQuery
        logger.info("Creando cliente de BigQuery...")
        bq_client = BigQueryClient()
        
        # Crear tablas
        logger.info("Creando tablas...")
        success = bq_client.create_tables()
        
        if success:
            logger.info("✅ Tablas creadas exitosamente!")
            
            # Verificar tablas creadas
            tables = ['users', 'conversations', 'messages', 'context']
            for table_name in tables:
                info = bq_client.get_table_info(table_name)
                if info:
                    logger.info(f"📊 Tabla '{table_name}': {info['num_rows']} filas, {info['num_bytes']} bytes")
                else:
                    logger.warning(f"⚠️  No se pudo obtener información de la tabla '{table_name}'")
            
            return True
        else:
            logger.error("❌ Error creando tablas")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en la creación de tablas: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)