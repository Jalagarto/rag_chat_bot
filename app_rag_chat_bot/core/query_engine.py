"""
Motor de consultas del chatbot.
"""
from langchain_openai import ChatOpenAI
from config.settings import settings
from core.document_processor import DocumentProcessor
from core.memory_manager import MemoryManager
from core.code_executor import CodeExecutor
from utils.logging_config import setup_logger
logger = setup_logger("query_engine", "query_engine.log")


class QueryEngine:
    """
    Motor para procesar consultas y generar respuestas.
    """

    def __init__(self, document_processor: DocumentProcessor, memory_manager: MemoryManager):
        """
        Inicializa el motor de consultas.    "
        
        Args:
            document_processor (DocumentProcessor): Procesador de documentos para RAG.
            memory_manager (MemoryManager): Gestor de memoria de conversación.
        """
        self.document_processor = document_processor
        self.memory_manager = memory_manager
        self.code_executor = CodeExecutor()
        
        # Inicializar LLM
        self.llm = ChatOpenAI(
            model_name=settings.llm_model_name,
            openai_api_key=settings.openai_api_key
        )

    def process_query(self, query: str) -> str:
        """
        Procesa una consulta y genera una respuesta.
        
        Args:
            query (str): Consulta del usuario.
        
        Returns:
            str: Respuesta generada.
        """
        logger.info(f"Procesando consulta: {query}")
        
        # Añadir la consulta a la memoria
        self.memory_manager.add_message("user", query)
        
        # Determinar si es necesario ejecutar código
        if self.code_executor.detect_code_execution_needed(query):
            logger.info("Se detectó necesidad de ejecución de código")
            response = self._handle_code_execution(query)
        else:
            # Enfoque RAG estándar
            response = self._handle_rag_query(query)
        
        # Añadir la respuesta a la memoria
        self.memory_manager.add_message("assistant", response)
        
        return response

    def _handle_code_execution(self, query: str) -> str:
        """
        Maneja una consulta que requiere ejecución de código.
        
        Args:
            query (str): Consulta del usuario.
        
        Returns:
            str: Respuesta que incluye los resultados del código.
        """
        try:
            # Generar código Python
            python_code = self.code_executor.generate_code(self.llm, query)
            
            # Ejecutar el código
            execution_result = self.code_executor.execute_code(python_code)
            
            # Generar explicación del resultado
            response = self.code_executor.explain_code_result(
                self.llm, query, python_code, execution_result
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error en ejecución de código: {str(e)}")
            
            # Respuesta de error
            return f"""
            Intenté realizar cálculos para responder tu pregunta, pero encontré un error técnico.
            Si tu pregunta requiere cálculos precisos, por favor reformúlala o proporciona más detalles.
            
            Error: {str(e)}
            """

    def _handle_rag_query(self, query: str) -> str:
        """
        Maneja una consulta usando RAG.
        
        Args:
            query (str): Consulta del usuario.
        
        Returns:
            str: Respuesta generada con RAG.
        """
        try:
            # Obtener documentos relevantes
            relevant_docs = self.document_processor.get_relevant_documents(query)
            
            # Preparar el contexto de la conversación
            conversation_context = self.memory_manager.get_formatted_history(5)
            
            # Crear el prompt RAG
            if relevant_docs:
                formatted_docs = self.document_processor.format_documents(relevant_docs)
                
                rag_prompt = f"""
                ### INSTRUCCIONES
                Eres un asistente de IA que proporciona respuestas precisas y útiles basadas en el contexto de la conversación
                y la información disponible en la base de conocimiento. Cuando la información no esté disponible en los documentos, 
                basa tu respuesta en tu conocimiento general, pero indica claramente cuando lo haces.
                
                ### CONTEXTO DE LA CONVERSACIÓN
                {conversation_context}
                
                ### INFORMACIÓN DE LA BASE DE CONOCIMIENTO
                {formatted_docs}
                
                ### CONSULTA DEL USUARIO
                {query}
                
                ### RESPUESTA
                """
            else:
                # Sin documentos relevantes, usar solo el contexto
                rag_prompt = f"""
                ### INSTRUCCIONES
                Eres un asistente de IA que proporciona respuestas precisas y útiles basadas en el contexto de la conversación
                y tu conocimiento general. Sé honesto cuando no sepas algo.
                
                ### CONTEXTO DE LA CONVERSACIÓN
                {conversation_context}
                
                ### CONSULTA DEL USUARIO
                {query}
                
                ### RESPUESTA
                """
            
            # Generar respuesta
            response = self.llm.invoke(rag_prompt).content
            return response
        
        except Exception as e:
            logger.error(f"Error en procesamiento RAG: {str(e)}")
            
            # Respuesta de error
            return f"""
            Lo siento, encontré un error al procesar tu consulta. Por favor, inténtalo de nuevo o reformula tu pregunta.
            
            Si el problema persiste, considera reiniciar la conversación.
            """        