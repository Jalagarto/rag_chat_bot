# RAG Chatbot con Memoria Dinámica
Un chatbot avanzado basado en RAG (Retrieval-Augmented Generation) con memoria dinámica y capacidad de ejecución de código Python.

## Características
- **RAG**: Responde preguntas basadas en documentos PDF cargados
- **Memoria Dinámica**: Resume automáticamente conversaciones largas
- **Ejecución de Código**: Detecta y ejecuta código Python para consultas que requieren precisión
- **Interfaz Amigable**: UI intuitiva construida con Gradio
- **Arquitectura Modular**: Diseñado para ser mantenible y extensible
- **Listo para Producción**: Incluye Dockerfile, docker-compose y 
manejo de errores

## Instalación
### Requisitos

- Python 3.10+
- Clave API de OpenAI
- [Poetry](https://python-poetry.org/)

### Instalación Local

1. Clonar el repositorio

```bash
git clone https://github.com/usuario/rag-chatbot.git
cd rag-chatbot
```

2. Instalar dependencias y crear el entorno virtual
```bash
poetry install
```

3. Activar el entorno virtual (opcional)
```bash
poetry shell
```

4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tu clave API y configuración
```

5. Ejecutar la aplicación
```bash
cd app
poetry run python main.py
```


### Despliegue con Docker

1. generar la imagen docker

```bash
docker build -t rag-chat-bot .
```

2. ejecutar el contenedor

```bash
docker run -d -p 7860:7860 rag-chat-bot
```


## Uso
1. Accede a la interfaz web en http://localhost:7860
2. Carga documentos PDF usando el panel lateral
3. Haz preguntas sobre el contenido de los documentos
4. Para consultas que requieren precisión numérica, el sistema ejecutará código Python automáticamente

## Estructura del Proyecto

* config/: Configuraciones y variables de entorno
* core/: Componentes principales del sistema
* utils/: Utilidades y funciones auxiliares
* logs/: Archivos de registro
* data/: Almacenamiento de la base de datos vectorial

## Arquitectura
El sistema se compone de los siguientes módulos:

1. Document Processor: Gestiona la carga y procesamiento de documentos PDF
2. Memory Manager: Administra el historial de conversación con resumen dinámico
3. Code Executor: Detecta, genera y ejecuta código Python de manera segura
4. Query Engine: Coordina el procesamiento de consultas y generación de respuestas
5. ChatbotApp: Integra todos los componentes y proporciona la interfaz de usuario

## TODOes
* Añadir un docker-compose si se considera necesario
* CI/CD pipeline
* Evaluación automática
* Tests

