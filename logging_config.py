import logging

logging.basicConfig(
    level=logging.INFO,  # Cambia a DEBUG para más detalle
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_logger(name: str):
    return logging.getLogger(name)