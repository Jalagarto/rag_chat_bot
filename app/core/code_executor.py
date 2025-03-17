"""
Ejecución segura de código Python.
"""
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any

from utils.security import is_safe_code, sanitize_code_output
from utils.logging_config import setup_logger

logger = setup_logger("code_executor", "code_executor.log")

class CodeExecutor:
    """
    Ejecuta código Python de manera segura.
    """
    def __init__(self):
        """Inicializa el ejecutor de código."""
        # Módulos permitidos
        self.allowed_imports = {
            "math": "import math",
            "random": "import random",
            "datetime": "from datetime import datetime, date, timedelta",
            "statistics": "import statistics",
            "pandas": "import pandas as pd",
            "numpy": "import numpy as np",
            "re": "import re",
            "collections": "import collections"
        }
    
    def detect_code_execution_needed(self, query: str) -> bool:
        """
        Detecta si la consulta requiere ejecución de código para precisión.
        
        Args:
            query (str): Consulta del usuario.
        
        Returns:
            bool: True si se requiere ejecución de código.
        """
        # Palabras clave que indican necesidad de cálculos precisos
        code_keywords = [
            "calcula", "calcular", "calcule", "resultado exacto", "precisión numérica",
            "computa", "computar", "cómputo", "ejecuta", "ejecutar", "código",
            "python", "algoritmo", "exactitud", "decimal", "número exacto",
            "estadística", "matemáticas", "fórmula", "ecuación"
        ]
        
        query_lower = query.lower()
        
        keyword_match = any(keyword in query_lower for keyword in code_keywords)
        
        # Verificar patrones numéricos o matemáticos
        math_patterns = [
            r'\d+\s*[+\-*/^]\s*\d+',  # Operaciones matemáticas básicas
            r'\d+\s*%',  # Porcentajes
            r'raíz\s+cuadrada',
            r'logaritmo',
            r'factorial',
            r'media|mediana|moda|promedio',
            r'desviación\s+estándar',
            r'probabilidad'
        ]
        
        import re
        math_match = any(re.search(pattern, query_lower) for pattern in math_patterns)
        
        return keyword_match or math_match
    
    def generate_code(self, llm, query: str) -> str:
        """
        Genera código Python para resolver la consulta.
        
        Args:
            llm: Modelo de lenguaje para generar el código.
            query (str): Consulta del usuario.
        
        Returns:
            str: Código Python generado.
        """
        code_generation_prompt = f"""
        El usuario ha realizado una consulta que requiere cálculos precisos o ejecución de código:
        
        "{query}"
        
        Genera ÚNICAMENTE código Python para resolver esta consulta. El código debe:
        1. Ser claro, eficiente y seguir las mejores prácticas
        2. Incluir comentarios explicativos
        3. Manejar posibles errores
        4. Mostrar resultados con print() para que sean visibles
        5. Usar bibliotecas estándar o numpy/pandas si es necesario
        
        NO expliques el código, NO incluyas markdown. Proporciona SOLAMENTE el código Python.
        """
        
        try:
            code_response = llm.invoke(code_generation_prompt)
            python_code = code_response.content
            
            # Extraer el código si está en un bloque markdown
            if "```python" in python_code:
                python_code = python_code.split("```python")[1].split("```")[0].strip()
            elif "```" in python_code:
                python_code = python_code.split("```")[1].split("```")[0].strip()
            
            return python_code
        
        except Exception as e:
            logger.error(f"Error al generar código: {str(e)}")
            return f"# Error al generar código\nprint('No se pudo generar código: {str(e)}')"
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Ejecuta código Python de manera segura.
        
        Args:
            code (str): Código Python a ejecutar.
        
        Returns:
            Dict[str, Any]: Resultado de la ejecución.
        """
        # Verificar seguridad del código
        is_safe, error_message = is_safe_code(code)
        if not is_safe:
            logger.warning(f"Código inseguro detectado: {error_message}")
            return {
                "status": "error",
                "stdout": "",
                "stderr": f"Código potencialmente peligroso detectado: {error_message}",
                "error": error_message
            }
        
        # Preparar entorno de ejecución
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        # Añadir importaciones comunes
        augmented_code = "\n".join(self.allowed_imports.values()) + "\n\n" + code
        
        # Variables locales para la ejecución
        local_vars = {}
        
        try:
            # Ejecutar código redirigiendo stdout y stderr
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                # Usar exec con globals limitados
                exec(augmented_code, {"__builtins__": __builtins__}, local_vars)
            
            # Recuperar salida y errores
            stdout = sanitize_code_output(output_buffer.getvalue())
            stderr = sanitize_code_output(error_buffer.getvalue())
            
            logger.info("Código ejecutado correctamente")
            
            return {
                "status": "success",
                "stdout": stdout,
                "stderr": stderr,
                "error": None,
                "variables": {k: str(v) for k, v in local_vars.items() if not k.startswith("_")}
            }
        
        except Exception as e:
            # Capturar y formatear el error
            error_msg = str(e)
            tb = traceback.format_exc()
            
            logger.error(f"Error al ejecutar código: {error_msg}")
            
            return {
                "status": "error",
                "stdout": sanitize_code_output(output_buffer.getvalue()),
                "stderr": sanitize_code_output(error_buffer.getvalue()),
                "error": error_msg,
                "traceback": tb
            }
    
    def explain_code_result(self, llm, query: str, code: str, execution_result: Dict[str, Any]) -> str:
        """
        Genera una explicación del código y su resultado.
        
        Args:
            llm: Modelo de lenguaje para generar la explicación.
            query (str): Consulta original del usuario.
            code (str): Código Python ejecutado.
            execution_result (Dict[str, Any]): Resultado de la ejecución.
        
        Returns:
            str: Explicación para el usuario.
        """
        status = execution_result["status"]
        stdout = execution_result.get("stdout", "")
        stderr = execution_result.get("stderr", "")
        error = execution_result.get("error", "")
        variables = execution_result.get("variables", {})
        
        # Formatear variables para la explicación
        var_str = "\n".join([f"{k} = {v}" for k, v in variables.items() if not k.startswith("_")])
        
        explanation_prompt = f"""
        El usuario preguntó: "{query}"
        
        Para responder con precisión, generé y ejecuté el siguiente código Python:
        
        ```python
        {code}
        ```
        
        El código {"se ejecutó correctamente" if status == "success" else "encontró errores"}. 
        
        Resultado de la ejecución:
        
        SALIDA ESTÁNDAR:
        {stdout}
        
        {"ERRORES:" if stderr or error else ""}
        {stderr}
        {error}
        
        {"VARIABLES FINALES:" if var_str else ""}
        {var_str}
        
        Por favor, explica el resultado al usuario de manera clara y concisa, 
        relacionándolo con su pregunta original. 
        
        La explicación debe:
        1. Responder directamente a la consulta del usuario
        2. Explicar el significado del resultado (no el código)
        3. Ser concisa pero completa
        4. Incluir los valores numéricos o resultados relevantes
        5. No mencionar el proceso de generación de código a menos que sea relevante
        
        Si hubo errores, explica el problema de manera sencilla y proporciona una respuesta alternativa si es posible.
        """
        
        try:
            explanation = llm.invoke(explanation_prompt).content
            return explanation
        except Exception as e:
            logger.error(f"Error al generar explicación: {str(e)}")
            
            # Respuesta de respaldo si falla la explicación
            if status == "success":
                return f"""
                He realizado el cálculo que solicitaste. Aquí está el resultado:
                
                {stdout}
                
                Si necesitas más detalles o tienes alguna pregunta adicional, házmelo saber.
                """
            else:
                return f"""
                Intenté realizar el cálculo, pero encontré algunos problemas técnicos.
                
                Error: {error}
                
                ¿Podrías reformular tu pregunta o proporcionar más detalles para que pueda ayudarte mejor?
                """