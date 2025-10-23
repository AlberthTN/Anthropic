"""
Utilidad para dividir mensajes largos en partes más pequeñas compatibles con Slack.
Maneja tanto texto plano como código, manteniendo la sintaxis y formato.
"""

import re
import logging
from typing import List, Tuple
from textwrap import dedent

logger = logging.getLogger(__name__)

class MessageSplitter:
    """
    Clase para dividir mensajes largos en partes más pequeñas para Slack.
    
    Límites de Slack:
    - Mensajes de texto: 4000 caracteres
    - Mensajes con formato: 3000 caracteres (para dar margen)
    - Bloques de código: 2900 caracteres (para dar margen con ```python```)
    """
    
    def __init__(self):
        """Inicializa el divisor de mensajes."""
        self.max_text_length = 3000  # Límite seguro para texto normal
        self.max_code_length = 2900  # Límite seguro para bloques de código
        self.continuation_indicator = "... (continúa)"
        self.part_indicator = "(Parte {}/{})"
        
    def split_message(self, message: str, is_code: bool = False) -> List[str]:
        """
        Divide un mensaje largo en partes más pequeñas.
        
        Args:
            message (str): El mensaje a dividir
            is_code (bool): Si el mensaje contiene principalmente código
            
        Returns:
            List[str]: Lista de partes del mensaje
        """
        try:
            logger.info(f"📝 Dividiendo mensaje de {len(message)} caracteres (código: {is_code})")
            
            if is_code:
                return self._split_code_message(message)
            else:
                return self._split_text_message(message)
                
        except Exception as e:
            logger.error(f"❌ Error dividiendo mensaje: {str(e)}")
            # En caso de error, devolver el mensaje original
            return [message]
    
    def _split_text_message(self, message: str) -> List[str]:
        """Divide un mensaje de texto normal."""
        if len(message) <= self.max_text_length:
            return [message]
        
        parts = []
        current_part = ""
        
        # Dividir por párrafos primero
        paragraphs = message.split('\n\n')
        
        for paragraph in paragraphs:
            # Si el párrafo completo cabe en la parte actual
            if len(current_part + paragraph + '\n\n') <= self.max_text_length:
                current_part += paragraph + '\n\n'
            else:
                # Si hay contenido en la parte actual, guardarlo
                if current_part.strip():
                    parts.append(current_part.strip())
                    current_part = ""
                
                # Si el párrafo es muy largo, dividirlo por oraciones
                if len(paragraph) > self.max_text_length:
                    sentence_parts = self._split_by_sentences(paragraph)
                    for sentence_part in sentence_parts:
                        if len(current_part + sentence_part) <= self.max_text_length:
                            current_part += sentence_part
                        else:
                            if current_part.strip():
                                parts.append(current_part.strip())
                            current_part = sentence_part
                else:
                    current_part = paragraph + '\n\n'
        
        # Agregar la última parte si tiene contenido
        if current_part.strip():
            parts.append(current_part.strip())
        
        return self._add_part_indicators(parts)
    
    def _split_code_message(self, message: str) -> List[str]:
        """Divide un mensaje que contiene código."""
        if len(message) <= self.max_code_length:
            return [message]
        
        parts = []
        
        # Buscar bloques de código
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', message, re.DOTALL)
        
        if code_blocks:
            # Si hay bloques de código, procesarlos especialmente
            return self._split_with_code_blocks(message)
        else:
            # Si no hay bloques de código, tratar como texto normal
            return self._split_text_message(message)
    
    def _split_with_code_blocks(self, message: str) -> List[str]:
        """Divide un mensaje que contiene bloques de código."""
        parts = []
        current_part = ""
        
        # Dividir el mensaje en partes: texto y bloques de código
        pattern = r'(```(?:\w+)?\n.*?\n```)'
        segments = re.split(pattern, message, flags=re.DOTALL)
        
        for segment in segments:
            if not segment.strip():
                continue
                
            # Verificar si es un bloque de código
            if segment.startswith('```'):
                # Es un bloque de código
                if len(current_part + segment) <= self.max_code_length:
                    current_part += segment
                else:
                    # Guardar la parte actual si tiene contenido
                    if current_part.strip():
                        parts.append(current_part.strip())
                    
                    # Si el bloque de código es muy grande, dividirlo
                    if len(segment) > self.max_code_length:
                        code_parts = self._split_large_code_block(segment)
                        parts.extend(code_parts[:-1])  # Agregar todas menos la última
                        current_part = code_parts[-1]  # La última parte se convierte en la actual
                    else:
                        current_part = segment
            else:
                # Es texto normal
                if len(current_part + segment) <= self.max_code_length:
                    current_part += segment
                else:
                    # Guardar la parte actual si tiene contenido
                    if current_part.strip():
                        parts.append(current_part.strip())
                    current_part = segment
        
        # Agregar la última parte si tiene contenido
        if current_part.strip():
            parts.append(current_part.strip())
        
        return self._add_part_indicators(parts)
    
    def _split_large_code_block(self, code_block: str) -> List[str]:
        """Divide un bloque de código muy grande."""
        # Extraer el lenguaje y el código
        match = re.match(r'```(\w+)?\n(.*)\n```', code_block, re.DOTALL)
        if not match:
            return [code_block]
        
        language = match.group(1) or ""
        code = match.group(2)
        
        # Dividir el código por líneas
        lines = code.split('\n')
        parts = []
        current_lines = []
        current_length = len(f"```{language}\n\n```")  # Longitud base
        
        for line in lines:
            line_length = len(line) + 1  # +1 para el \n
            
            if current_length + line_length <= self.max_code_length - 50:  # -50 para margen
                current_lines.append(line)
                current_length += line_length
            else:
                # Crear una parte con las líneas actuales
                if current_lines:
                    code_part = f"```{language}\n" + '\n'.join(current_lines) + "\n```"
                    parts.append(code_part)
                
                # Comenzar una nueva parte
                current_lines = [line]
                current_length = len(f"```{language}\n{line}\n```")
        
        # Agregar la última parte si tiene contenido
        if current_lines:
            code_part = f"```{language}\n" + '\n'.join(current_lines) + "\n```"
            parts.append(code_part)
        
        return parts
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Divide un texto por oraciones."""
        # Dividir por puntos, pero mantener los puntos
        sentences = re.split(r'(\. )', text)
        parts = []
        current_part = ""
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            
            # Si es un separador (punto), agregarlo a la oración anterior
            if sentence == '. ' and i > 0:
                current_part += sentence
                i += 1
                continue
            
            if len(current_part + sentence) <= self.max_text_length:
                current_part += sentence
            else:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = sentence
            
            i += 1
        
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
    def _add_part_indicators(self, parts: List[str]) -> List[str]:
        """Agrega indicadores de parte a los mensajes divididos."""
        if len(parts) <= 1:
            return parts
        
        result = []
        for i, part in enumerate(parts, 1):
            indicator = f"\n\n{self.part_indicator.format(i, len(parts))}"
            
            # Si no es la última parte, agregar indicador de continuación
            if i < len(parts):
                indicator += f" {self.continuation_indicator}"
            
            result.append(part + indicator)
        
        return result
    
    def needs_splitting(self, message: str, is_code: bool = False) -> bool:
        """
        Verifica si un mensaje necesita ser dividido.
        
        Args:
            message (str): El mensaje a verificar
            is_code (bool): Si el mensaje contiene principalmente código
            
        Returns:
            bool: True si necesita división, False en caso contrario
        """
        limit = self.max_code_length if is_code else self.max_text_length
        return len(message) > limit


# Instancia global del divisor de mensajes
message_splitter = MessageSplitter()