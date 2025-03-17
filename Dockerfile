FROM python:3.10-slim

WORKDIR /app

# Install curl and Poetry
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy Poetry config files
COPY pyproject.toml poetry.lock* ./

# Install dependencies without creating a virtualenv
RUN poetry config virtualenvs.create false && poetry install --no-root

# Copy the rest of the code
COPY . .

# Expose the app port
EXPOSE 7860

# Run the application
CMD ["poetry", "run", "python", "app/main.py"]
