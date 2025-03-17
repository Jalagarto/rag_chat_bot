"""
Configuración del sistema de logging.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import settings

# Crear directorio de logs si no existe
log_dir = Path("./logs")
log_dir.mkdir(parents=True, exist_ok=True)

def setup_logger(name, log_file=None):
    """
    Configura y devuelve un logger con handlers para consola y archivo.
    
    Args:
        name (str): Nombre del logger.
        log_file (str, optional): Ruta al archivo de log.
    
    Returns:
        logging.Logger: Logger configurado.
    """
    logger = logging.getLogger(name)
    
    # Configurar nivel de log según la configuración
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Evitar duplicación de logs
    if logger.handlers:
        return logger
    
    # Formato del log
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Handler para archivo (si se especifica)
    if log_file:
        file_handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger

# Logger principal de la aplicación
logger = setup_logger("rag_chatbot", "app.log")