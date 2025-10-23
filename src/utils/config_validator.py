"""
Validador de configuración para el Claude Programming Agent.
Verifica que todas las variables de entorno y configuraciones necesarias estén presentes.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Resultado de la validación de configuración."""
    is_valid: bool
    missing_required: List[str]
    missing_optional: List[str]
    invalid_values: List[str]
    warnings: List[str]
    bigquery_available: bool

class ConfigValidator:
    """Validador de configuración del sistema."""
    
    # Variables requeridas para el funcionamiento básico
    REQUIRED_VARS = [
        "ANTHROPIC_API_KEY",
        "SLACK_BOT_TOKEN", 
        "SLACK_APP_TOKEN",
        "SLACK_SIGNING_SECRET"
    ]
    
    # Variables opcionales para funcionalidades adicionales
    OPTIONAL_VARS = [
        "WEBHOOK_PORT",
        "LOG_LEVEL",
        "HEALTH_CHECK_INTERVAL",
        "MAX_RETRIES"
    ]
    
    # Variables para BigQuery (memoria persistente)
    BIGQUERY_VARS = [
        "GOOGLE_APPLICATION_CREDENTIALS_JSON",
        "BIGQUERY_PROJECT_ID",
        "BIGQUERY_DATASET",
        "BIGQUERY_LOCATION",
        "BIGQUERY_MAX_BYTES_BILLED"
    ]
    
    @classmethod
    def validate_configuration(cls) -> ValidationResult:
        """
        Valida toda la configuración del sistema.
        
        Returns:
            ValidationResult: Resultado detallado de la validación
        """
        print("🔍 VALIDANDO CONFIGURACIÓN DEL SISTEMA")
        print("=" * 60)
        
        missing_required = []
        missing_optional = []
        invalid_values = []
        warnings = []
        
        # Validar variables requeridas
        print("\n📋 Variables Requeridas:")
        print("-" * 30)
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                missing_required.append(var)
                print(f"❌ {var}: NO CONFIGURADA")
            else:
                # Validar formato específico
                validation_error = cls._validate_variable_format(var, value)
                if validation_error:
                    invalid_values.append(f"{var}: {validation_error}")
                    print(f"⚠️ {var}: FORMATO INVÁLIDO - {validation_error}")
                else:
                    # Mostrar valor enmascarado por seguridad
                    masked_value = cls._mask_sensitive_value(var, value)
                    print(f"✅ {var}: {masked_value}")
        
        # Validar variables opcionales
        print("\n🔧 Variables Opcionales:")
        print("-" * 30)
        for var in cls.OPTIONAL_VARS:
            value = os.getenv(var)
            if not value:
                missing_optional.append(var)
                default_value = cls._get_default_value(var)
                print(f"⚠️ {var}: NO CONFIGURADA (usando por defecto: {default_value})")
            else:
                validation_error = cls._validate_variable_format(var, value)
                if validation_error:
                    invalid_values.append(f"{var}: {validation_error}")
                    print(f"⚠️ {var}: FORMATO INVÁLIDO - {validation_error}")
                else:
                    print(f"✅ {var}: {value}")
        
        # Validar configuración de BigQuery
        print("\n🗄️ Configuración de BigQuery (Memoria Persistente):")
        print("-" * 50)
        bigquery_available = cls._validate_bigquery_config(warnings)
        
        # Validaciones adicionales
        cls._validate_network_config(warnings)
        cls._validate_security_config(warnings)
        
        # Determinar si la configuración es válida
        is_valid = len(missing_required) == 0 and len(invalid_values) == 0
        
        # Mostrar resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 60)
        
        if is_valid:
            print("✅ Configuración válida para funcionamiento básico")
        else:
            print("❌ Configuración inválida - se requieren correcciones")
        
        if bigquery_available:
            print("✅ Memoria persistente disponible (BigQuery)")
        else:
            print("⚠️ Memoria persistente no disponible")
        
        if warnings:
            print(f"⚠️ {len(warnings)} advertencias encontradas")
        
        print("=" * 60)
        
        return ValidationResult(
            is_valid=is_valid,
            missing_required=missing_required,
            missing_optional=missing_optional,
            invalid_values=invalid_values,
            warnings=warnings,
            bigquery_available=bigquery_available
        )
    
    @classmethod
    def _validate_bigquery_config(cls, warnings: List[str]) -> bool:
        """Valida la configuración de BigQuery."""
        bigquery_vars_present = []
        bigquery_vars_missing = []
        
        for var in cls.BIGQUERY_VARS:
            value = os.getenv(var)
            if value:
                bigquery_vars_present.append(var)
                if var == "GOOGLE_APPLICATION_CREDENTIALS_JSON":
                    # Validar que sea JSON válido
                    try:
                        json.loads(value)
                        print(f"✅ {var}: Credenciales JSON válidas")
                    except json.JSONDecodeError:
                        warnings.append(f"{var} contiene JSON inválido")
                        print(f"⚠️ {var}: JSON INVÁLIDO")
                        return False
                else:
                    print(f"✅ {var}: {value}")
            else:
                bigquery_vars_missing.append(var)
                print(f"⚠️ {var}: NO CONFIGURADA")
        
        # BigQuery está disponible si al menos las variables críticas están presentes
        critical_vars = ["GOOGLE_APPLICATION_CREDENTIALS_JSON", "BIGQUERY_PROJECT_ID", "BIGQUERY_DATASET"]
        bigquery_available = all(os.getenv(var) for var in critical_vars)
        
        if not bigquery_available:
            print("⚠️ Memoria persistente deshabilitada - faltan variables críticas de BigQuery")
        
        return bigquery_available
    
    @classmethod
    def _validate_variable_format(cls, var_name: str, value: str) -> Optional[str]:
        """Valida el formato de una variable específica."""
        if var_name == "WEBHOOK_PORT":
            try:
                port = int(value)
                if not (1 <= port <= 65535):
                    return "Puerto debe estar entre 1 y 65535"
            except ValueError:
                return "Puerto debe ser un número entero"
        
        elif var_name == "LOG_LEVEL":
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if value.upper() not in valid_levels:
                return f"Nivel de log debe ser uno de: {', '.join(valid_levels)}"
        
        elif var_name == "HEALTH_CHECK_INTERVAL":
            try:
                interval = int(value)
                if interval < 1:
                    return "Intervalo de health check debe ser mayor a 0"
            except ValueError:
                return "Intervalo debe ser un número entero"
        
        elif var_name == "MAX_RETRIES":
            try:
                retries = int(value)
                if retries < 0:
                    return "Número de reintentos no puede ser negativo"
            except ValueError:
                return "Número de reintentos debe ser un entero"
        
        elif var_name == "BIGQUERY_MAX_BYTES_BILLED":
            try:
                bytes_billed = int(value)
                if bytes_billed < 0:
                    return "Bytes máximos facturados no puede ser negativo"
            except ValueError:
                return "Bytes máximos debe ser un número entero"
        
        return None
    
    @classmethod
    def _mask_sensitive_value(cls, var_name: str, value: str) -> str:
        """Enmascara valores sensibles para mostrar en logs."""
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"
    
    @classmethod
    def _get_default_value(cls, var_name: str) -> str:
        """Obtiene el valor por defecto para una variable."""
        defaults = {
            "WEBHOOK_PORT": "8080",
            "LOG_LEVEL": "INFO",
            "HEALTH_CHECK_INTERVAL": "30",
            "MAX_RETRIES": "3"
        }
        return defaults.get(var_name, "N/A")
    
    @classmethod
    def _validate_network_config(cls, warnings: List[str]) -> None:
        """Valida la configuración de red."""
        port = os.getenv("WEBHOOK_PORT", "8080")
        try:
            port_num = int(port)
            if port_num < 1024 and os.name != 'nt':  # En sistemas Unix, puertos < 1024 requieren privilegios
                warnings.append(f"Puerto {port_num} puede requerir privilegios de administrador en sistemas Unix")
        except ValueError:
            pass  # Ya se validó en _validate_variable_format
    
    @classmethod
    def _validate_security_config(cls, warnings: List[str]) -> None:
        """Valida aspectos de seguridad de la configuración."""
        # Verificar que las claves no estén en valores por defecto obvios
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if api_key and (api_key.startswith("sk-test") or len(api_key) < 20):
            warnings.append("La clave de Anthropic parece ser de prueba o muy corta")
        
        # Verificar configuración de Slack
        slack_token = os.getenv("SLACK_BOT_TOKEN", "")
        if slack_token and not slack_token.startswith("xoxb-"):
            warnings.append("El token de Slack Bot no tiene el formato esperado (debe empezar con 'xoxb-')")
        
        app_token = os.getenv("SLACK_APP_TOKEN", "")
        if app_token and not app_token.startswith("xapp-"):
            warnings.append("El token de Slack App no tiene el formato esperado (debe empezar con 'xapp-')")