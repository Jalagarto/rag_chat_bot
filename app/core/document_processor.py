"""
Procesamiento de documentos para RAG.
"""
import os
import tempfile
from typing import List, Dict, Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from config.settings import settings
from utils.logging_config import setup_logger

logger = setup_logger("document_processor", "document_processor.log")

class DocumentProcessor:
    """
    Clase para el procesamiento y gestión de documentos.
    """
    def __init__(self):
        """Inicializa el procesador de documentos."""
        self.vector_db = None
        self.embedding_model = OpenAIEmbeddings(
            model=settings.embedding_model_name,
            openai_api_key=settings.openai_api_key
        )
        
        # Crear directorio para base de datos vectorial si no existe
        if settings.enable_vector_db_persistence:
            os.makedirs(settings.vector_db_path, exist_ok=True)
            
            # Intentar cargar la base de datos si existe
            try:
                self.vector_db = Chroma(
                    persist_directory=settings.vector_db_path,
                    embedding_function=self.embedding_model
                )
                logger.info(f"Base de datos vectorial cargada desde {settings.vector_db_path}")
            except Exception as e:
                logger.warning(f"No se pudo cargar la base de datos vectorial: {str(e)}")
    
    def process_pdfs(self, pdf_files: List[bytes]) -> Dict[str, Any]:
        """
        Procesa archivos PDF y los carga en la base de datos vectorial.
        
        Args:
            pdf_files (List[bytes]): Lista de archivos PDF en formato binario.
        
        Returns:
            Dict[str, Any]: Resultados del procesamiento.
        """
        documents = []
        temp_files = []
        stats = {"success": 0, "failed": 0, "chunks": 0}
        
        try:
            # Procesar cada archivo PDF
            for i, pdf_file in enumerate(pdf_files):
                try:
                    # Crear archivo temporal
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    temp_file.write(pdf_file)
                    temp_file.close()
                    temp_files.append(temp_file.name)
                    
                    # Cargar PDF
                    loader = PyPDFLoader(temp_file.name)
                    pdf_documents = loader.load()
                    
                    if pdf_documents:
                        documents.extend(pdf_documents)
                        stats["success"] += 1
                        logger.info(f"PDF {i+1} procesado correctamente: {len(pdf_documents)} páginas")
                    else:
                        stats["failed"] += 1
                        logger.warning(f"PDF {i+1} no contenía texto extraíble")
                
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"Error al procesar PDF {i+1}: {str(e)}")
            
            # Dividir documentos en chunks
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap
                )
                splits = text_splitter.split_documents(documents)
                stats["chunks"] = len(splits)
                
                # Inicializar o actualizar vectorial BD
                if not self.vector_db:
                    # Crear nueva db
                    if settings.enable_vector_db_persistence:
                        self.vector_db = Chroma.from_documents(
                            documents=splits,
                            embedding=self.embedding_model,
                            persist_directory=settings.vector_db_path
                        )
                    else:
                        self.vector_db = Chroma.from_documents(
                            documents=splits,
                            embedding=self.embedding_model
                        )
                else:
                    # Actualizar BD existente
                    self.vector_db.add_documents(documents=splits)
                    if settings.enable_vector_db_persistence:
                        pass
                logger.info(f"Base de datos vectorial actualizada con {len(splits)} fragmentos")
            
            return {
                "status": "success",
                "message": f"Se procesaron {stats['success']} archivos correctamente y {stats['failed']} fallaron. "
                          f"Se añadieron {stats['chunks']} fragmentos a la base de conocimiento.",
                "stats": stats
            }
        
        except Exception as e:
            logger.error(f"Error en el procesamiento de documentos: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en el procesamiento: {str(e)}",
                "stats": stats
            }
        finally:
            # Limpiar archivos temporales
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal {temp_file}: {str(e)}")
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Recupera documentos relevantes para una consulta.
        
        Args:
            query (str): Consulta del usuario.
        
        Returns:
            List[Document]: Lista de documentos relevantes.
        """
        if not self.vector_db:
            logger.warning("Se solicitaron documentos relevantes, pero no hay base de datos vectorial")
            return []
        
        try:
            return self.vector_db.similarity_search(
                query, 
                k=settings.retrieval_k
            )
        except Exception as e:
            logger.error(f"Error al recuperar documentos relevantes: {str(e)}")
            return []
    
    def format_documents(self, docs: List[Document]) -> str:
        """
        Formatea los documentos para incluirlos en el prompt.
        
        Args:
            docs (List[Document]): Lista de documentos.
        
        Returns:
            str: Texto formateado.
        """
        if not docs:
            return "No se encontró información relevante en la base de conocimiento."
        
        formatted_docs = []
        for i, doc in enumerate(docs):
            source = getattr(doc.metadata, "source", "Desconocido") if hasattr(doc, "metadata") else "Desconocido"
            page = getattr(doc.metadata, "page", "N/A") if hasattr(doc, "metadata") else "N/A"
            
            formatted_docs.append(
                f"--- Documento {i+1} (Fuente: {source}, Página: {page}) ---\n"
                f"{doc.page_content}\n"
            )
        
        return "\n".join(formatted_docs)