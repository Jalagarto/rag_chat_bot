"""
Aplicación principal del chatbot RAG con memoria dinámica.
"""
import os
import time
import signal
import sys
from typing import List, Tuple
from config.settings import settings
from core.document_processor import DocumentProcessor
from core.memory_manager import MemoryManager
from core.query_engine import QueryEngine
from utils.logging_config import logger
from app_rag_chat_bot.core.interfaz import create_interface


class ChatbotApp:
    """
    Aplicación principal del chatbot.
    """
    def __init__(self):
        """Inicializa la aplicación del chatbot."""
        logger.info("Inicializando aplicación del chatbot")
        # Crear directorios necesarios
        os.makedirs("./data", exist_ok=True)
        
        # Inicializar componentes
        self.document_processor = DocumentProcessor()
        self.memory_manager = MemoryManager()
        self.query_engine = QueryEngine(self.document_processor, self.memory_manager)
        
        # Crear interfaz de Gradio
        self.interface = create_interface(self)

    def _process_files(self, files: List) -> str:
        """
        Procesa los archivos subidos.
        
        Args:
            files (List): Lista de archivos subidos.
        
        Returns:
            str: Mensaje de estado.
        """
        if not files:
            return "No se han subido archivos."
        
        start_time = time.time()
        
        try:
            # Convertir archivos a formato binario
            file_contents = []
            for file in files:
                with open(file.name, "rb") as f:
                    file_contents.append(f.read())
            
            # Procesar archivos
            result = self.document_processor.process_pdfs(file_contents)
            
            elapsed_time = time.time() - start_time
            
            if result["status"] == "success":
                return f"{result['message']} (Procesado en {elapsed_time:.2f} segundos)"
            else:
                return f"Error: {result['message']} (Tiempo: {elapsed_time:.2f} segundos)"
        
        except Exception as e:
            logger.error(f"Error al procesar archivos: {str(e)}")
            return f"Error al procesar los archivos: {str(e)}"

    def _chat_and_log(self, query: str, history: List[List[str]]) -> Tuple[str, List[List[str]]]:
        """
        Procesa una consulta del usuario y actualiza el historial.
        
        Args:
            query (str): Consulta del usuario.
            history (List[List[str]]): Historial de chat de Gradio.
        
        Returns:
            Tuple[str, List[List[str]]]: Input vacío y historial actualizado.
        """
        if not query:
            return "", history
        
        try:
            # Procesar la consulta
            response = self.query_engine.process_query(query)
            
            # Actualizar historial de Gradio
            history.append([query, response])
            
            return "", history
        
        except Exception as e:
            logger.error(f"Error en el chat: {str(e)}")
            error_msg = f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"
            history.append([query, error_msg])
            return "", history

    def _clear_chat(self) -> List[List[str]]:
        """
        Limpia el historial de chat y la memoria.
        
        Returns:
            List[List[str]]: Historial de chat vacío.
        """
        self.memory_manager.clear_memory()
        return []

    def _regenerate_response(self, history: List[List[str]]) -> List[List[str]]:
        """
        Regenera la última respuesta.
        
        Args:
            history (List[List[str]]): Historial de chat de Gradio.
        
        Returns:
            List[List[str]]: Historial actualizado.
        """
        if not history:
            return []
        
        # Obtener la última consulta
        last_query = history[-1][0]
        
        # Eliminar la última respuesta del historial
        history.pop()
        
        # Actualizar la memoria (eliminar la última interacción)
        if len(self.memory_manager.conversation_history) >= 2:
            self.memory_manager.conversation_history = self.memory_manager.conversation_history[:-2]
        
        # Regenerar respuesta
        response = self.query_engine.process_query(last_query)
        
        # Actualizar historial
        history.append([last_query, response])
        
        return history

    def run(self):
        """Ejecuta la aplicación."""
        # Configurar manejo de señales para salida limpia
        def signal_handler(sig, frame):
            logger.info("Cerrando aplicación...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Lanzar la interfaz
        self.interface.launch(
            server_name=settings.host,
            server_port=settings.port,
            share=False,
            debug=False,
        )

if __name__=="__main__":
    try:
        # Verificar configuración
        if not settings.openai_api_key:
            logger.error("API key de OpenAI no configurada. Configúrala en .env o como variable de entorno.")
            print("Error: API key de OpenAI no configurada. Configúrala en .env o como variable de entorno.")
            sys.exit(1)        
        # Crear e iniciar la aplicación
        app = ChatbotApp()
        app.run()

    except Exception as e:
        logger.critical(f"Error fatal al iniciar la aplicación: {str(e)}")
        print(f"Error fatal: {str(e)}")
        sys.exit(1)        