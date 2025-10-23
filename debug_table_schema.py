#!/usr/bin/env python3
"""
Script para consultar el esquema de la tabla agentes_slack en BigQuery
"""

import os
from google.cloud import bigquery
from google.oauth2 import service_account

def get_table_schema():
    """Consulta el esquema de la tabla agentes_slack"""
    try:
        # Configurar credenciales desde variables de entorno
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'neto-cloud')
        
        print(f"🔍 Consultando esquema de tabla...")
        print(f"   - Proyecto: {project_id}")
        print(f"   - Credenciales: {credentials_path}")
        
        # Inicializar cliente BigQuery
        if credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            client = bigquery.Client(project=project_id)
        
        # Referencia a la tabla
        table_ref = client.dataset('metricas_agentes').table('agentes_slack')
        table = client.get_table(table_ref)
        
        print(f"\n📊 Esquema de la tabla {table.full_table_id}:")
        print("=" * 60)
        
        for field in table.schema:
            print(f"  {field.name:<25} | {field.field_type:<12} | {field.mode}")
        
        print("=" * 60)
        print(f"Total de columnas: {len(table.schema)}")
        
        # Mostrar nombres de columnas como lista
        column_names = [field.name for field in table.schema]
        print(f"\nNombres de columnas:")
        for i, name in enumerate(column_names, 1):
            print(f"  {i:2d}. {name}")
            
        return column_names
        
    except Exception as e:
        print(f"❌ Error consultando esquema: {e}")
        return None

if __name__ == "__main__":
    schema = get_table_schema()
    if schema:
        print(f"\n✅ Esquema consultado exitosamente")
    else:
        print(f"\n❌ No se pudo consultar el esquema")