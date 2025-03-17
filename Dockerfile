FROM python:3.10-slim
WORKDIR /app

# Instalar curl y Poetry
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copiar archivos de configuración de Poetry
COPY pyproject.toml poetry.lock* ./

# Instalar dependencias sin crear virtualenv
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-root

# Copiar el resto del código
COPY . .

# Exponer el puerto de la aplicación (en este ejemplo, 7860)
EXPOSE 7860

# Comando para ejecutar la aplicación a través de Poetry
CMD ["poetry", "run", "python", "main.py"]