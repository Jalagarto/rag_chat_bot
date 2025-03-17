"""
Utilidades de seguridad para el chatbot.
"""
import ast
import re
from typing import Tuple

# Lista de módulos y funciones potencialmente peligrosos
DANGEROUS_MODULES = [
    "os", "subprocess", "sys", "shutil", "socket", "requests", "urllib",
    "ftplib", "paramiko", "telnetlib", "smtplib", "http.server", "socketserver"
]

DANGEROUS_FUNCTIONS = [
    "eval", "exec", "compile", "globals", "locals", "getattr", "setattr", "delattr",
    "__import__", "open", "file", "input", "raw_input"
]

DANGEROUS_PATTERNS = [
    r"__[a-zA-Z]+__",  # Métodos dunder
    r"sys\s*\.\s*exit",
    r"os\s*\.\s*system",
    r"subprocess\s*\.\s*(?:call|run|Popen)",
    r"import\s+(?:" + "|".join(DANGEROUS_MODULES) + ")"
]

def is_safe_code(code: str) -> Tuple[bool, str]:
    """
    Verifica si el código Python es seguro para ejecutar.
    
    Args:
        code (str): Código Python a analizar.
    
    Returns:
        Tuple[bool, str]: (es_seguro, mensaje_error)
    """
    # Verificar patrones peligrosos
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code):
            return False, f"Patrón de código potencialmente peligroso detectado: {pattern}"
    
    # Analizar el AST
    try:
        parsed = ast.parse(code)
    except SyntaxError as e:
        return False, f"Error de sintaxis: {str(e)}"
    
    # Examinar el AST en busca de operaciones peligrosas
    for node in ast.walk(parsed):
        # Importaciones peligrosas
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name in DANGEROUS_MODULES:
                    return False, f"Importación no permitida: {name.name}"
        
        elif isinstance(node, ast.ImportFrom):
            if node.module in DANGEROUS_MODULES:
                return False, f"Importación desde módulo no permitido: {node.module}"
        
        # Llamadas a funciones peligrosas
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_FUNCTIONS:
                return False, f"Función potencialmente peligrosa: {node.func.id}"
            
            # Verificar atributos (como os.system)
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id in DANGEROUS_MODULES:
                        return False, f"Módulo potencialmente peligroso: {node.func.value.id}.{node.func.attr}"
    
    return True, ""

def sanitize_code_output(output: str) -> str:
    """
    Sanitiza la salida del código ejecutado para evitar posibles vulnerabilidades.
    
    Args:
        output (str): Salida del código ejecutado.
    
    Returns:
        str: Salida sanitizada.
    """
    # Limitar longitud máxima
    if len(output) > 10000:
        output = output[:10000] + "... (salida truncada)"
    
    # Eliminar caracteres de control excepto saltos de línea y tabulaciones
    output = re.sub(r'[\x00-\x09\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', output)
    
    return output