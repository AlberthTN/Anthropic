import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecurityValidator:
    """
    Validador de seguridad que consulta un servicio externo para verificar
    si las consultas son seguras antes de procesarlas con Claude.
    """
    
    def __init__(self):
        """Inicializa el validador de seguridad."""
        self.security_endpoint = "https://seguridad.tiendasnetows.com/analyze"
        self.auth_token = "1e000080d536e36131e1743e6da9e4fd"
        self.agent_name = "A-Anthropic"
        self.model = "openai:gpt-4o-mini"
        self.timeout = 10  # Timeout de 10 segundos
        
    def validate_query(self, text: str) -> Dict[str, Any]:
        """
        Valida si una consulta es segura usando el servicio externo.
        
        Args:
            text (str): El texto de la consulta a validar
            
        Returns:
            Dict[str, Any]: Resultado de la validación con estructura:
                {
                    "is_safe": bool,
                    "message": str,
                    "details": dict (opcional)
                }
        """
        try:
            logger.info(f"🔒 Validando seguridad para consulta: {text[:100]}...")
            
            # Preparar headers
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            
            # Preparar payload
            payload = {
                "text": text,
                "model": self.model,
                "token": self.auth_token,
                "agent": self.agent_name
            }
            
            # Hacer la petición HTTP
            response = requests.post(
                self.security_endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Verificar status code
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Validación de seguridad exitosa: {result}")
                
                # Interpretar la respuesta del servicio
                # Asumiendo que el servicio devuelve un campo que indica si es seguro
                is_safe = self._interpret_security_response(result)
                
                return {
                    "is_safe": is_safe,
                    "message": "Consulta validada exitosamente",
                    "details": result
                }
                
            else:
                logger.warning(f"⚠️ Error en validación de seguridad: {response.status_code} - {response.text}")
                # En caso de error del servicio, permitir por defecto (fail-open)
                return {
                    "is_safe": True,
                    "message": f"Servicio de seguridad no disponible (HTTP {response.status_code}), permitiendo consulta",
                    "details": {"error": response.text}
                }
                
        except requests.exceptions.Timeout:
            logger.warning("⚠️ Timeout en validación de seguridad, permitiendo consulta")
            return {
                "is_safe": True,
                "message": "Timeout en servicio de seguridad, permitiendo consulta",
                "details": {"error": "timeout"}
            }
            
        except requests.exceptions.ConnectionError:
            logger.warning("⚠️ Error de conexión en validación de seguridad, permitiendo consulta")
            return {
                "is_safe": True,
                "message": "Error de conexión con servicio de seguridad, permitiendo consulta",
                "details": {"error": "connection_error"}
            }
            
        except Exception as e:
            logger.error(f"❌ Error inesperado en validación de seguridad: {str(e)}")
            # En caso de error inesperado, permitir por defecto (fail-open)
            return {
                "is_safe": True,
                "message": f"Error inesperado en validación de seguridad: {str(e)}, permitiendo consulta",
                "details": {"error": str(e)}
            }
    
    def _interpret_security_response(self, response: Dict[str, Any]) -> bool:
        """
        Interpreta la respuesta del servicio de seguridad para determinar si es segura.
        
        Args:
            response (Dict[str, Any]): Respuesta del servicio de seguridad
            
        Returns:
            bool: True si es segura, False si no es segura
        """
        # Buscar diferentes campos que podrían indicar seguridad
        # Adaptable según la estructura real de respuesta del servicio
        
        if "is_safe" in response:
            return bool(response["is_safe"])
        
        if "safe" in response:
            return bool(response["safe"])
            
        if "security_score" in response:
            # Asumiendo que un score > 0.5 es seguro
            return float(response["security_score"]) > 0.5
            
        if "risk_level" in response:
            # Asumiendo que "low" o "none" son seguros
            risk_level = str(response["risk_level"]).lower()
            return risk_level in ["low", "none", "safe"]
            
        if "status" in response:
            status = str(response["status"]).lower()
            return status in ["safe", "ok", "approved", "clean"]
        
        # Si no encontramos un campo claro, revisar si hay indicadores de peligro
        dangerous_indicators = ["unsafe", "dangerous", "blocked", "rejected", "malicious"]
        response_str = json.dumps(response).lower()
        
        for indicator in dangerous_indicators:
            if indicator in response_str:
                logger.warning(f"🚨 Indicador de peligro encontrado: {indicator}")
                return False
        
        # Por defecto, si no hay indicadores claros, permitir (fail-open)
        logger.info("🤔 No se encontraron indicadores claros de seguridad, permitiendo por defecto")
        return True

# Instancia global del validador
security_validator = SecurityValidator()