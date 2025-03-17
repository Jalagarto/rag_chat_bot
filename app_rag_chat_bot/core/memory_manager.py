"""
Gestión de la memoria de conversación.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI

from config.settings import settings
from utils.logging_config import setup_logger

logger = setup_logger("memory_manager", "memory_manager.log")

class MemoryManager:
    """
    Gestiona la memoria de conversación con resumen dinámico.
    """
    def __init__(self):
        """Inicializa el gestor de memoria."""
        self.conversation_history = []
        self.summarizer_llm = ChatOpenAI(
            model_name=settings.summarizer_model_name,
            openai_api_key=settings.openai_api_key
        )
    
    def add_message(self, role: str, content: str) -> None:
        """
        Añade un mensaje a la memoria de conversación.
        
        Args:
            role (str): Rol del mensaje (user, assistant, system).
            content (str): Contenido del mensaje.
        """
        timestamp = datetime.now().isoformat()
        
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
        
        # Verificar si es necesario resumir
        self._check_and_summarize()
    
    def get_recent_history(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Recupera los n mensajes más recientes.
        
        Args:
            n (int, optional): Número de mensajes a recuperar. Por defecto 5.
        
        Returns:
            List[Dict[str, Any]]: Lista de mensajes recientes.
        """
        return self.conversation_history[-n:] if len(self.conversation_history) > 0 else []
    
    def get_formatted_history(self, n: Optional[int] = None) -> str:
        """
        Obtiene el historial formateado como texto.
        
        Args:
            n (int, optional): Número de mensajes a incluir (todos si es None).
        
        Returns:
            str: Historial formateado.
        """
        history = self.conversation_history if n is None else self.conversation_history[-n:]
        
        formatted = []
        for msg in history:
            formatted.append(f"{msg['role'].upper()}: {msg['content']}")
        
        return "\n\n".join(formatted)
    
    def clear_memory(self) -> None:
        """Limpia toda la memoria de conversación."""
        self.conversation_history = []
        logger.info("Memoria de conversación limpiada")
    
    def _check_and_summarize(self) -> None:
        """
        Verifica si es necesario resumir la memoria y lo hace si procede.
        """
        if len(self.conversation_history) <= 2:
            return
        
        # Estimar número de tokens (aproximadamente 4 caracteres por token)
        total_chars = sum(len(entry["content"]) for entry in self.conversation_history)
        estimated_tokens = total_chars // settings.char_to_token_ratio
        
        if estimated_tokens > settings.max_memory_tokens:
            logger.info(f"Resumiendo memoria (aprox. {estimated_tokens} tokens)")
            self._summarize_memory()
    
    def _summarize_memory(self) -> None:
        """
        Resume la memoria de conversación manteniendo el contexto importante.
        """
        try:
            # Mantener los últimos 2 intercambios intactos
            recent_history = self.conversation_history[-4:] if len(self.conversation_history) >= 4 else []
            history_to_summarize = self.conversation_history[:-4] if len(self.conversation_history) >= 4 else self.conversation_history
            
            if not history_to_summarize:
                return
            
            # Preparar el texto para resumir
            history_text = ""
            for entry in history_to_summarize:
                history_text += f"{entry['role'].upper()}: {entry['content']}\n\n"
            
            # Resumir la conversación
            summary_prompt = f"""
            Resume la siguiente conversación de manera concisa pero manteniendo 
            los puntos clave, el contexto importante y cualquier información factual relevante.
            El resumen debe ser completo pero compacto.
            
            CONVERSACIÓN:
            {history_text}
            
            RESUMEN CONCISO:
            """
            
            summary_response = self.summarizer_llm.invoke(summary_prompt)
            summary = summary_response.content
            
            # Crear nueva historia con el resumen
            timestamp = datetime.now().isoformat()
            self.conversation_history = [
                {
                    "role": "system", 
                    "content": f"Resumen de la conversación previa: {summary}",
                    "timestamp": timestamp
                }
            ] + recent_history
            
            logger.info(f"Memoria resumida exitosamente")
        
        except Exception as e:
            logger.error(f"Error al resumir la memoria: {str(e)}")